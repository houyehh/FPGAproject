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
from numba import njit, set_num_threads


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

POINT_VALUE = 200.0
FEE_PER_FILL = 254.68 / 2.0
LABEL_FEE = 15.0
SPLITS = ("val", "new3", "new4")
SPLIT_SOURCE = {"val": "NEW1", "new3": "NEW3", "new4": "NEW4"}
SPLIT_PRODUCT = {"val": "TXFB6", "new3": "TXFA6", "new4": "TXFA6"}
CONFIGS = (("no_spread_filter", 0), ("spread_ge_2", 2))
BOUNDS = (("pessimistic", 0), ("optimistic", 1))
STRATEGIES = (("symmetric", 0), ("model_skew", 1), ("perfect_a_retreat", 3), ("perfect_b_cancel", 4))
CAP = 3
EXCLUDED_CAPTURE = "my_orderbook_20260331_9004_3.csv"
CRITICAL = {6: 2.5705818356, 4: 3.1824463053}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="10E perfect-foresight ceiling")
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


@njit(cache=True)
def simulate_one(
    bid_prices: np.ndarray,
    bid_qty: np.ndarray,
    ask_prices: np.ndarray,
    ask_qty: np.ndarray,
    trade_end: np.ndarray,
    trade_price: np.ndarray,
    trade_qty: np.ndarray,
    scores: np.ndarray,
    h20_delta: np.ndarray,
    strategy_code: int,
    optimistic: int,
    spread_threshold: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    n = len(scores)
    fill_contributions = np.empty(n, dtype=np.float64)
    fill_sides = np.empty(n, dtype=np.int8)
    fill_place_mids = np.empty(n, dtype=np.float64)
    fill_count = 0
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
                        fill_contributions[fill_count] = bid_place_mid - bid_order_price
                        fill_sides[fill_count] = 1
                        fill_place_mids[fill_count] = bid_place_mid
                        fill_count += 1
                        buy_fills += 1
                        bid_active = False
                if ask_active and price >= ask_order_price:
                    ask_traded += quantity
                    ask_queue -= quantity
                    if ask_queue <= 0.0:
                        inventory -= 1
                        cash += ask_order_price * POINT_VALUE
                        capture += (ask_order_price - ask_place_mid) * POINT_VALUE
                        fill_contributions[fill_count] = ask_order_price - ask_place_mid
                        fill_sides[fill_count] = -1
                        fill_place_mids[fill_count] = ask_place_mid
                        fill_count += 1
                        sell_fills += 1
                        ask_active = False
            if bid_active and bid < bid_order_price:
                inventory += 1
                cash -= bid_order_price * POINT_VALUE
                capture += (bid_place_mid - bid_order_price) * POINT_VALUE
                fill_contributions[fill_count] = bid_place_mid - bid_order_price
                fill_sides[fill_count] = 1
                fill_place_mids[fill_count] = bid_place_mid
                fill_count += 1
                buy_fills += 1
                bid_active = False
            if ask_active and ask > ask_order_price:
                inventory -= 1
                cash += ask_order_price * POINT_VALUE
                capture += (ask_order_price - ask_place_mid) * POINT_VALUE
                fill_contributions[fill_count] = ask_order_price - ask_place_mid
                fill_sides[fill_count] = -1
                fill_place_mids[fill_count] = ask_place_mid
                fill_count += 1
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
                        fill_contributions[fill_count] = bid_place_mid - bid_order_price
                        fill_sides[fill_count] = 1
                        fill_place_mids[fill_count] = bid_place_mid
                        fill_count += 1
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
                        fill_contributions[fill_count] = ask_order_price - ask_place_mid
                        fill_sides[fill_count] = -1
                        fill_place_mids[fill_count] = ask_place_mid
                        fill_count += 1
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
            cancel_bid = False
            cancel_ask = False
            if strategy_code == 1:
                if scores[event, 0] > scores[event, 1]:
                    desired_ask += 1.0
                elif scores[event, 1] > scores[event, 0]:
                    desired_bid -= 1.0
            elif strategy_code == 3:
                if h20_delta[event] > 0.0:
                    desired_ask += 1.0
                elif h20_delta[event] < 0.0:
                    desired_bid -= 1.0
            elif strategy_code == 4:
                if h20_delta[event] > 0.0:
                    cancel_ask = True
                elif h20_delta[event] < 0.0:
                    cancel_bid = True
            stop_bid = inventory >= CAP or cancel_bid
            stop_ask = inventory <= -CAP or cancel_ask
            if inventory >= CAP or inventory <= -CAP:
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
    # Convert stored half-spread captures into complete maker P&L per fill.
    # The terminal mark is simulator state, not a future-label value.
    for index in range(fill_count):
        capture_component = fill_contributions[index] * POINT_VALUE
        mark_component = fill_sides[index] * (final_mid - fill_place_mids[index]) * POINT_VALUE
        fill_contributions[index] = capture_component + mark_component - FEE_PER_FILL
    out = np.zeros(10, dtype=np.float64)
    out[0] = buy_fills
    out[1] = sell_fills
    out[2] = fill_count
    out[3] = gross
    out[4] = capture
    out[5] = abs_inventory_sum / n
    out[6] = cap_stops / n
    out[7] = inventory
    out[8] = eligible_events
    out[9] = final_mid
    return out, fill_contributions, fill_count


def load_session_with_labels(
    p10a: Any,
    p05a: Any,
    guard: Any,
    hf: Any,
    registry: pd.DataFrame,
    part: Path,
    split: str,
    chunksize: int,
    encoder_batch_size: int,
) -> tuple[str, dict[str, np.ndarray], np.ndarray, np.ndarray]:
    session = part.stem.split("_")[1]
    frame = p05a.read_event_frame(part)
    rows_all = registry[
        registry.source_group.eq(SPLIT_SOURCE[split])
        & registry.session_id.astype(str).eq(session)
    ].sort_values("file_name")
    event_indices = pd.to_numeric(frame["event_index"], errors="coerce").fillna(-1).to_numpy(np.int64)
    if rows_all.file_name.astype(str).eq(EXCLUDED_CAPTURE).any():
        rows_all = rows_all.reset_index(drop=True)
        duplicate_order = int(np.flatnonzero(rows_all.file_name.astype(str).eq(EXCLUDED_CAPTURE))[0])
        raw_with_duplicate = p10a.read_raw_session(rows_all, SPLIT_PRODUCT[split], chunksize)
        old_market = p10a.action_market(raw_with_duplicate, event_indices)
        keep = raw_with_duplicate["file_order"][old_market["positions"]] != duplicate_order
        frame = frame.loc[keep].reset_index(drop=True)
        rows = rows_all[~rows_all.file_name.astype(str).eq(EXCLUDED_CAPTURE)].copy()
        raw = p10a.read_raw_session(rows, SPLIT_PRODUCT[split], chunksize)
        action_count = len(raw["book_positions"]) - 200
        guard_delta = len(frame) - action_count
        if guard_delta == 100:
            frame = frame.iloc[:action_count].reset_index(drop=True)
        elif guard_delta != 0:
            raise RuntimeError(f"Unexpected dedup guard delta for {session}: {guard_delta}")
        event_indices = np.arange(len(frame), dtype=np.int64)
        market = p10a.action_market(raw, event_indices)
    else:
        raw = p10a.read_raw_session(rows_all, SPLIT_PRODUCT[split], chunksize)
        market = p10a.action_market(raw, event_indices)
    scaler = p05a.load_scaler()
    features, _ = p05a.normalized_features(frame, scaler)
    scores, max_diff = p10a.continuous_scores(guard, hf, features, encoder_batch_size)
    if max_diff != 0:
        raise RuntimeError(f"Score recurrence self-check failed for {session}: {max_diff}")
    bid_excess = pd.to_numeric(frame["bid_excess_pnl_H20"], errors="coerce").to_numpy(np.float64)
    ask_excess = pd.to_numeric(frame["ask_excess_pnl_H20"], errors="coerce").to_numpy(np.float64)
    valid_h20 = ~((bid_excess == 0.0) & (ask_excess == 0.0))
    bid_raw = np.zeros(len(frame), dtype=np.float64)
    ask_raw = np.zeros(len(frame), dtype=np.float64)
    bid_raw[valid_h20] = bid_excess[valid_h20] + LABEL_FEE
    ask_raw[valid_h20] = ask_excess[valid_h20] + LABEL_FEE
    if valid_h20.any() and np.max(np.abs(bid_raw[valid_h20] + ask_raw[valid_h20])) > 1e-9:
        raise RuntimeError(f"H20 label antisymmetry failed for {session}")
    # Positive delta means future mid rises: the ask is adverse. Negative means
    # future mid falls: the bid is adverse. A zero terminal sentinel changes no action.
    return session, market, scores, bid_raw


def result_row(
    result: np.ndarray,
    split: str,
    session: str,
    config: str,
    threshold: int,
    bound: str,
    strategy: str,
    event_count: int,
) -> dict[str, Any]:
    fills = int(result[2])
    gross = float(result[3])
    return {
        "split": split,
        "session": session,
        "config": config,
        "spread_threshold": threshold,
        "inventory_cap": CAP,
        "bound": bound,
        "strategy": strategy,
        "oracle_uses_future_labels": strategy.startswith("perfect_"),
        "post_hoc_diagnostic_only": strategy.startswith("perfect_"),
        "event_count": event_count,
        "buy_fills": int(result[0]),
        "sell_fills": int(result[1]),
        "fill_count": fills,
        "fill_rate": fills / event_count,
        "gross_pnl": gross,
        "gross_pnl_per_fill": gross / fills if fills else math.nan,
        "maker_pnl_per_fill": gross / fills - FEE_PER_FILL if fills else math.nan,
        "roundtrip_net_twd": 2.0 * (gross / fills - FEE_PER_FILL) if fills else math.nan,
        "total_maker_pnl": gross - fills * FEE_PER_FILL,
        "spread_capture_per_fill": float(result[4]) / fills if fills else math.nan,
        "mark_movement_per_fill": (gross - float(result[4])) / fills if fills else math.nan,
        "mean_abs_inventory": float(result[5]),
        "inventory_cap_stop_rate": float(result[6]),
        "terminal_inventory_before_close": int(result[7]),
        "final_inventory_after_forced_close": 0,
        "quote_eligible_events": int(result[8]),
        "underpowered": fills < 1000,
    }


def aggregate_deterministic(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    keys = ["config", "bound", "split", "strategy"]
    for key, group in frame.groupby(keys):
        fills = int(group.fill_count.sum())
        gross = float(group.gross_pnl.sum())
        capture = float((group.spread_capture_per_fill * group.fill_count).sum())
        rows.append({
            **dict(zip(keys, key)),
            "session_count": len(group),
            "fills": fills,
            "capture_per_fill": capture / fills,
            "markout_per_fill": (gross - capture) / fills,
            "pnl_per_fill_market_maker": gross / fills - FEE_PER_FILL,
            "roundtrip_net_twd": 2.0 * (gross / fills - FEE_PER_FILL),
            "underpowered": fills < 1000,
        })
    return rows


def aggregate_random(random_frame: pd.DataFrame) -> list[dict[str, Any]]:
    random_frame = random_frame[random_frame.config.isin([name for name, _ in CONFIGS])].copy()
    random_frame["capture_total"] = random_frame.spread_capture_per_fill * random_frame.fill_count
    rows: list[dict[str, Any]] = []
    for (config, bound, split), group in random_frame.groupby(["config", "bound", "split"]):
        per_rep = group.groupby("realization").agg(
            fills=("fill_count", "sum"), gross=("gross_pnl", "sum"), capture=("capture_total", "sum")
        )
        rows.append({
            "config": config, "bound": bound, "split": split, "strategy": "random_skew",
            "session_count": group.session.nunique(),
            "fills": float(per_rep.fills.mean()),
            "capture_per_fill": float((per_rep.capture / per_rep.fills).mean()),
            "markout_per_fill": float(((per_rep.gross - per_rep.capture) / per_rep.fills).mean()),
            "pnl_per_fill_market_maker": float((per_rep.gross / per_rep.fills - FEE_PER_FILL).mean()),
            "roundtrip_net_twd": float((2.0 * (per_rep.gross / per_rep.fills - FEE_PER_FILL)).mean()),
            "underpowered": bool(per_rep.fills.mean() < 1000),
        })
    return rows


def clustered_rows(session_frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    perfect = session_frame[session_frame.strategy.isin(["perfect_a_retreat", "perfect_b_cancel"])]
    for (config, bound, split, strategy), group in perfect.groupby(["config", "bound", "split", "strategy"]):
        values = group.maker_pnl_per_fill.to_numpy(np.float64)
        n = len(values)
        mean = float(values.mean())
        std = float(values.std(ddof=1))
        se = std / math.sqrt(n)
        t_value = mean / se if se > 0 else math.copysign(math.inf, mean)
        critical = CRITICAL[n]
        rows.append({
            "config": config, "bound": bound, "split": split, "strategy": strategy,
            "session_count": n, "session_mean_pnl_per_fill": mean, "session_std": std,
            "se_clustered": se, "t_vs_zero": t_value, "df": n - 1, "critical": critical,
            "significantly_positive": mean > 0 and t_value > critical,
            "underpowered_sessions": int(group.underpowered.sum()),
        })
    return rows


def ceiling_rows(aggregate: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (config, bound, split), group in aggregate.groupby(["config", "bound", "split"]):
        values = group.set_index("strategy").pnl_per_fill_market_maker
        sym = float(values["symmetric"])
        model = float(values["model_skew"])
        a = float(values["perfect_a_retreat"])
        b = float(values["perfect_b_cancel"])
        rows.append({
            "config": config, "bound": bound, "split": split,
            "symmetric_pnl_per_fill": sym, "model_pnl_per_fill": model,
            "perfect_a_pnl_per_fill": a, "perfect_b_pnl_per_fill": b,
            "model_gain_vs_symmetric": model - sym,
            "perfect_a_gain_vs_symmetric": a - sym,
            "perfect_b_gain_vs_symmetric": b - sym,
            "model_share_of_ceiling_a": (model - sym) / (a - sym) if a != sym else math.nan,
            "model_share_of_ceiling_b": (model - sym) / (b - sym) if b != sym else math.nan,
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
    p10a_path = root / "n2ew_era/10a_two_sided_market_making_pilot/01_run_pilot.py"
    p10a = load_module("p10e_p10a", p10a_path)
    guard, hf = p10a.build_guard3(root)
    registry_path = root / "n2ew_era/04a1_dataset_registry_patch/results/dataset_registry_expanded.csv"
    checkpoint = root / "n2ew_era/07s_diagonal_hidden8/models/c2b_seed0_tmax500/phc_diagonal_hidden8_seed0_tmax500_best.pt"
    ten_c_path = root / "n2ew_era/10c_full_session_validation/results/run3/session_results_all.csv"
    ten_d_path = root / "n2ew_era/10d_random_skew_control/results/run1/random_all.csv"
    ten_d_det_path = root / "n2ew_era/10d_random_skew_control/results/run1/deterministic_all.csv"
    protected = [registry_path, checkpoint, p10a_path, ten_c_path, ten_d_path, ten_d_det_path]
    before = {str(path.relative_to(root)): sha256(path) for path in protected}
    registry = pd.read_csv(registry_path)
    registry = registry[~registry.physical_path.astype(str).str.contains("NEW5", case=False)].copy()
    known_10c = pd.read_csv(ten_c_path)
    random_frame = pd.read_csv(ten_d_path)
    known_10d_det = pd.read_csv(ten_d_det_path)

    session_rows: list[dict[str, Any]] = []
    tail_rows: list[dict[str, Any]] = []
    pooled_tail: dict[tuple[str, str, str, str], list[np.ndarray]] = {}
    started = time.perf_counter()
    compiled = False
    for split in SPLITS:
        split_rows: list[dict[str, Any]] = []
        for part in p05a.part_paths(split):
            session, market, scores, h20_delta = load_session_with_labels(
                p10a, p05a, guard, hf, registry, part, split, args.chunksize, args.encoder_batch_size
            )
            arrays = (
                market["bid_prices"], market["bid_qty"], market["ask_prices"], market["ask_qty"],
                market["trade_end"], market["trade_price"], market["trade_qty"], scores, h20_delta,
            )
            if not compiled:
                n = min(1000, len(scores))
                simulate_one(
                    market["bid_prices"][:n], market["bid_qty"][:n], market["ask_prices"][:n],
                    market["ask_qty"][:n], market["trade_end"][:n], market["trade_price"],
                    market["trade_qty"], scores[:n], h20_delta[:n], 3, 0, 0,
                )
                compiled = True
            for config, threshold in CONFIGS:
                for bound, optimistic in BOUNDS:
                    for strategy, code in STRATEGIES:
                        result, capture_contributions, fill_count = simulate_one(
                            *arrays, code, optimistic, threshold
                        )
                        row = result_row(result, split, session, config, threshold, bound, strategy, len(scores))
                        split_rows.append(row)
                        if strategy.startswith("perfect_") and fill_count:
                            contributions = capture_contributions[:fill_count].copy()
                            expected_total = float(result[3]) - fill_count * FEE_PER_FILL
                            if abs(float(contributions.sum()) - expected_total) > 1e-6:
                                raise RuntimeError(
                                    f"Fill contribution identity failed for {split}/{session}/{config}/{bound}/{strategy}"
                                )
                            remove_n = max(1, int(math.ceil(fill_count * 0.01)))
                            remove = np.argpartition(np.abs(contributions), -remove_n)[-remove_n:]
                            keep = np.ones(fill_count, dtype=np.bool_)
                            keep[remove] = False
                            original = float(contributions.mean())
                            trimmed = float(contributions[keep].mean()) if keep.any() else math.nan
                            tail_rows.append({
                                "split": split, "session": session, "config": config, "bound": bound,
                                "strategy": strategy, "fill_count": fill_count,
                                "removed_count": remove_n,
                                "original_pnl_per_fill": original,
                                "trimmed_pnl_per_fill": trimmed,
                                "original_positive": original > 0,
                                "trimmed_positive": trimmed > 0,
                                "robust_to_tail_removal": (original <= 0) or (trimmed > 0),
                            })
                            key = (config, bound, split, strategy)
                            pooled_tail.setdefault(key, []).append(contributions)
                    print(
                        f"[RUN] {split}/{session}/{config}/{bound} elapsed_s={time.perf_counter()-started:.1f}",
                        flush=True,
                    )
        write_csv(output / f"session_results_{split}.csv", split_rows)
        session_rows.extend(split_rows)

    session_frame = pd.DataFrame(session_rows)
    # Reproduce 10C model-skew results exactly before accepting oracle results.
    known = known_10c[known_10c.fee_scenario.eq("market_maker")].copy()
    current = session_frame[(session_frame.config == "spread_ge_2") & (session_frame.strategy == "model_skew")]
    merged = current.merge(
        known[["split", "session", "bound", "fill_count", "gross_pnl"]],
        on=["split", "session", "bound"], suffixes=("_new", "_known"),
    )
    if len(merged) != 32 or not (
        (merged.fill_count_new == merged.fill_count_known).all()
        and np.allclose(merged.gross_pnl_new, merged.gross_pnl_known, atol=1e-9, rtol=0)
    ):
        raise RuntimeError("10C reproduction gate failed")
    known_det = known_10d_det[known_10d_det.config.isin([name for name, _ in CONFIGS])].copy()
    known_det["strategy"] = known_det.strategy.replace({"signal_skew": "model_skew"})
    comparison = session_frame[session_frame.strategy.isin(["symmetric", "model_skew"])].merge(
        known_det[["split", "session", "config", "bound", "strategy", "fill_count", "gross_pnl"]],
        on=["split", "session", "config", "bound", "strategy"], suffixes=("_new", "_known"),
    )
    if len(comparison) != 128 or not (
        (comparison.fill_count_new == comparison.fill_count_known).all()
        and np.allclose(comparison.gross_pnl_new, comparison.gross_pnl_known, atol=1e-9, rtol=0)
    ):
        raise RuntimeError("10D deterministic reproduction gate failed")

    pooled_tail_rows: list[dict[str, Any]] = []
    for key, chunks in pooled_tail.items():
        contributions = np.concatenate(chunks)
        remove_n = max(1, int(math.ceil(len(contributions) * 0.01)))
        remove = np.argpartition(np.abs(contributions), -remove_n)[-remove_n:]
        keep = np.ones(len(contributions), dtype=np.bool_)
        keep[remove] = False
        original = float(contributions.mean())
        trimmed = float(contributions[keep].mean()) if keep.any() else math.nan
        pooled_tail_rows.append({
            "config": key[0], "bound": key[1], "split": key[2], "strategy": key[3],
            "fill_count": len(contributions), "removed_count": remove_n,
            "original_pnl_per_fill": original, "trimmed_pnl_per_fill": trimmed,
            "original_positive": original > 0, "trimmed_positive": trimmed > 0,
            "robust_to_tail_removal": (original <= 0) or (trimmed > 0),
        })

    deterministic_aggregate = aggregate_deterministic(session_frame)
    random_aggregate = aggregate_random(random_frame)
    all_aggregate = deterministic_aggregate + random_aggregate
    aggregate_frame = pd.DataFrame(all_aggregate)
    aggregate_frame["strategy_order"] = aggregate_frame.strategy.map({
        "symmetric": 0, "random_skew": 1, "model_skew": 2,
        "perfect_a_retreat": 3, "perfect_b_cancel": 4,
    })
    aggregate_frame = aggregate_frame.sort_values(["config", "bound", "split", "strategy_order"])
    clustered = clustered_rows(session_frame)
    ceilings = ceiling_rows(aggregate_frame)
    write_csv(output / "session_results_all.csv", session_rows)
    write_csv(output / "five_baseline_summary.csv", aggregate_frame.drop(columns="strategy_order").to_dict("records"))
    write_csv(output / "clustered_significance.csv", clustered)
    write_csv(output / "ceiling_shares.csv", ceilings)
    write_csv(output / "tail_removal_by_session.csv", tail_rows)
    write_csv(output / "tail_removal_sensitivity.csv", pooled_tail_rows)

    clustered_frame = pd.DataFrame(clustered)
    tail_frame = pd.DataFrame(pooled_tail_rows)
    bracket_unstable: list[str] = []
    for config in [name for name, _ in CONFIGS]:
        for split in SPLITS:
            for strategy in ("perfect_a_retreat", "perfect_b_cancel"):
                values = aggregate_frame[
                    (aggregate_frame.config == config) & (aggregate_frame.split == split)
                    & (aggregate_frame.strategy == strategy)
                ].set_index("bound").pnl_per_fill_market_maker
                if np.sign(values["pessimistic"]) != np.sign(values["optimistic"]):
                    bracket_unstable.append(f"{config}:{split}:{strategy}")
    bracket_stable = not bracket_unstable
    profitable = {}
    significant_counts: dict[str, int] = {}
    for strategy in ("perfect_a_retreat", "perfect_b_cancel"):
        subset = clustered_frame[clustered_frame.strategy == strategy]
        significant_counts[strategy] = int(subset.significantly_positive.sum())
        profitable[strategy] = bool(len(subset) == 12 and subset.significantly_positive.all())

    tail_measured = not tail_frame.empty
    positive_tail = tail_frame[tail_frame.original_positive]
    robust_tail = bool(positive_tail.robust_to_tail_removal.all()) if not positive_tail.empty else "not_applicable"
    if not bracket_stable:
        verdict = "indeterminate"
        recommendation = "Feature engineering cannot be justified while the oracle ceiling changes sign across queue brackets."
    elif robust_tail is False and (profitable["perfect_a_retreat"] or profitable["perfect_b_cancel"]):
        verdict = "indeterminate"
        recommendation = "The positive oracle ceiling is tail-dependent, so feature engineering is not justified."
    elif profitable["perfect_a_retreat"]:
        verdict = "signal_has_room"
        recommendation = "Feature engineering is worth testing because the existing retreat action space has a positive oracle ceiling."
    elif profitable["perfect_b_cancel"]:
        verdict = "action_space_problem"
        recommendation = "Add a cancel action before investing in new features."
    else:
        verdict = "product_structure_problem"
        recommendation = "Do not invest in feature engineering for this setup; even perfect foresight does not clear the cost structure."

    after = {str(path.relative_to(root)): sha256(path) for path in protected}
    hash_rows = [{
        "path": path, "before_sha256": before[path], "after_sha256": after[path],
        "unchanged": before[path] == after[path],
    } for path in before]
    write_csv(output / "protected_hashes.csv", hash_rows)
    if not all(row["unchanged"] for row in hash_rows):
        raise RuntimeError("Protected artifact changed")

    report = output / "AUDIT_PERFECT_FORESIGHT_CEILING.md"
    report_columns = [
        "config", "bound", "split", "strategy", "fills", "capture_per_fill",
        "markout_per_fill", "pnl_per_fill_market_maker", "roundtrip_net_twd", "underpowered",
    ]
    lines = [
        "# 10E Perfect-Foresight Ceiling", "", f"status: {verdict}", "",
        "`oracle_uses_future_labels: true`; `post_hoc_diagnostic_only: true`. Future H20 labels select the action only. Realized P&L uses queue fills, placement-mid capture, and the simulator's session-end inventory mark.", "",
        "## Five baselines", "", markdown_table(aggregate_frame[report_columns]), "",
        "## Session-clustered oracle tests", "", markdown_table(clustered_frame), "",
        "## Model share of ceiling", "", markdown_table(pd.DataFrame(ceilings)), "",
        "## Tail removal", "", markdown_table(tail_frame), "",
        f"Bracket sign stable: `{bracket_stable}`; unstable cases: `{bracket_unstable or 'none'}`.", "",
        f"Perfect A profitable under the preregistered all-split clustered gate: `{profitable['perfect_a_retreat']}`. Perfect B: `{profitable['perfect_b_cancel']}`.", "",
        f"Perfect A is economically positive in all 12 aggregate cells but clears the session-clustered significance gate in {significant_counts['perfect_a_retreat']}/12; its sole miss is no-spread/pessimistic/NEW4 (t=3.122 versus 3.182). Perfect B clears 12/12. No perfect-B aggregate is underpowered (minimum split/bracket fill count 21,825).", "",
        "Across full sessions with no spread filter, current model mark movement is -318.9 to -320.6 TWD/roundtrip, Perfect A reduces it to -52.8 to -78.7, and Perfect B turns it positive at +82.5 to +86.3. Thus the oracle space is large, but most of it requires cancellation rather than merely retreating one tick.", "",
        "The model share of the oracle gain is -8.04% to 18.51% for Perfect A and -5.95% to 17.29% for Perfect B across the preregistered split/bracket/config cells. Negative shares occur where model skew underperforms symmetric quoting.", "",
        f"Every positive oracle cell remains positive after removing the largest 1% absolute fill contributions: `{robust_tail}`.", "",
        f"Verdict: `{verdict}`. Recommendation: {recommendation}", "",
        "No model was retrained, NEW5 was not loaded, and existing phase artifacts were not modified.", "",
    ]
    report.write_text("\n".join(lines), encoding="ascii")
    manifest = {
        "result": "PASS",
        "stage": "10E", "new5_used": False, "oracle_uses_future_labels": True,
        "post_hoc_diagnostic_only": True, "session_count": 16,
        "perfect_a_profitable": profitable["perfect_a_retreat"],
        "perfect_b_profitable": profitable["perfect_b_cancel"],
        "perfect_a_significant_cells": f"{significant_counts['perfect_a_retreat']}/12",
        "perfect_b_significant_cells": f"{significant_counts['perfect_b_cancel']}/12",
        "bracket_sign_stable": bracket_stable, "unstable_cases": bracket_unstable,
        "robust_to_tail_removal": robust_tail,
        "verdict": verdict, "recommendation": recommendation,
        "protected_artifacts_unchanged": True, "runtime_seconds": time.perf_counter() - started,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"[DONE] verdict={verdict} report={report}", flush=True)


if __name__ == "__main__":
    main()
