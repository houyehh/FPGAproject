from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SPLITS = ("val", "new3", "new4")
SPLIT_MAP = {"val": "NEW1", "new3": "NEW3", "new4": "NEW4"}
EXPECTED = {
    "back": {"val": 0.3812, "new3": 0.3548, "new4": 0.3715},
    "proportional": {"val": 0.3891, "new3": 0.3611, "new4": 0.3777},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="16A historical fill-rate gate")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--chunksize", type=int, default=250_000)
    return parser.parse_args()


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def simulate_touch_three(market: dict[str, np.ndarray], start: int, side: int) -> tuple[int, int, int]:
    bid = market["bid"]
    ask = market["ask"]
    bid_qty = market["bid_qty"]
    ask_qty = market["ask_qty"]
    valid_book = market["valid_book"]
    trade = market["trade"]
    trade_price = market["trade_price"]
    trade_qty = market["trade_qty"]
    file_order = market["file_order"]
    price = float(bid[start] if side > 0 else ask[start])
    initial_depth = float(bid_qty[start] if side > 0 else ask_qty[start])
    q_back = initial_depth
    q_prop = initial_depth
    q_front = initial_depth
    previous_depth = initial_depth
    traded_at_price_since_book = 0.0
    outcomes = [0, 0, 0]
    source_file = int(file_order[start])
    for index in range(start + 1, len(bid)):
        if int(file_order[index]) != source_file:
            break
        if trade[index]:
            qualifies = trade_price[index] <= price if side > 0 else trade_price[index] >= price
            if qualifies:
                volume = float(trade_qty[index])
                traded_at_price_since_book += volume
                if outcomes[0] == 0:
                    q_back -= volume
                    if q_back <= 0:
                        outcomes[0] = 1
                if outcomes[1] == 0:
                    q_prop -= volume
                    if q_prop <= 0:
                        outcomes[1] = 1
                if outcomes[2] == 0:
                    q_front -= volume
                    if q_front <= 0:
                        outcomes[2] = 1
        if valid_book[index]:
            best = float(bid[index] if side > 0 else ask[index])
            new_depth = float(bid_qty[index] if side > 0 else ask_qty[index])
            swept = best < price if side > 0 else best > price
            stale = best > price if side > 0 else best < price
            if swept:
                for rule in range(3):
                    if outcomes[rule] == 0:
                        outcomes[rule] = 2
            elif stale:
                for rule in range(3):
                    if outcomes[rule] == 0:
                        outcomes[rule] = 3
            else:
                d_value = max(previous_depth - new_depth - traded_at_price_since_book, 0.0)
                if outcomes[1] == 0 and previous_depth > 0:
                    q_prop -= d_value * min(max(q_prop / previous_depth, 0.0), 1.0)
                    if q_prop <= 0:
                        outcomes[1] = 1
                if outcomes[2] == 0:
                    q_front -= d_value
                    if q_front <= 0:
                        outcomes[2] = 1
                previous_depth = new_depth
                traded_at_price_since_book = 0.0
        if outcomes[0] != 0 and outcomes[1] != 0 and outcomes[2] != 0:
            break
    return int(outcomes[0]), int(outcomes[1]), int(outcomes[2])


