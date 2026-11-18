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
FEE_PER_FILL = 254.68 / 2.0
HORIZON_EVENTS = 20
SPLITS = ("train", "val", "new3", "new4")
SPLIT_SOURCE = {"train": "NEW2", "val": "NEW1", "new3": "NEW3", "new4": "NEW4"}
SPLIT_PRODUCT = {"train": "TXFB6", "val": "TXFB6", "new3": "TXFA6", "new4": "TXFA6"}
EXCLUDED_CAPTURE = "my_orderbook_20260331_9004_3.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="11B Stage 1 H20 queue-label generation")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--chunksize", type=int, default=250_000)
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
        raise ValueError(f"No rows for {path}")
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


@njit(cache=True)
def depth_at(prices: np.ndarray, quantities: np.ndarray, event: int, price: float) -> float:
    for level in range(5):
        if prices[event, level] == price:
            return quantities[event, level]
    return 0.0


@njit(parallel=True, cache=True)
def side_labels(
    side: int,
    optimistic: int,
    bid_prices: np.ndarray,
    bid_qty: np.ndarray,
    ask_prices: np.ndarray,
    ask_qty: np.ndarray,
    trade_end: np.ndarray,
    trade_price: np.ndarray,
    trade_qty: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = len(bid_prices)
    labels = np.zeros(n, dtype=np.float64)
    filled = np.zeros(n, dtype=np.uint8)
    wait_events = np.zeros(n, dtype=np.int32)
    terminal_truncated = np.zeros(n, dtype=np.uint8)
    settlement_event = np.full(n, -1, dtype=np.int64)
    for start_event in prange(n):
        placement_bid = bid_prices[start_event, 0]
        placement_ask = ask_prices[start_event, 0]
        placement_mid = (placement_bid + placement_ask) / 2.0
        if side > 0:
            order_price = placement_bid
            queue_ahead = max(bid_qty[start_event, 0], 1.0)
            visible = bid_qty[start_event, 0]
        else:
            order_price = placement_ask
            queue_ahead = max(ask_qty[start_event, 0], 1.0)
            visible = ask_qty[start_event, 0]
        fill_event = -1
        for event in range(start_event + 1, n):
            traded = 0.0
            begin = trade_end[event - 1]
            end = trade_end[event]
            for trade_index in range(begin, end):
                price = trade_price[trade_index]
                quantity = trade_qty[trade_index]
                if (side > 0 and price <= order_price) or (side < 0 and price >= order_price):
                    traded += quantity
                    queue_ahead -= quantity
                    if queue_ahead <= 0.0:
                        fill_event = event
                        break
            if fill_event >= 0:
                break
            current_bid = bid_prices[event, 0]
            current_ask = ask_prices[event, 0]
            if (side > 0 and current_bid < order_price) or (side < 0 and current_ask > order_price):
                fill_event = event
                break
            if (side > 0 and current_bid > order_price) or (side < 0 and current_ask < order_price):
                break
            if optimistic == 1:
                if side > 0:
                    new_depth = depth_at(bid_prices, bid_qty, event, order_price)
                else:
                    new_depth = depth_at(ask_prices, ask_qty, event, order_price)
                cancels = max(visible - new_depth - traded, 0.0)
                if cancels > 0.0 and visible > 0.0:
                    fraction = min(max(queue_ahead / visible, 0.0), 1.0)
                    queue_ahead -= cancels * fraction
                visible = new_depth
                if queue_ahead <= 0.0:
                    fill_event = event
                    break
        if fill_event >= 0:
            target_event = fill_event + HORIZON_EVENTS
            if target_event >= n:
                target_event = n - 1
                terminal_truncated[start_event] = 1
            settlement_mid = (bid_prices[target_event, 0] + ask_prices[target_event, 0]) / 2.0
            capture = side * (placement_mid - order_price) * POINT_VALUE
            mark_movement = side * (settlement_mid - placement_mid) * POINT_VALUE
            labels[start_event] = capture + mark_movement - FEE_PER_FILL
            filled[start_event] = 1
            wait_events[start_event] = fill_event - start_event
            settlement_event[start_event] = target_event
    return labels, filled, wait_events, terminal_truncated, settlement_event


def load_market_and_frame(
    p10a: Any,
    p05a: Any,
    registry: pd.DataFrame,
    part: Path,
    split: str,
    chunksize: int,
) -> tuple[str, pd.DataFrame, dict[str, np.ndarray]]:
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
    if len(frame) != len(market["positions"]):
        raise RuntimeError(f"Frame/market length mismatch for {split}/{session}")
    return session, frame, market


def statistics(
    split: str,
    session: str,
    bound: str,
    side: str,
    labels: np.ndarray,
    filled: np.ndarray,
    terminal_truncated: np.ndarray,
) -> dict[str, Any]:
    q = np.quantile(labels, [0.05, 0.25, 0.50, 0.75, 0.95])
    filled_labels = labels[filled.astype(bool)]
    if len(filled_labels) == 0:
        raise RuntimeError(f"No filled labels for {split}/{session}/{bound}/{side}")
    fq = np.quantile(filled_labels, [0.01, 0.50, 0.99])
    abs_p99 = float(np.quantile(np.abs(filled_labels), 0.99))
    truncated_count = int(terminal_truncated[filled.astype(bool)].sum())
    return {
        "split": split, "session": session, "bound": bound, "side": side,
        "event_count": len(labels), "zero_count": int((labels == 0).sum()),
        "zero_rate": float((labels == 0).mean()), "positive_count": int((labels > 0).sum()),
        "positive_rate": float((labels > 0).mean()), "negative_count": int((labels < 0).sum()),
        "negative_rate": float((labels < 0).mean()), "p5": float(q[0]), "p25": float(q[1]),
        "p50": float(q[2]), "p75": float(q[3]), "p95": float(q[4]),
        "filled_count": int(len(filled_labels)), "filled_p1": float(fq[0]),
        "filled_p50": float(fq[1]), "filled_p99": float(fq[2]),
        "filled_abs_p99": abs_p99, "terminal_truncated_count": truncated_count,
        "terminal_truncated_rate": truncated_count / len(filled_labels),
    }


def main() -> None:
    args = parse_args()
    if "new5" in str(vars(args)).lower():
        raise RuntimeError("NEW5 is forbidden")
    set_num_threads(args.numba_threads)
    root = args.project_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    labels_dir = output / "labels"
    labels_dir.mkdir()
    sys.path.insert(0, str(root / "n2ew_era/05a_phc_lite_microstructure_sequence_feasibility"))
    import common_05a as p05a
    p10a_path = root / "n2ew_era/10a_two_sided_market_making_pilot/01_run_pilot.py"
    p10a = load_module("p11a_p10a", p10a_path)
    registry_path = root / "n2ew_era/04a1_dataset_registry_patch/results/dataset_registry_expanded.csv"
    action_manifest = root / "n2ew_era/04b_txf_only_final_development_rerun/results/txf_action_universe_manifest.csv"
    protected = [registry_path, action_manifest, p10a_path]
    before = {str(path.relative_to(root)): sha256(path) for path in protected}
    registry = pd.read_csv(registry_path)
    registry = registry[~registry.physical_path.astype(str).str.contains("NEW5", case=False)].copy()

    stats: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    started = time.perf_counter()
    compiled = False
    expected_counts = {"train": 3, "val": 6, "new3": 6, "new4": 4}
    for split in SPLITS:
        parts = p05a.part_paths(split)
        if len(parts) != expected_counts[split]:
            raise RuntimeError(f"Unexpected {split} session count: {len(parts)}")
        for part in parts:
            session, frame, market = load_market_and_frame(p10a, p05a, registry, part, split, args.chunksize)
            if not compiled:
                n = min(1000, len(frame))
                side_labels(
                    1, 0, market["bid_prices"][:n], market["bid_qty"][:n],
                    market["ask_prices"][:n], market["ask_qty"][:n], market["trade_end"][:n],
                    market["trade_price"], market["trade_qty"],
                )
                compiled = True
            payload: dict[str, np.ndarray] = {
                "event_index": pd.to_numeric(frame["event_index"], errors="coerce").fillna(-1).to_numpy(np.int64),
                "timestamp_us": pd.to_numeric(frame["timestamp_us"], errors="coerce").fillna(-1).to_numpy(np.int64),
            }
            for bound, optimistic in (("pessimistic", 0), ("optimistic", 1)):
                for side_name, side_code in (("bid", 1), ("ask", -1)):
                    labels, filled, waits, truncated, settlement = side_labels(
                        side_code, optimistic, market["bid_prices"], market["bid_qty"],
                        market["ask_prices"], market["ask_qty"], market["trade_end"],
                        market["trade_price"], market["trade_qty"],
                    )
                    payload[f"{bound}_{side_name}_label"] = labels.astype(np.float32)
                    payload[f"{bound}_{side_name}_filled"] = filled
                    payload[f"{bound}_{side_name}_wait_events"] = waits
                    payload[f"{bound}_{side_name}_terminal_truncated"] = truncated
                    payload[f"{bound}_{side_name}_settlement_event"] = settlement
                    stats.append(statistics(split, session, bound, side_name, labels, filled, truncated))
            path = labels_dir / f"{split}_{session}_queue_labels.npz"
            np.savez_compressed(path, **payload)
            files.append({
                "split": split, "session": session, "event_count": len(frame),
                "path": str(path.relative_to(root)).replace("\\", "/"), "sha256": sha256(path),
            })
            print(f"[LABEL] {split}/{session} events={len(frame)} elapsed_s={time.perf_counter()-started:.1f}", flush=True)
        write_csv(output / f"label_statistics_{split}.csv", [row for row in stats if row["split"] == split])

    stats_frame = pd.DataFrame(stats)
    aggregate: list[dict[str, Any]] = []
    for (split, bound, side), group in stats_frame.groupby(["split", "bound", "side"]):
        # Re-read exact arrays so quantiles are event-weighted rather than session-weighted.
        arrays = []
        filled_arrays = []
        truncated_arrays = []
        for file_row in files:
            if file_row["split"] == split:
                with np.load(root / file_row["path"]) as payload:
                    arrays.append(payload[f"{bound}_{side}_label"].astype(np.float64))
                    filled_arrays.append(payload[f"{bound}_{side}_filled"].astype(np.uint8))
                    truncated_arrays.append(payload[f"{bound}_{side}_terminal_truncated"].astype(np.uint8))
        labels = np.concatenate(arrays)
        filled = np.concatenate(filled_arrays)
        truncated = np.concatenate(truncated_arrays)
        aggregate.append(statistics(split, "ALL", bound, side, labels, filled, truncated))
    write_csv(output / "label_statistics_all_sessions.csv", stats)
    write_csv(output / "label_statistics_aggregate.csv", aggregate)
    write_csv(output / "label_files.csv", files)
    mostly_zero = bool(pd.DataFrame(aggregate).zero_rate.max() > 0.80)
    label_abs_p99 = float(pd.DataFrame(aggregate).filled_abs_p99.max())
    label_scale_sane = label_abs_p99 < 3000.0
    terminal_truncated_rate = float(
        pd.DataFrame(aggregate).terminal_truncated_count.sum()
        / pd.DataFrame(aggregate).filled_count.sum()
    )

    after = {str(path.relative_to(root)): sha256(path) for path in protected}
    hashes = [{"path": key, "before_sha256": before[key], "after_sha256": after[key], "unchanged": before[key] == after[key]} for key in before]
    write_csv(output / "protected_hashes.csv", hashes)
    if not all(row["unchanged"] for row in hashes):
        raise RuntimeError("Protected artifact changed")

    report = output / "AUDIT_STAGE1_QUEUE_LABELS.md"
    aggregate_frame = pd.DataFrame(aggregate)
    lines = [
        "# 11B Stage 1 H20 Queue Labels", "", f"status: {'complete' if label_scale_sane else 'blocked'}", "",
        "The frozen 186-parameter architecture consumes 16 PHC features derived from the unchanged 13 TARGET_RAW_COLUMNS. Passing 13 tensors directly would reduce the parameter count to 162 and was therefore not done.", "",
        "The requested 16 primary sessions are val/NEW3/NEW4 and cannot supply train-only labels. The same frozen protocol was therefore also applied to the three NEW2 train sessions; only those three label files may be used for fitting. NEW3/NEW4 remain OOS diagnostics.", "",
        "Each event-side label is an independent best-quote counterfactual. Unfilled/stale/expired orders receive zero. A fill receives placement-mid spread capture plus signed movement from the fill event to 20 events after the fill, minus 127.34 TWD. If fewer than 20 events remain, the session-final mid is used and the row is marked terminal_truncated.", "",
        aggregate_frame.to_markdown(index=False), "",
        f"LABEL_SCALE_SANE: `{label_scale_sane}`; maximum filled-sample absolute p99 across split/bound/side aggregates = `{label_abs_p99:.6f}` TWD (gate < 3000).", "",
        f"TERMINAL_TRUNCATED_RATE: `{terminal_truncated_rate:.9%}` across generated filled labels.", "",
        f"LABEL_IS_MOSTLY_ZERO: `{mostly_zero}`. No class reweighting is prescribed at this stage: zeros are real unconditional outcomes, and reweighting them would bias an expected-PnL target. Stage 2 uses normalized MSE, whose conditional optimum is the expected maker P&L.", "",
        "Both pessimistic and optimistic labels are stored. Training is restricted to pessimistic train labels; optimistic labels are sensitivity-only. NEW5 was not loaded.", "",
    ]
    report.write_text("\n".join(lines), encoding="ascii")
    manifest = {
        "result": "PASS" if label_scale_sane else "BLOCKED", "stage": "11B_stage1", "new5_used": False,
        "primary_session_count": 16, "additional_train_session_count": 3,
        "label_is_mostly_zero": mostly_zero,
        "label_semantics": "independent_best_quote; placement_mid_capture + signed_H20_from_fill_mark - 127.34_per_fill; unfilled_zero",
        "horizon_events_from_fill": HORIZON_EVENTS, "label_scale_sane": label_scale_sane,
        "filled_abs_p99_max": label_abs_p99, "terminal_truncated_rate": terminal_truncated_rate,
        "training_label_bound": "pessimistic", "optimistic_sensitivity_only": True,
        "architecture_input_resolution": "13_raw_columns_to_existing_16_phc_features_keeps_186_params",
        "protected_artifacts_unchanged": True, "runtime_seconds": time.perf_counter() - started,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"[DONE] scale_sane={label_scale_sane} abs_p99={label_abs_p99:.6f} truncated={terminal_truncated_rate:.9%} report={report}", flush=True)
    if not label_scale_sane:
        raise RuntimeError(f"LABEL_SCALE_SANE failed: filled abs p99={label_abs_p99:.6f} >= 3000")


if __name__ == "__main__":
    main()
