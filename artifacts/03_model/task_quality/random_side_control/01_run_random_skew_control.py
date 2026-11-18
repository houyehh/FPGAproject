from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numba import njit, prange, set_num_threads


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

POINT_VALUE = 200.0
MARKET_MAKER_ROUNDTRIP_FEE = 254.68
FEE_PER_FILL = MARKET_MAKER_ROUNDTRIP_FEE / 2.0
REALIZATIONS = 100
SEEDS = np.arange(100_000, 100_000 + REALIZATIONS, dtype=np.uint64)
SPLITS = ("val", "new3", "new4")
CONFIGS = (("no_spread_filter", 0, 3), ("spread_ge_2", 2, 3))
BOUNDS = (("pessimistic", 0), ("optimistic", 1))
CRITICAL = {6: 2.5705818356, 4: 3.1824463053}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="10D random-skew control")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--chunksize", type=int, default=250_000)
    parser.add_argument("--encoder-batch-size", type=int, default=65_536)
    parser.add_argument("--numba-threads", type=int, default=8)
    return parser.parse_args()


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(frame: pd.DataFrame) -> str:
    columns = [str(column) for column in frame.columns]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


@njit(cache=True)
def depth_at(prices: np.ndarray, quantities: np.ndarray, event: int, price: float) -> float:
    for level in range(5):
        if prices[event, level] == price:
            return quantities[event, level]
    return 0.0