def main() -> None:
    args = parse_args()
    if "new5" in str(vars(args)).lower():
        raise RuntimeError("NEW5 is forbidden")
    root = args.project_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    track_c = load_module("p16a_track_c", root / "n2ew_era/09j_three_independent_tracks/04_run_track_c.py")
    registry = pd.read_csv(root / "n2ew_era/04a1_dataset_registry_patch/results/dataset_registry_expanded.csv")
    registry = registry[registry.source_group.isin(SPLIT_MAP.values())].copy()
    if registry.physical_path.astype(str).str.contains("NEW5", case=False).any():
        raise RuntimeError("NEW5 entered registry")
    manifest = pd.read_csv(root / "n2ew_era/04b_txf_only_final_development_rerun/results/txf_action_universe_manifest.csv")
    manifest = manifest[manifest.split.isin(SPLITS)].copy()
    session_rows: list[dict[str, Any]] = []
    for split in SPLITS:
        cache_path = root / f"n2ew_era/09a_deployed_model_statistics/results/decision_cache/decisions_{split}.npz"
        with np.load(cache_path) as cache:
            session_code = cache["session_code"].astype(np.int64)
            event_index = cache["event_index"].astype(np.int64)
            decision = cache["c11_guard3_hardware_faithful"].astype(np.int8)
        split_manifest = manifest[manifest.split.eq(split)].sort_values("calendar_session_id")
        for code, item in enumerate(split_manifest.itertuples(index=False)):
            session = str(item.calendar_session_id)
            rows = registry[(registry.source_group == str(item.source_group)) & registry.session_id.astype(str).eq(session)]
            market = track_c.read_session_market(rows, str(item.product_id), args.chunksize)
            positions = np.flatnonzero(session_code == code)
            action_books = market["book_positions"][100 : len(market["book_positions"]) - 100]
            raw_positions = action_books[event_index[positions]]
            selected = 0
            side_selected = {"bid": 0, "ask": 0}
            filled = {rule: 0 for rule in ("back", "proportional", "front")}
            side_filled = {(rule, side): 0 for rule in filled for side in ("bid", "ask")}
            for global_position, raw_position in zip(positions, raw_positions):
                action = int(decision[global_position])
                if action == 0:
                    continue
                side = 1 if action == 1 else -1
                side_name = "bid" if side > 0 else "ask"
                selected += 1
                side_selected[side_name] += 1
                outcomes = simulate_touch_three(market, int(raw_position), side)
                for rule, outcome in zip(("back", "proportional", "front"), outcomes):
                    if outcome in (1, 2):
                        filled[rule] += 1
                        side_filled[(rule, side_name)] += 1
            for rule in filled:
                for side_name in ("bid", "ask", "combined"):
                    denominator = selected if side_name == "combined" else side_selected[side_name]
                    numerator = filled[rule] if side_name == "combined" else side_filled[(rule, side_name)]
                    session_rows.append({
                        "split": split, "session": session, "rule": rule, "side": side_name,
                        "selected": denominator, "filled": numerator,
                        "fill_rate": numerator / denominator if denominator else float("nan"),
                    })
            print(f"[GATE] {split}/{session} selected={selected}", flush=True)
    frame = pd.DataFrame(session_rows)
    frame.to_csv(output / "fill_rate_gate_by_session.csv", index=False)
    aggregate_rows: list[dict[str, Any]] = []
    for (split, rule, side), group in frame.groupby(["split", "rule", "side"]):
        selected = int(group.selected.sum())
        filled = int(group.filled.sum())
        aggregate_rows.append({
            "split": split, "rule": rule, "side": side, "selected": selected,
            "filled": filled, "fill_rate": filled / selected,
        })
    aggregate = pd.DataFrame(aggregate_rows)
    aggregate.to_csv(output / "fill_rate_gate.csv", index=False)
    reproduced = True
    for rule, splits in EXPECTED.items():
        for split, expected in splits.items():
            actual = float(aggregate[(aggregate.split == split) & (aggregate.rule == rule) & (aggregate.side == "combined")].iloc[0].fill_rate)
            reproduced &= abs(actual - expected) <= 0.0005
    monotonic = True
    for split in SPLITS:
        for side in ("bid", "ask", "combined"):
            values = aggregate[(aggregate.split == split) & (aggregate.side == side)].set_index("rule").fill_rate
            monotonic &= bool(values["front"] >= values["proportional"] >= values["back"])
    summary = {"existing_endpoints_reproduced": reproduced, "monotonicity_holds": monotonic, "new5_used": False}
    (output / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")
    if not reproduced:
        raise RuntimeError("Historical fill-rate endpoint gate failed")
    if not monotonic:
        raise RuntimeError("Front/proportional/back monotonicity failed")
    print("[DONE] existing_endpoints_reproduced=yes monotonicity_holds=yes", flush=True)


if __name__ == "__main__":
    main()
