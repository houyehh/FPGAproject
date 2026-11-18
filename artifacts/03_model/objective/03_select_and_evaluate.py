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
import torch
from numba import njit, set_num_threads


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

POINT_VALUE = 200.0
FEE_SCENARIOS = {"retail": 372.0, "proprietary": 292.0, "market_maker": 254.68}
SPLITS = ("val", "new3", "new4")
CONFIGS = (("no_spread_filter", 0), ("spread_ge_2", 2))
BOUNDS = (("pessimistic", 0), ("optimistic", 1))
CAP = 3
MIN_FILLS_VAL = 1000
CHUNK_LENGTH = 2048
CRITICAL = {6: 2.5705818356, 4: 3.1824463053}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="11B Stage 3 H20 selection and evaluation")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--stage1-dir", type=Path, required=True)
    parser.add_argument("--stage2-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
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
        raise ValueError(path)
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(frame: pd.DataFrame) -> str:
    cols = list(frame.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
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
def simulate(
    bid_prices: np.ndarray,
    bid_qty: np.ndarray,
    ask_prices: np.ndarray,
    ask_qty: np.ndarray,
    trade_end: np.ndarray,
    trade_price: np.ndarray,
    trade_qty: np.ndarray,
    scores: np.ndarray,
    tau: float,
    optimistic: int,
    spread_threshold: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    n = len(scores)
    contributions = np.empty(n, dtype=np.float64)
    contribution_sides = np.empty(n, dtype=np.int8)
    contribution_mids = np.empty(n, dtype=np.float64)
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
            for trade_index in range(trade_end[event - 1], trade_end[event]):
                price = trade_price[trade_index]
                quantity = trade_qty[trade_index]
                if bid_active and price <= bid_order_price:
                    bid_traded += quantity
                    bid_queue -= quantity
                    if bid_queue <= 0.0:
                        inventory += 1
                        cash -= bid_order_price * POINT_VALUE
                        capture += (bid_place_mid - bid_order_price) * POINT_VALUE
                        contributions[fill_count] = (bid_place_mid - bid_order_price) * POINT_VALUE
                        contribution_sides[fill_count] = 1
                        contribution_mids[fill_count] = bid_place_mid
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
                        contributions[fill_count] = (ask_order_price - ask_place_mid) * POINT_VALUE
                        contribution_sides[fill_count] = -1
                        contribution_mids[fill_count] = ask_place_mid
                        fill_count += 1
                        sell_fills += 1
                        ask_active = False
            if bid_active and bid < bid_order_price:
                inventory += 1
                cash -= bid_order_price * POINT_VALUE
                capture += (bid_place_mid - bid_order_price) * POINT_VALUE
                contributions[fill_count] = (bid_place_mid - bid_order_price) * POINT_VALUE
                contribution_sides[fill_count] = 1
                contribution_mids[fill_count] = bid_place_mid
                fill_count += 1
                buy_fills += 1
                bid_active = False
            if ask_active and ask > ask_order_price:
                inventory -= 1
                cash += ask_order_price * POINT_VALUE
                capture += (ask_order_price - ask_place_mid) * POINT_VALUE
                contributions[fill_count] = (ask_order_price - ask_place_mid) * POINT_VALUE
                contribution_sides[fill_count] = -1
                contribution_mids[fill_count] = ask_place_mid
                fill_count += 1
                sell_fills += 1
                ask_active = False
            if optimistic == 1:
                if bid_active:
                    new_depth = depth_at(bid_prices, bid_qty, event, bid_order_price)
                    cancels = max(bid_visible - new_depth - bid_traded, 0.0)
                    if cancels > 0.0 and bid_visible > 0.0:
                        bid_queue -= cancels * min(max(bid_queue / bid_visible, 0.0), 1.0)
                    bid_visible = new_depth
                    if bid_queue <= 0.0:
                        inventory += 1
                        cash -= bid_order_price * POINT_VALUE
                        capture += (bid_place_mid - bid_order_price) * POINT_VALUE
                        contributions[fill_count] = (bid_place_mid - bid_order_price) * POINT_VALUE
                        contribution_sides[fill_count] = 1
                        contribution_mids[fill_count] = bid_place_mid
                        fill_count += 1
                        buy_fills += 1
                        bid_active = False
                if ask_active:
                    new_depth = depth_at(ask_prices, ask_qty, event, ask_order_price)
                    cancels = max(ask_visible - new_depth - ask_traded, 0.0)
                    if cancels > 0.0 and ask_visible > 0.0:
                        ask_queue -= cancels * min(max(ask_queue / ask_visible, 0.0), 1.0)
                    ask_visible = new_depth
                    if ask_queue <= 0.0:
                        inventory -= 1
                        cash += ask_order_price * POINT_VALUE
                        capture += (ask_order_price - ask_place_mid) * POINT_VALUE
                        contributions[fill_count] = (ask_order_price - ask_place_mid) * POINT_VALUE
                        contribution_sides[fill_count] = -1
                        contribution_mids[fill_count] = ask_place_mid
                        fill_count += 1
                        sell_fills += 1
                        ask_active = False
        spread = ask - bid
        if spread < spread_threshold:
            bid_active = False
            ask_active = False
        else:
            eligible_events += 1
            quote_bid = scores[event, 0] >= tau and inventory < CAP
            quote_ask = scores[event, 1] >= tau and inventory > -CAP
            if inventory >= CAP or inventory <= -CAP:
                cap_stops += 1
            if not quote_bid:
                bid_active = False
            elif (not bid_active) or bid_order_price != bid:
                visible = bid_qty[event, 0]
                bid_active = True
                bid_order_price = bid
                bid_queue = max(visible, 1.0)
                bid_visible = visible
                bid_place_mid = mid
            if not quote_ask:
                ask_active = False
            elif (not ask_active) or ask_order_price != ask:
                visible = ask_qty[event, 0]
                ask_active = True
                ask_order_price = ask
                ask_queue = max(visible, 1.0)
                ask_visible = visible
                ask_place_mid = mid
        abs_inventory_sum += abs(inventory)
    final_mid = (bid_prices[n - 1, 0] + ask_prices[n - 1, 0]) / 2.0
    gross = cash + inventory * final_mid * POINT_VALUE
    for index in range(fill_count):
        contributions[index] += contribution_sides[index] * (final_mid - contribution_mids[index]) * POINT_VALUE
    result = np.zeros(9, dtype=np.float64)
    result[0] = buy_fills
    result[1] = sell_fills
    result[2] = fill_count
    result[3] = gross
    result[4] = capture
    result[5] = abs_inventory_sum / n
    result[6] = cap_stops / n
    result[7] = inventory
    result[8] = eligible_events
    return result, contributions, fill_count


def load_model_scores(
    root: Path, stage1: Path, stage2: Path, seed: int, split: str, p05a: Any, p11s1: Any,
    p10a: Any, p11train: Any, registry: pd.DataFrame, cache_dir: Path,
) -> dict[str, np.ndarray]:
    checkpoint = torch.load(stage2 / "models" / f"toxicity_hidden8_seed{seed}_best.pt", map_location="cpu", weights_only=False)
    from models.phc_diagonal_hidden8 import PHCDiagonalSSMHidden8
    model = p11train.ContinuousToxicityModel(PHCDiagonalSSMHidden8(16, 8, 1, 0.0))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    sessions = p11train.load_split_sessions(
        split, root, stage1,
        cache_dir, p05a, p11s1, p10a, registry,
    )
    return p11train.predict_sessions(model, sessions, float(checkpoint["target_scale"]))


def result_row(result: np.ndarray, split: str, session: str, config: str, bound: str, tau: float) -> dict[str, Any]:
    fills = int(result[2])
    gross = float(result[3])
    return {
        "split": split, "session": session, "config": config, "bound": bound,
        "strategy": "new_toxicity_model", "tau": tau, "fill_count": fills,
        "buy_fills": int(result[0]), "sell_fills": int(result[1]),
        "gross_pnl": gross, "capture_per_fill": float(result[4]) / fills if fills else math.nan,
        "markout_per_fill": (gross - float(result[4])) / fills if fills else math.nan,
        "gross_per_fill": gross / fills if fills else math.nan,
        "maker_pnl_per_fill": gross / fills - FEE_SCENARIOS["market_maker"] / 2 if fills else math.nan,
        "roundtrip_net_twd": 2 * (gross / fills - FEE_SCENARIOS["market_maker"] / 2) if fills else math.nan,
        "mean_abs_inventory": float(result[5]), "inventory_cap_stop_rate": float(result[6]),
        "terminal_inventory_before_close": int(result[7]), "final_inventory_after_close": 0,
        "underpowered": fills < 1000,
    }


def main() -> None:
    args = parse_args()
    if "new5" in str(vars(args)).lower():
        raise RuntimeError("NEW5 is forbidden")
    set_num_threads(args.numba_threads)
    root = args.project_root.resolve()
    stage1 = args.stage1_dir.resolve()
    stage2 = args.stage2_dir.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    cache_dir = output / "feature_cache"
    cache_dir.mkdir()
    sys.path.insert(0, str(root / "n2ew_era/05a_phc_lite_microstructure_sequence_feasibility"))
    sys.path.insert(0, str(root / "n2ew_era/07s_diagonal_hidden8"))
    import common_05a as p05a
    p10a = load_module("p11a_p10a_eval", root / "n2ew_era/10a_two_sided_market_making_pilot/01_run_pilot.py")
    p11s1 = load_module("p11b_s1_eval", root / "n2ew_era/11b_toxicity_objective_retrain_v2/01_generate_queue_labels.py")
    p11train = load_module("p11b_train_eval", root / "n2ew_era/11b_toxicity_objective_retrain_v2/02_train_toxicity.py")
    registry_path = root / "n2ew_era/04a1_dataset_registry_patch/results/dataset_registry_expanded.csv"
    ten_e_summary = root / "n2ew_era/10e_perfect_foresight_ceiling/results/run1/five_baseline_summary.csv"
    ten_e_sessions = root / "n2ew_era/10e_perfect_foresight_ceiling/results/run1/session_results_all.csv"
    protected = [registry_path, ten_e_summary, ten_e_sessions, stage1 / "manifest.json", stage2 / "manifest.json"]
    before = {str(path.relative_to(root)): sha256(path) for path in protected}
    registry = pd.read_csv(registry_path)
    registry = registry[~registry.physical_path.astype(str).str.contains("NEW5", case=False)].copy()

    # Stage 3a: val-only seed and threshold selection.
    val_markets: dict[str, dict[str, np.ndarray]] = {}
    for part in p05a.part_paths("val"):
        session, _, market = p11s1.load_market_and_frame(p10a, p05a, registry, part, "val", 250_000)
        val_markets[session] = market
    search_rows: list[dict[str, Any]] = []
    compiled = False
    symmetric_total_gross = 0.0
    symmetric_total_fills = 0
    for session, market in val_markets.items():
        symmetric_scores = np.ones((len(market["bid_prices"]), 2), dtype=np.float32)
        result, _, _ = simulate(
            market["bid_prices"], market["bid_qty"], market["ask_prices"], market["ask_qty"],
            market["trade_end"], market["trade_price"], market["trade_qty"], symmetric_scores,
            0.0, 0, 0,
        )
        symmetric_total_gross += float(result[3])
        symmetric_total_fills += int(result[2])
    symmetric_total_maker = (
        symmetric_total_gross - symmetric_total_fills * FEE_SCENARIOS["market_maker"] / 2
    )
    for seed in (0, 1, 2):
        val_scores = {}
        for score_path in sorted((stage2 / "val_scores").glob(f"seed{seed}_val_*_scores.npz")):
            session = score_path.stem.split("_val_", 1)[1].rsplit("_scores", 1)[0]
            with np.load(score_path) as payload:
                val_scores[session] = payload["scores"].astype(np.float32)
        all_scores = np.concatenate([val_scores[key].reshape(-1) for key in sorted(val_scores)])
        quantiles = np.arange(0.10, 0.91, 0.10)
        taus = np.unique(np.quantile(all_scores, quantiles))
        for tau in taus:
            total_gross = 0.0
            total_fills = 0
            for session, scores in val_scores.items():
                market = val_markets[session]
                if not compiled:
                    n = min(1000, len(scores))
                    simulate(
                        market["bid_prices"][:n], market["bid_qty"][:n], market["ask_prices"][:n],
                        market["ask_qty"][:n], market["trade_end"][:n], market["trade_price"],
                        market["trade_qty"], scores[:n], float(tau), 0, 0,
                    )
                    compiled = True
                result, _, _ = simulate(
                    market["bid_prices"], market["bid_qty"], market["ask_prices"], market["ask_qty"],
                    market["trade_end"], market["trade_price"], market["trade_qty"], scores,
                    float(tau), 0, 0,
                )
                total_gross += float(result[3])
                total_fills += int(result[2])
            total_maker = total_gross - total_fills * FEE_SCENARIOS["market_maker"] / 2
            search_rows.append({
                "seed": seed, "tau": float(tau), "selection_split": "val",
                "selection_bound": "pessimistic", "selection_config": "no_spread_filter",
                "fill_count": total_fills, "gross_pnl": total_gross,
                "total_maker_pnl": total_maker,
                "symmetric_total_maker_pnl": symmetric_total_maker,
                "improvement_vs_symmetric": total_maker - symmetric_total_maker,
                "maker_pnl_per_fill": total_maker / total_fills if total_fills else math.nan,
                "eligible_min_fills": total_fills >= MIN_FILLS_VAL,
                "degenerate_candidate": total_fills < MIN_FILLS_VAL or total_fills == 0,
                "new3_used": False, "new4_used": False, "new5_used": False,
            })
    write_csv(output / "threshold_search_val_only.csv", search_rows)
    eligible_rows = [row for row in search_rows if row["eligible_min_fills"]]
    if not eligible_rows:
        raise RuntimeError(f"No val threshold candidate reaches MIN_FILLS_VAL={MIN_FILLS_VAL}")
    if any(row["total_maker_pnl"] >= 0.0 for row in eligible_rows):
        selection_criterion = "absolute"
        chosen = max(eligible_rows, key=lambda row: (row["total_maker_pnl"], -row["fill_count"]))
    else:
        selection_criterion = "relative_to_symmetric"
        chosen = max(eligible_rows, key=lambda row: (row["improvement_vs_symmetric"], -row["fill_count"]))
    no_viable_operating_point = bool(
        chosen["total_maker_pnl"] < 0.0 and chosen["improvement_vs_symmetric"] < 0.0
    )
    selected_seed = int(chosen["seed"])
    selected_tau = float(chosen["tau"])
    checkpoint_path = stage2 / "models" / f"toxicity_hidden8_seed{selected_seed}_best.pt"
    frozen = {
        "status": "frozen_before_new3_new4_load", "seed": selected_seed, "tau": selected_tau,
        "selection_split": "val", "selection_bound": "pessimistic",
        "selection_config": "no_spread_filter", "selection_criterion": selection_criterion,
        "selection_metric": "total_maker_pnl" if selection_criterion == "absolute" else "improvement_vs_symmetric",
        "minimum_val_fills": MIN_FILLS_VAL, "no_viable_operating_point": no_viable_operating_point,
        "val_total_maker_pnl": chosen["total_maker_pnl"], "val_fill_count": chosen["fill_count"],
        "val_symmetric_total_maker_pnl": symmetric_total_maker,
        "val_improvement_vs_symmetric": chosen["improvement_vs_symmetric"],
        "checkpoint": str(checkpoint_path.relative_to(root)).replace("\\", "/"),
        "checkpoint_sha256": sha256(checkpoint_path), "new3_loaded_at_freeze": False,
        "new4_loaded_at_freeze": False, "new5_loaded": False,
    }
    (output / "frozen_selection_manifest.json").write_text(json.dumps(frozen, indent=2) + "\n", encoding="ascii")
    print(f"[SELECT] criterion={selection_criterion} seed={selected_seed} tau={selected_tau:.9g} fills={chosen['fill_count']} val_total={chosen['total_maker_pnl']:.2f} delta_sym={chosen['improvement_vs_symmetric']:.2f} no_viable={no_viable_operating_point}", flush=True)

    scores_by_split: dict[str, dict[str, np.ndarray]] = {"val": {}}
    for path in sorted((stage2 / "val_scores").glob(f"seed{selected_seed}_val_*_scores.npz")):
        session = path.stem.split("_val_", 1)[1].rsplit("_scores", 1)[0]
        with np.load(path) as payload:
            scores_by_split["val"][session] = payload["scores"].astype(np.float32)
    for split in ("new3", "new4"):
        scores_by_split[split] = load_model_scores(
            root, stage1, stage2, selected_seed, split, p05a, p11s1, p10a, p11train, registry, cache_dir
        )

    session_rows: list[dict[str, Any]] = []
    tail_chunks: dict[tuple[str, str, str], list[np.ndarray]] = {}
    for split in SPLITS:
        split_rows: list[dict[str, Any]] = []
        for part in p05a.part_paths(split):
            session, _, market = p11s1.load_market_and_frame(p10a, p05a, registry, part, split, 250_000)
            scores = scores_by_split[split][session]
            for config, spread_threshold in CONFIGS:
                for bound, optimistic in BOUNDS:
                    result, contributions, fills = simulate(
                        market["bid_prices"], market["bid_qty"], market["ask_prices"], market["ask_qty"],
                        market["trade_end"], market["trade_price"], market["trade_qty"], scores,
                        selected_tau, optimistic, spread_threshold,
                    )
                    row = result_row(result, split, session, config, bound, selected_tau)
                    split_rows.append(row)
                    maker_contributions = contributions[:fills].copy() - FEE_SCENARIOS["market_maker"] / 2
                    if abs(float(maker_contributions.sum()) - (float(result[3]) - fills * FEE_SCENARIOS["market_maker"] / 2)) > 1e-6:
                        raise RuntimeError("Fill contribution identity failed")
                    tail_chunks.setdefault((config, bound, split), []).append(maker_contributions)
            print(f"[EVAL] {split}/{session}", flush=True)
        write_csv(output / f"new_model_session_results_{split}.csv", split_rows)
        session_rows.extend(split_rows)

    session_frame = pd.DataFrame(session_rows)
    aggregate_rows: list[dict[str, Any]] = []
    for (config, bound, split), group in session_frame.groupby(["config", "bound", "split"]):
        fills = int(group.fill_count.sum())
        gross = float(group.gross_pnl.sum())
        capture = float((group.capture_per_fill * group.fill_count).sum())
        aggregate_rows.append({
            "config": config, "bound": bound, "split": split, "strategy": "new_toxicity_model",
            "fills": fills, "capture_per_fill": capture / fills,
            "markout_per_fill": (gross - capture) / fills,
            "pnl_per_fill_market_maker": gross / fills - FEE_SCENARIOS["market_maker"] / 2,
            "roundtrip_net_twd": 2 * (gross / fills - FEE_SCENARIOS["market_maker"] / 2),
            "underpowered": fills < 1000,
        })
    write_csv(output / "new_model_session_results_all.csv", session_rows)
    write_csv(output / "new_model_aggregate.csv", aggregate_rows)
    selected_point_fills = {
        row["split"]: int(row["fills"])
        for row in aggregate_rows
        if row["config"] == "no_spread_filter" and row["bound"] == "pessimistic"
    }

    old_summary = pd.read_csv(ten_e_summary)
    comparison = pd.concat([old_summary, pd.DataFrame(aggregate_rows)], ignore_index=True, sort=False)
    comparison = comparison[comparison.strategy.isin([
        "symmetric", "random_skew", "model_skew", "perfect_a_retreat",
        "perfect_b_cancel", "new_toxicity_model",
    ])]
    write_csv(output / "six_baseline_comparison.csv", comparison.to_dict("records"))

    paired_rows: list[dict[str, Any]] = []
    old_sessions = pd.read_csv(ten_e_sessions)
    old_sym = old_sessions[old_sessions.strategy.eq("symmetric")]
    for (config, bound, split), group in session_frame.groupby(["config", "bound", "split"]):
        symmetric = old_sym[(old_sym.config == config) & (old_sym.bound == bound) & (old_sym.split == split)]
        merged = group[["session", "maker_pnl_per_fill"]].merge(
            symmetric[["session", "maker_pnl_per_fill"]], on="session", suffixes=("_new", "_symmetric")
        )
        differences = (merged.maker_pnl_per_fill_new - merged.maker_pnl_per_fill_symmetric).to_numpy(np.float64)
        n = len(differences)
        mean = float(differences.mean())
        std = float(differences.std(ddof=1))
        se = std / math.sqrt(n)
        t_value = mean / se if se > 0 else math.copysign(math.inf, mean)
        paired_rows.append({
            "config": config, "bound": bound, "split": split, "session_count": n,
            "paired_differences": ";".join(f"{x:.12g}" for x in differences),
            "mean_difference": mean, "std_difference": std, "se_clustered": se,
            "t": t_value, "df": n - 1, "critical": CRITICAL[n],
            "significantly_better_than_symmetric": mean > 0 and t_value > CRITICAL[n],
        })
    write_csv(output / "paired_vs_symmetric.csv", paired_rows)
    paired_frame = pd.DataFrame(paired_rows)

    ceiling_rows: list[dict[str, Any]] = []
    for (config, bound, split), group in comparison.groupby(["config", "bound", "split"]):
        values = group.set_index("strategy").pnl_per_fill_market_maker
        ceiling_rows.append({
            "config": config, "bound": bound, "split": split,
            "new_model_share_of_ceiling_b": (values["new_toxicity_model"] - values["symmetric"]) / (values["perfect_b_cancel"] - values["symmetric"]),
            "old_model_share_of_ceiling_b": (values["model_skew"] - values["symmetric"]) / (values["perfect_b_cancel"] - values["symmetric"]),
        })
    write_csv(output / "ceiling_shares.csv", ceiling_rows)

    tail_rows: list[dict[str, Any]] = []
    for key, chunks in tail_chunks.items():
        contributions = np.concatenate(chunks)
        remove_n = max(1, int(math.ceil(len(contributions) * 0.01)))
        remove = np.argpartition(np.abs(contributions), -remove_n)[-remove_n:]
        keep = np.ones(len(contributions), dtype=bool)
        keep[remove] = False
        original = float(contributions.mean())
        trimmed = float(contributions[keep].mean())
        tail_rows.append({
            "config": key[0], "bound": key[1], "split": key[2], "fill_count": len(contributions),
            "removed_count": remove_n, "original_pnl_per_fill": original,
            "trimmed_pnl_per_fill": trimmed, "original_positive": original > 0,
            "trimmed_positive": trimmed > 0,
            "robust_to_tail_removal": (original <= 0) or (trimmed > 0),
        })
    write_csv(output / "tail_removal_sensitivity.csv", tail_rows)
    tail_frame = pd.DataFrame(tail_rows)

    bracket_unstable: list[str] = []
    for config in [x[0] for x in CONFIGS]:
        for split in SPLITS:
            values = paired_frame[(paired_frame.config == config) & (paired_frame.split == split)].set_index("bound").mean_difference
            if np.sign(values["pessimistic"]) != np.sign(values["optimistic"]):
                bracket_unstable.append(f"{config}:{split}")
    bracket_stable = not bracket_unstable
    significant_all = bool(paired_frame.significantly_better_than_symmetric.all())
    mean_positive_all = bool((paired_frame.mean_difference > 0).all())

    profitability_rows: list[dict[str, Any]] = []
    for fee_name, roundtrip_fee in FEE_SCENARIOS.items():
        for (config, bound, split), group in session_frame.groupby(["config", "bound", "split"]):
            values = group.gross_per_fill.to_numpy(np.float64) - roundtrip_fee / 2
            n = len(values)
            mean = float(values.mean())
            std = float(values.std(ddof=1))
            se = std / math.sqrt(n)
            t_value = mean / se if se > 0 else math.copysign(math.inf, mean)
            profitability_rows.append({
                "fee_scenario": fee_name, "config": config, "bound": bound, "split": split,
                "session_mean_pnl_per_fill": mean, "t": t_value, "df": n - 1,
                "significantly_positive": mean > 0 and t_value > CRITICAL[n],
            })
    write_csv(output / "profitability_by_fee.csv", profitability_rows)
    profit_frame = pd.DataFrame(profitability_rows)
    profitable_under = []
    for fee in FEE_SCENARIOS:
        subset = profit_frame[profit_frame.fee_scenario == fee]
        if len(subset) == 12 and subset.significantly_positive.all():
            profitable_under.append(fee)

    positive_tail = tail_frame[tail_frame.original_positive]
    robust_tail = bool(positive_tail.robust_to_tail_removal.all()) if not positive_tail.empty else "not_applicable"
    if significant_all and bracket_stable and robust_tail is not False:
        verdict = "success"
        next_step = "The toxicity objective is supported; freeze the software result and start fixed-point portability checks before any HLS rebuild."
    elif mean_positive_all:
        verdict = "partial"
        next_step = "The objective has directional value but is not yet a stable deployable claim; inspect session failures before hardware work."
    else:
        verdict = "failure"
        next_step = "Existing features do not reliably predict realized toxicity; feature engineering is the next justified step."

    after = {str(path.relative_to(root)): sha256(path) for path in protected}
    hashes = [{"path": key, "before_sha256": before[key], "after_sha256": after[key], "unchanged": before[key] == after[key]} for key in before]
    write_csv(output / "protected_hashes.csv", hashes)
    if not all(row["unchanged"] for row in hashes):
        raise RuntimeError("Protected artifact changed")

    report = output / "AUDIT_STAGE3_TOXICITY_EVALUATION.md"
    report_cols = ["config", "bound", "split", "strategy", "fills", "capture_per_fill", "markout_per_fill", "pnl_per_fill_market_maker", "roundtrip_net_twd", "underpowered"]
    lines = [
        "# 11B Stage 3 H20 Toxicity Evaluation", "", f"status: {verdict}", "",
        f"SELECTION_CRITERION: `{selection_criterion}`. SELECTED_TAU: `{selected_tau}`; selected seed `{selected_seed}` with val fills `{chosen['fill_count']}` (minimum `{MIN_FILLS_VAL}`). The manifest was frozen before NEW3/NEW4 were loaded.", "",
        f"NO_VIABLE_OPERATING_POINT: `{no_viable_operating_point}`. SELECTED_POINT_FILLS (pessimistic/no-spread): `{selected_point_fills}`.", "",
        "## Six baselines", "", markdown_table(comparison[report_cols]), "",
        "## Session-clustered paired tests versus symmetric quoting", "", markdown_table(paired_frame), "",
        "## Ceiling share", "", markdown_table(pd.DataFrame(ceiling_rows)), "",
        "## Tail removal", "", markdown_table(tail_frame), "",
        f"BRACKET_SIGN_STABLE: `{bracket_stable}`; unstable cells: `{bracket_unstable or 'none'}`.", "",
        f"PROFITABLE_UNDER: `{profitable_under or 'none'}`. ROBUST_TO_TAIL_REMOVAL: `{robust_tail}`.", "",
        f"VERDICT: `{verdict}`. NEXT_STEP_INDICATED: {next_step}", "",
        "The statistical unit is the session. No per-fill standard errors are used. NEW5 was not loaded.", "",
    ]
    report.write_text("\n".join(lines), encoding="ascii")
    manifest = {
        "result": "PASS", "stage": "11B_stage3", "selected_seed": selected_seed,
        "selected_tau": selected_tau, "selection_split": "val",
        "selection_criterion": selection_criterion,
        "minimum_val_fills": MIN_FILLS_VAL,
        "no_viable_operating_point": no_viable_operating_point,
        "selected_point_fills": selected_point_fills,
        "threshold_frozen_before_oos": True, "new_model_share_of_ceiling_b": ceiling_rows,
        "bracket_sign_stable": bracket_stable, "unstable_cells": bracket_unstable,
        "profitable_under": profitable_under, "robust_to_tail_removal": robust_tail,
        "verdict": verdict, "next_step_indicated": next_step,
        "new5_used": False, "protected_artifacts_unchanged": True,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"[DONE] verdict={verdict} report={report}", flush=True)


if __name__ == "__main__":
    main()