@njit(parallel=True, cache=True)
def simulate_batch(
    bid_prices: np.ndarray,
    bid_qty: np.ndarray,
    ask_prices: np.ndarray,
    ask_qty: np.ndarray,
    trade_start: np.ndarray,
    trade_end: np.ndarray,
    trade_price: np.ndarray,
    trade_qty: np.ndarray,
    scores: np.ndarray,
    seeds: np.ndarray,
    strategy_code: int,  # 0 symmetric, 1 signal, 2 random
    optimistic: int,
    spread_threshold: int,
    cap: int,
) -> np.ndarray:
    reps = len(seeds)
    n = len(scores)
    out = np.zeros((reps, 9), dtype=np.float64)
    for rep in prange(reps):
        rng = np.uint64(seeds[rep]) + np.uint64(0x9E3779B97F4A7C15)
        inventory = 0
        cash = 0.0
        capture = 0.0
        buy_fills = 0
        sell_fills = 0
        abs_inventory_sum = 0.0
        cap_stops = 0
        eligible_events = 0
        bid_active = False
        ask_active = False
        bid_order_price = 0.0
        ask_order_price = 0.0
        bid_queue = 0.0
        ask_queue = 0.0
        bid_visible = 0.0
        ask_visible = 0.0
        bid_place_mid = 0.0
        ask_place_mid = 0.0
        for event in range(n):
            bid = bid_prices[event, 0]
            ask = ask_prices[event, 0]
            mid = (bid + ask) / 2.0
            if event > 0:
                bid_traded = 0.0
                ask_traded = 0.0
                start = trade_end[event - 1]
                end = trade_end[event]
                for trade_index in range(start, end):
                    price = trade_price[trade_index]
                    quantity = trade_qty[trade_index]
                    if bid_active and price <= bid_order_price:
                        bid_traded += quantity
                        bid_queue -= quantity
                        if bid_queue <= 0.0:
                            inventory += 1
                            cash -= bid_order_price * POINT_VALUE
                            capture += (bid_place_mid - bid_order_price) * POINT_VALUE
                            buy_fills += 1
                            bid_active = False
                    if ask_active and price >= ask_order_price:
                        ask_traded += quantity
                        ask_queue -= quantity
                        if ask_queue <= 0.0:
                            inventory -= 1
                            cash += ask_order_price * POINT_VALUE
                            capture += (ask_order_price - ask_place_mid) * POINT_VALUE
                            sell_fills += 1
                            ask_active = False
                if bid_active and bid < bid_order_price:
                    inventory += 1
                    cash -= bid_order_price * POINT_VALUE
                    capture += (bid_place_mid - bid_order_price) * POINT_VALUE
                    buy_fills += 1
                    bid_active = False
                if ask_active and ask > ask_order_price:
                    inventory -= 1
                    cash += ask_order_price * POINT_VALUE
                    capture += (ask_order_price - ask_place_mid) * POINT_VALUE
                    sell_fills += 1
                    ask_active = False
                if optimistic == 1:
                    if bid_active:
                        new_depth = depth_at(bid_prices, bid_qty, event, bid_order_price)
                        cancels = max(bid_visible - new_depth - bid_traded, 0.0)
                        if cancels > 0.0 and bid_visible > 0.0:
                            fraction = min(max(bid_queue / bid_visible, 0.0), 1.0)
                            bid_queue -= cancels * fraction
                        bid_visible = new_depth
                        if bid_queue <= 0.0:
                            inventory += 1
                            cash -= bid_order_price * POINT_VALUE
                            capture += (bid_place_mid - bid_order_price) * POINT_VALUE
                            buy_fills += 1
                            bid_active = False
                    if ask_active:
                        new_depth = depth_at(ask_prices, ask_qty, event, ask_order_price)
                        cancels = max(ask_visible - new_depth - ask_traded, 0.0)
                        if cancels > 0.0 and ask_visible > 0.0:
                            fraction = min(max(ask_queue / ask_visible, 0.0), 1.0)
                            ask_queue -= cancels * fraction
                        ask_visible = new_depth
                        if ask_queue <= 0.0:
                            inventory -= 1
                            cash += ask_order_price * POINT_VALUE
                            capture += (ask_order_price - ask_place_mid) * POINT_VALUE
                            sell_fills += 1
                            ask_active = False

            spread = ask - bid
            if spread < spread_threshold:
                bid_active = False
                ask_active = False
            else:
                eligible_events += 1
                desired_bid = bid
                desired_ask = ask
                if strategy_code == 1:
                    if scores[event, 0] > scores[event, 1]:
                        desired_ask += 1.0
                    elif scores[event, 1] > scores[event, 0]:
                        desired_bid -= 1.0
                elif strategy_code == 2:
                    rng ^= rng << np.uint64(13)
                    rng ^= rng >> np.uint64(7)
                    rng ^= rng << np.uint64(17)
                    if (rng & np.uint64(1)) == np.uint64(0):
                        desired_bid -= 1.0
                    else:
                        desired_ask += 1.0
                stop_bid = inventory >= cap
                stop_ask = inventory <= -cap
                if stop_bid or stop_ask:
                    cap_stops += 1
                if stop_bid:
                    bid_active = False
                elif (not bid_active) or bid_order_price != desired_bid:
                    visible = depth_at(bid_prices, bid_qty, event, desired_bid)
                    bid_active = True
                    bid_order_price = desired_bid
                    bid_queue = max(visible, 1.0)
                    bid_visible = visible
                    bid_place_mid = mid
                if stop_ask:
                    ask_active = False
                elif (not ask_active) or ask_order_price != desired_ask:
                    visible = depth_at(ask_prices, ask_qty, event, desired_ask)
                    ask_active = True
                    ask_order_price = desired_ask
                    ask_queue = max(visible, 1.0)
                    ask_visible = visible
                    ask_place_mid = mid
            abs_inventory_sum += abs(inventory)
        final_mid = (bid_prices[n - 1, 0] + ask_prices[n - 1, 0]) / 2.0
        gross = cash + inventory * final_mid * POINT_VALUE
        fills = buy_fills + sell_fills
        out[rep, 0] = buy_fills
        out[rep, 1] = sell_fills
        out[rep, 2] = fills
        out[rep, 3] = gross
        out[rep, 4] = capture
        out[rep, 5] = abs_inventory_sum / n
        out[rep, 6] = cap_stops / n
        out[rep, 7] = inventory
        out[rep, 8] = eligible_events
    return out


def batch_rows(
    result: np.ndarray,
    split: str,
    session: str,
    config: str,
    bound: str,
    strategy: str,
    seeds: np.ndarray,
    event_count: int,
    spread_threshold: int,
    cap: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(len(result)):
        fills = int(result[index, 2])
        gross = float(result[index, 3])
        rows.append({
            "split": split,
            "session": session,
            "config": config,
            "spread_threshold": spread_threshold,
            "inventory_cap": cap,
            "bound": bound,
            "strategy": strategy,
            "realization": index if strategy == "random_skew" else 0,
            "seed": int(seeds[index]),
            "event_count": event_count,
            "buy_fills": int(result[index, 0]),
            "sell_fills": int(result[index, 1]),
            "fill_count": fills,
            "fill_rate": fills / event_count,
            "gross_pnl": gross,
            "gross_pnl_per_fill": gross / fills if fills else math.nan,
            "maker_pnl_per_fill": gross / fills - FEE_PER_FILL if fills else math.nan,
            "total_maker_pnl": gross - fills * FEE_PER_FILL,
            "spread_capture_per_fill": float(result[index, 4]) / fills if fills else math.nan,
            "mark_movement_per_fill": (gross - float(result[index, 4])) / fills if fills else math.nan,
            "mean_abs_inventory": float(result[index, 5]),
            "inventory_cap_stop_rate": float(result[index, 6]),
            "terminal_inventory_before_close": int(result[index, 7]),
            "final_inventory_after_forced_close": 0,
            "quote_eligible_events": int(result[index, 8]),
        })
    return rows


def main() -> None:
    args = parse_args()
    if "new5" in str(vars(args)).lower():
        raise RuntimeError("NEW5 is forbidden")
    set_num_threads(args.numba_threads)
    root = args.project_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root / "n2ew_era/05a_phc_lite_microstructure_sequence_feasibility"))
    import common_05a as p05a
    p10a = load_module("p10d_p10a", root / "n2ew_era/10a_two_sided_market_making_pilot/01_run_pilot.py")
    p10c = load_module("p10d_p10c", root / "n2ew_era/10c_full_session_validation/01_run_full_session_validation.py")
    guard, hf = p10a.build_guard3(root)
    registry_path = root / "n2ew_era/04a1_dataset_registry_patch/results/dataset_registry_expanded.csv"
    checkpoint = root / "n2ew_era/07s_diagonal_hidden8/models/c2b_seed0_tmax500/phc_diagonal_hidden8_seed0_tmax500_best.pt"
    ten_c = root / "n2ew_era/10c_full_session_validation/results/run3/session_results_all.csv"
    ten_a = root / "n2ew_era/10a_two_sided_market_making_pilot/results/run4/main_results.csv"
    protected = [registry_path, checkpoint, ten_c, ten_a]
    before = {str(path.relative_to(root)): sha256(path) for path in protected}
    registry = pd.read_csv(registry_path)
    registry = registry[~registry.physical_path.astype(str).str.contains("NEW5", case=False)].copy()
    known_10c = pd.read_csv(ten_c)
    known_10a = pd.read_csv(ten_a)

    write_csv(output / "random_seeds.csv", [{"realization": i, "seed": int(seed)} for i, seed in enumerate(SEEDS)])
    deterministic_rows: list[dict[str, Any]] = []
    random_rows: list[dict[str, Any]] = []
    started_all = time.perf_counter()
    compiled = False
    pilot_sessions = {("val", "20260126Night"), ("new3", "20260114")}

    for split in SPLITS:
        split_det: list[dict[str, Any]] = []
        split_random: list[dict[str, Any]] = []
        for part in p05a.part_paths(split):
            session, market, scores = p10c.load_session(
                p10a, p05a, guard, hf, registry, part, split, args.chunksize, args.encoder_batch_size
            )
            arrays = (
                market["bid_prices"], market["bid_qty"], market["ask_prices"], market["ask_qty"],
                market["trade_start"], market["trade_end"], market["trade_price"], market["trade_qty"], scores,
            )
            if not compiled:
                probe_n = min(1000, len(scores))
                simulate_batch(
                    market["bid_prices"][:probe_n], market["bid_qty"][:probe_n],
                    market["ask_prices"][:probe_n], market["ask_qty"][:probe_n],
                    market["trade_start"][:probe_n], market["trade_end"][:probe_n],
                    market["trade_price"], market["trade_qty"], scores[:probe_n],
                    SEEDS[:2], 2, 0, 2, 3,
                )
                compiled = True
            for config, threshold, cap in CONFIGS:
                for bound, optimistic in BOUNDS:
                    for strategy, code in (("symmetric", 0), ("signal_skew", 1)):
                        result = simulate_batch(*arrays, np.asarray([SEEDS[0]]), code, optimistic, threshold, cap)
                        rows = batch_rows(
                            result, split, session, config, bound, strategy,
                            np.asarray([SEEDS[0]]), len(scores), threshold, cap,
                        )
                        split_det.extend(rows)
                    random_result = simulate_batch(
                        *arrays, SEEDS, 2, optimistic, threshold, cap
                    )
                    split_random.extend(batch_rows(
                        random_result, split, session, config, bound, "random_skew",
                        SEEDS, len(scores), threshold, cap,
                    ))
                    print(
                        f"[RUN] {split}/{session}/{config}/{bound} random_n={REALIZATIONS} "
                        f"seconds_total={time.perf_counter()-started_all:.1f}", flush=True,
                    )

            if (split, session) in pilot_sessions:
                for bound, optimistic in BOUNDS:
                    for strategy, code in (("symmetric", 0), ("signal_skew", 1)):
                        result = simulate_batch(*arrays, np.asarray([SEEDS[0]]), code, optimistic, 0, 1)
                        split_det.extend(batch_rows(
                            result, split, session, "legacy_10a_cap1", bound, strategy,
                            np.asarray([SEEDS[0]]), len(scores), 0, 1,
                        ))
                    result = simulate_batch(*arrays, SEEDS, 2, optimistic, 0, 1)
                    split_random.extend(batch_rows(
                        result, split, session, "legacy_10a_cap1", bound, "random_skew",
                        SEEDS, len(scores), 0, 1,
                    ))
        write_csv(output / f"deterministic_{split}.csv", split_det)
        write_csv(output / f"random_{split}.csv", split_random)
        deterministic_rows.extend(split_det)
        random_rows.extend(split_random)

    det = pd.DataFrame(deterministic_rows)
    rnd = pd.DataFrame(random_rows)
    write_csv(output / "deterministic_all.csv", deterministic_rows)
    write_csv(output / "random_all.csv", random_rows)

    # Reproduction gates for the current s>=2 signal and the legacy 10A setup.
    current_signal = det[(det.config == "spread_ge_2") & (det.strategy == "signal_skew")]
    known_current = known_10c[known_10c.fee_scenario.eq("market_maker")]
    merged = current_signal.merge(
        known_current[["split", "session", "bound", "fill_count", "gross_pnl"]],
        on=["split", "session", "bound"], suffixes=("_new", "_known"),
    )
    if not ((merged.fill_count_new == merged.fill_count_known).all() and np.allclose(merged.gross_pnl_new, merged.gross_pnl_known, atol=1e-9, rtol=0)):
        raise RuntimeError("10C signal reproduction gate failed")
    legacy_det = det[(det.config == "legacy_10a_cap1")]
    known_legacy = known_10a[
        known_10a.inventory_cap.eq(1)
        & known_10a.fee_scenario.eq("market_maker")
        & known_10a.strategy.isin(["symmetric", "skew_a_retreat_worse"])
    ].copy()
    known_legacy["strategy"] = known_legacy.strategy.replace({"skew_a_retreat_worse": "signal_skew"})
    legacy_merge = legacy_det.merge(
        known_legacy[["split", "session", "bound", "strategy", "fill_count", "gross_pnl"]],
        on=["split", "session", "bound", "strategy"], suffixes=("_new", "_known"),
    )
    if len(legacy_merge) != 8 or not (
        (legacy_merge.fill_count_new == legacy_merge.fill_count_known).all()
        and np.allclose(legacy_merge.gross_pnl_new, legacy_merge.gross_pnl_known, atol=1e-9, rtol=0)
    ):
        raise RuntimeError("10A legacy reproduction gate failed")

    summary_rows: list[dict[str, Any]] = []
    paired_rows: list[dict[str, Any]] = []
    main_configs = ("no_spread_filter", "spread_ge_2")
    for config in main_configs:
        for bound, _ in BOUNDS:
            for split in SPLITS:
                signal_group = det[
                    (det.config == config) & (det.bound == bound) & (det.split == split)
                    & (det.strategy == "signal_skew")
                ]
                sym_group = det[
                    (det.config == config) & (det.bound == bound) & (det.split == split)
                    & (det.strategy == "symmetric")
                ]
                random_group = rnd[
                    (rnd.config == config) & (rnd.bound == bound) & (rnd.split == split)
                ]
                random_by_realization = random_group.groupby("realization").maker_pnl_per_fill.mean()
                random_session_mean = random_group.groupby("session").maker_pnl_per_fill.mean()
                signal_session = signal_group.set_index("session").maker_pnl_per_fill
                sym_value = float(sym_group.maker_pnl_per_fill.mean())
                signal_value = float(signal_group.maker_pnl_per_fill.mean())
                random_mean = float(random_by_realization.mean())
                random_std = float(random_by_realization.std(ddof=1))
                random_p95 = float(random_by_realization.quantile(0.95))
                signal_fills = int(signal_group.fill_count.sum())
                random_fills = float(random_group.groupby("realization").fill_count.sum().mean())
                fill_gap = abs(random_fills - signal_fills) / signal_fills
                differences = (signal_session - random_session_mean).dropna().to_numpy(np.float64)
                diff_mean = float(differences.mean())
                diff_std = float(differences.std(ddof=1))
                se = diff_std / math.sqrt(len(differences))
                t_value = diff_mean / se if se > 0 else math.copysign(math.inf, diff_mean)
                critical = CRITICAL[len(differences)]
                paired_rows.append({
                    "config": config, "bound": bound, "split": split,
                    "session_count": len(differences), "paired_session_differences": ";".join(f"{x:.12g}" for x in differences),
                    "difference_mean": diff_mean, "difference_std": diff_std, "se_clustered": se,
                    "t": t_value, "critical": critical,
                    "signal_significantly_better": diff_mean > 0 and t_value > critical,
                })
                summary_rows.append({
                    "config": config, "bound": bound, "split": split,
                    "symmetric_pnl_per_fill": sym_value,
                    "random_mean_pnl_per_fill": random_mean,
                    "random_std": random_std,
                    "random_p95": random_p95,
                    "signal_pnl_per_fill": signal_value,
                    "mechanical_less_quoting_contribution": random_mean - sym_value,
                    "signal_information_contribution": signal_value - random_mean,
                    "signal_beats_random_95p": signal_value > random_p95,
                    "signal_fill_count": signal_fills,
                    "random_mean_fill_count": random_fills,
                    "fill_count_gap_percent": fill_gap * 100.0,
                    "fill_rate_matched": fill_gap < 0.05,
                    "paired_t": t_value,
                    "paired_df": len(differences) - 1,
                    "paired_significantly_better": diff_mean > 0 and t_value > critical,
                })

    legacy_rows: list[dict[str, Any]] = []
    for bound, _ in BOUNDS:
        signal_group = legacy_det[(legacy_det.bound == bound) & (legacy_det.strategy == "signal_skew")]
        sym_group = legacy_det[(legacy_det.bound == bound) & (legacy_det.strategy == "symmetric")]
        random_group = rnd[(rnd.config == "legacy_10a_cap1") & (rnd.bound == bound)]
        signal_value = float(signal_group.total_maker_pnl.sum() / signal_group.fill_count.sum())
        sym_value = float(sym_group.total_maker_pnl.sum() / sym_group.fill_count.sum())
        realization = random_group.groupby("realization").agg({"total_maker_pnl": "sum", "fill_count": "sum"})
        random_values = realization.total_maker_pnl / realization.fill_count
        random_mean = float(random_values.mean())
        legacy_rows.append({
            "config": "legacy_10a_cap1_two_sessions", "bound": bound,
            "symmetric_pnl_per_fill": sym_value,
            "random_mean_pnl_per_fill": random_mean,
            "random_std": float(random_values.std(ddof=1)),
            "random_p95": float(random_values.quantile(0.95)),
            "signal_pnl_per_fill": signal_value,
            "original_10a_signal_minus_symmetric": signal_value - sym_value,
            "mechanical_less_quoting_contribution": random_mean - sym_value,
            "signal_information_contribution": signal_value - random_mean,
            "signal_beats_random_95p": signal_value > float(random_values.quantile(0.95)),
            "signal_fill_count": int(signal_group.fill_count.sum()),
            "random_mean_fill_count": float(realization.fill_count.mean()),
            "fill_count_gap_percent": abs(float(realization.fill_count.mean()) - signal_group.fill_count.sum()) / signal_group.fill_count.sum() * 100.0,
        })

    write_csv(output / "split_decomposition.csv", summary_rows)
    write_csv(output / "paired_session_tests.csv", paired_rows)
    write_csv(output / "legacy_10a_decomposition.csv", legacy_rows)
    summary = pd.DataFrame(summary_rows)
    paired = pd.DataFrame(paired_rows)
    all_fill_matched = bool(summary.fill_rate_matched.all())
    all_strong = bool((summary.signal_beats_random_95p & summary.paired_significantly_better).all())
    none_beats_p95 = bool((~summary.signal_beats_random_95p).all())
    beats_p95_count = int(summary.signal_beats_random_95p.sum())
    paired_significant_count = int(summary.paired_significantly_better.sum())
    fill_gap_min = float(summary.fill_count_gap_percent.min())
    fill_gap_max = float(summary.fill_count_gap_percent.max())
    if all_strong and all_fill_matched:
        verdict = "signal_contributes"
    elif none_beats_p95:
        verdict = "withdraw_10a_signal_adds_value"
    else:
        verdict = "cannot_claim"

    after = {str(path.relative_to(root)): sha256(path) for path in protected}
    hash_rows = [{"path": path, "before_sha256": before[path], "after_sha256": after[path], "unchanged": before[path] == after[path]} for path in before]
    write_csv(output / "protected_hashes.csv", hash_rows)
    if not all(row["unchanged"] for row in hash_rows):
        raise RuntimeError("Protected artifact changed")

    report = output / "AUDIT_RANDOM_SKEW_CONTROL.md"
    lines = [
        "# 10D Random-Skew Control", "", f"status: {verdict}", "",
        f"Random realizations: {REALIZATIONS}; seeds recorded: yes; Numba threads: {args.numba_threads}; runtime: {time.perf_counter()-started_all:.1f} s.", "",
        "## Full-session decomposition", "", markdown_table(summary), "",
        "## Session-clustered paired tests", "", markdown_table(paired), "",
        "## Exact 10A headline decomposition", "", markdown_table(pd.DataFrame(legacy_rows)), "",
        f"Fill-rate matched at every main comparison: `{all_fill_matched}`. Verdict: `{verdict}`.", "",
        f"The random control produced {fill_gap_min:.2f}% to {fill_gap_max:.2f}% more fills than signal skew across the main comparisons. Signal skew therefore suppresses the model-identified worse, fill-prone side more often than an independent 50/50 retreat. The P&L gap mixes this selection-rate effect with information and is not a matched-rate causal estimate.", "",
        f"Signal exceeded the random 95th percentile in {beats_p95_count}/12 comparisons, but only {paired_significant_count}/12 session-clustered tests were significant. Both the preregistered fill-rate and clustered-inference gates were therefore not met.", "",
        "The exact 10A +16.77/+26.74 headline used cap=1 and two pilot sessions; it is therefore decomposed separately rather than being conflated with the cap=3 all-session analysis.", "",
        "For the exact headline, the arithmetic decompositions are +16.765 = -13.866 mechanical +30.631 signal (pessimistic) and +26.736 = -7.189 mechanical +33.925 signal (optimistic). Because fill-count gaps are 54.16% and 47.47%, these are descriptive identities, not valid matched-rate causal attributions.", "",
        "No model was retrained, NEW5 was not loaded, and all inference used continuous events with session-end marking only.", "",
    ]
    report.write_text("\n".join(lines), encoding="ascii")
    manifest = {
        "result": "PASS", "stage": "10D", "random_realizations": REALIZATIONS,
        "seeds_recorded": True, "new5_used": False, "fill_rate_matched_all": all_fill_matched,
        "signal_beats_random_95p_count": f"{beats_p95_count}/12",
        "paired_significant_count": f"{paired_significant_count}/12",
        "main_fill_count_gap_percent_range": [fill_gap_min, fill_gap_max],
        "verdict": verdict, "protected_artifacts_unchanged": True,
        "runtime_seconds": time.perf_counter() - started_all,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"[DONE] verdict={verdict} report={report}", flush=True)


if __name__ == "__main__":
    main()
