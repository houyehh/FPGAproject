from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def mean_std(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    return float(np.mean(array)), float(np.std(array, ddof=1))


def selected_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return next(row for row in rows if row["selected_for_stage2"].lower() == "true")


def parse_csynth(path: Path) -> dict[str, int | float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    latency = re.search(r"\|\s*(\d+)\|\s*(\d+)\|\s*([0-9.]+) us\|", text)
    utilization = re.search(
        r"\|Total\s*\|\s*(\d+)\|\s*(\d+)\|\s*(\d+)\|\s*(\d+)\|", text
    )
    timing = re.search(r"\|ap_clk\s*\|\s*([0-9.]+) ns\|\s*([0-9.]+) ns\|", text)
    if latency is None or utilization is None or timing is None:
        raise RuntimeError(f"Could not parse csynth report: {path}")
    return {
        "latency_min_cycles": int(latency.group(1)),
        "latency_max_cycles": int(latency.group(2)),
        "latency_min_us": float(latency.group(3)),
        "bram_18k": int(utilization.group(1)),
        "dsp": int(utilization.group(2)),
        "ff": int(utilization.group(3)),
        "lut": int(utilization.group(4)),
        "target_clock_ns": float(timing.group(1)),
        "estimated_clock_ns": float(timing.group(2)),
    }


def fmt_pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase-dir", type=Path, required=True)
    parser.add_argument("--old-08a-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    phase = args.phase_dir.resolve()
    old_08a = args.old_08a_dir.resolve()
    if "new5" in str(phase).lower() or "new5" in str(old_08a).lower():
        raise RuntimeError("NEW5 paths are forbidden")

    results = phase / "results"
    metrics_path = results / "capacity_matched_seed_metrics.csv"
    protocol_path = results / "preregistered_protocol.json"
    rows = read_csv(metrics_path)
    if len(rows) != 6:
        raise RuntimeError(f"Expected six completed seed rows, found {len(rows)}")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))

    by_kind: dict[str, list[dict[str, str]]] = {}
    for kind in ("recurrent", "feedforward"):
        kind_rows = sorted(
            (row for row in rows if row["model_kind"] == kind), key=lambda row: int(row["seed"])
        )
        if [int(row["seed"]) for row in kind_rows] != [0, 1, 2]:
            raise RuntimeError(f"Missing seed for {kind}")
        by_kind[kind] = kind_rows

    aggregate_rows: list[dict[str, object]] = []
    for kind, kind_rows in by_kind.items():
        aggregate: dict[str, object] = {"model_kind": kind, "seed_count": len(kind_rows)}
        for metric in (
            "val_macro_f1",
            "val_weighted_f1",
            "test_macro_f1",
            "test_weighted_f1",
        ):
            mean, std = mean_std([float(row[metric]) for row in kind_rows])
            aggregate[f"{metric}_mean"] = mean
            aggregate[f"{metric}_sample_std"] = std
        aggregate_rows.append(aggregate)
    write_csv(results / "capacity_matched_aggregate.csv", aggregate_rows)

    paired_rows: list[dict[str, object]] = []
    for seed in (0, 1, 2):
        recurrent = by_kind["recurrent"][seed]
        feedforward = by_kind["feedforward"][seed]
        paired_rows.append(
            {
                "seed": seed,
                "recurrent_test_macro_f1": float(recurrent["test_macro_f1"]),
                "feedforward_test_macro_f1": float(feedforward["test_macro_f1"]),
                "recurrent_minus_feedforward": float(recurrent["test_macro_f1"])
                - float(feedforward["test_macro_f1"]),
            }
        )
    write_csv(results / "paired_seed_differences.csv", paired_rows)
    paired_mean, paired_std = mean_std(
        [float(row["recurrent_minus_feedforward"]) for row in paired_rows]
    )
    if paired_mean > paired_std:
        verdict = "recurrent_win"
        verdict_zh = "遞迴勝"
    elif paired_mean < -paired_std:
        verdict = "feedforward_win"
        verdict_zh = "前饋勝"
    else:
        verdict = "tie"
        verdict_zh = "持平"
    std_units = paired_mean / paired_std if paired_std > 0 else float("inf")

    old_selected = selected_row(old_08a / "results" / "stage2_checkpoint_selection.csv")
    new_selection_path = (
        phase
        / "precondition_08a_resynthesis"
        / "results"
        / "stage2_checkpoint_selection.csv"
    )
    new_selected = selected_row(new_selection_path)
    selection_changed = old_selected["checkpoint"] != new_selected["checkpoint"]
    prep_audit = json.loads(
        (
            phase
            / "precondition_08a_resynthesis"
            / "results"
            / "precondition_prepare_audit.json"
        ).read_text(encoding="utf-8")
    )
    csim_log = (
        phase
        / "precondition_08a_resynthesis"
        / "hls_component"
        / "hls_component"
        / "hls"
        / "csim"
        / "report"
        / "fi2010_phc_step_csim.log"
    )
    csynth_report = (
        phase
        / "precondition_08a_resynthesis"
        / "hls_component"
        / "hls_component"
        / "hls"
        / "syn"
        / "report"
        / "fi2010_phc_step_csynth.rpt"
    )
    csynth = parse_csynth(csynth_report)
    csim_text = csim_log.read_text(encoding="utf-8", errors="replace")
    csim_pass = "mismatches=0" in csim_text and "total=25600" in csim_text

    deep_lob = next(
        row
        for row in read_csv(old_08a / "results" / "published_comparisons.csv")
        if row["model"] == "DeepLOB"
    )
    recurrent_agg = next(row for row in aggregate_rows if row["model_kind"] == "recurrent")
    feedforward_agg = next(row for row in aggregate_rows if row["model_kind"] == "feedforward")
    all_early_stop = all(row["early_stop"].lower() == "true" for row in rows)

    verdict_record = {
        "paired_test_macro_f1_mean_difference": paired_mean,
        "paired_test_macro_f1_sample_std": paired_std,
        "difference_in_paired_std_units": std_units,
        "verdict": verdict,
        "threshold_rule": protocol["verdict_rule"],
        "both_sides_converged_naturally": all_early_stop,
        "new5_used": False,
    }
    (results / "verdict.json").write_text(
        json.dumps(verdict_record, indent=2) + "\n", encoding="ascii"
    )

    seed_lines = []
    for row in sorted(rows, key=lambda row: (row["model_kind"], int(row["seed"]))):
        seed_lines.append(
            f"| {row['model_kind']} | {row['seed']} | {row['best_epoch']} | "
            f"{row['stop_epoch']} | {row['stop_reason']} | {fmt_pct(float(row['val_macro_f1']))} | "
            f"{fmt_pct(float(row['test_macro_f1']))} | {fmt_pct(float(row['test_weighted_f1']))} |"
        )

    report = f"""status: resolved

# FI-2010 Capacity-Matched Recurrent vs Feedforward

## Scope and verification boundary

- Dataset: FI-2010 NoAuction Zscore Setup 2 cache already prepared by 08A.
- Horizon: k={protocol['horizon_k']}, preregistered before training.
- NEW5: not accessed.
- Model training and F1 values: measured PyTorch results.
- 08A prerequisite CSim/csynth: measured Vitis HLS results; no implementation or P&R claim is made.
- Test metrics were computed only after each validation-selected checkpoint was frozen.

## Prerequisite: 08A test-isolated resynthesis

`08A_RESYNTHESIS: done`

`SELECTED_CHECKPOINT_CHANGED_VS_OLD: {'yes' if selection_changed else 'no'}`

| Selection | Seed | Val macro-F1 | Test macro-F1 | Checkpoint |
|---|---:|---:|---:|---|
| old, invalid test-ranked median | {old_selected['seed']} | {fmt_pct(float(old_selected['val_macro_f1']))} | {fmt_pct(float(old_selected['test_macro_f1']))} | `{old_selected['checkpoint']}` |
| corrected val-ranked median | {new_selected['seed']} | {fmt_pct(float(new_selected['val_macro_f1']))} | {fmt_pct(float(new_selected['test_macro_f1']))} | `{new_selected['checkpoint']}` |

The corrected selection changed from seed {old_selected['seed']} to seed {new_selected['seed']}. The isolated rerun left protected 08A files unchanged: `{prep_audit['protected_08a_unchanged']}`.

| HLS check for corrected seed | Result | Evidence |
|---|---:|---|
| CSim | {'25,600/25,600, 0 mismatch' if csim_pass else 'failed or unparsed'} | `{csim_log}` |
| csynth latency | {csynth['latency_max_cycles']} cycles / {csynth['latency_min_us']:.3f} us at 10 ns target | `{csynth_report}` |
| csynth resources | DSP {csynth['dsp']}, LUT {csynth['lut']}, FF {csynth['ff']}, BRAM_18K {csynth['bram_18k']} | `{csynth_report}` |

These are CSim and csynth results, not routed timing or board measurements.

## Preregistered comparison

`RECURRENT: {protocol['recurrent_parameter_count']} parameters | stateful`

- encoder weight `[4, 40]`, bias `[4]`
- LayerNorm weight/bias `[4]` each
- diagonal decay `[4]`, diagonal gain `[4]`
- readout weight `[3, 4]`, bias `[3]`

`FEEDFORWARD: {protocol['feedforward_parameter_count']} parameters | stateless`

- hidden weight `[4, 40]`, bias `[4]`
- SiLU
- readout weight `[3, 4]`, bias `[3]`

`PARAM_COUNT_DELTA: {protocol['parameter_delta_pct_vs_feedforward']:.2f}%` relative to feedforward, within the preregistered +/-15% bound.

`HORIZON_K: {protocol['horizon_k']}`

`LR_SCHEDULE: AdamW(lr={protocol['learning_rate']}, weight_decay={protocol['weight_decay']}); CosineAnnealingLR(T_max={protocol['lr_t_max']}, eta_min={protocol['lr_eta_min']}); identical for both sides.`

Common budget: max {protocol['max_epochs']} epochs, patience {protocol['patience']}, min_delta {protocol['min_delta']}, batch {protocol['batch_size']}, raw cross-entropy, seeds 0/1/2.

## Per-seed results

| Model | Seed | Best epoch | Stop epoch | Stop reason | Val macro-F1 | Test macro-F1 | Test weighted-F1 |
|---|---:|---:|---:|---|---:|---:|---:|
{chr(10).join(seed_lines)}

`BOTH_SIDES_CONVERGED_NATURALLY: {'yes' if all_early_stop else 'no'}`

## Three-seed aggregate

| Model | Val macro-F1 mean +/- sample std | Test macro-F1 mean +/- sample std |
|---|---:|---:|
| recurrent | {fmt_pct(float(recurrent_agg['val_macro_f1_mean']))} +/- {fmt_pct(float(recurrent_agg['val_macro_f1_sample_std']))} | {fmt_pct(float(recurrent_agg['test_macro_f1_mean']))} +/- {fmt_pct(float(recurrent_agg['test_macro_f1_sample_std']))} |
| feedforward | {fmt_pct(float(feedforward_agg['val_macro_f1_mean']))} +/- {fmt_pct(float(feedforward_agg['val_macro_f1_sample_std']))} | {fmt_pct(float(feedforward_agg['test_macro_f1_mean']))} +/- {fmt_pct(float(feedforward_agg['test_macro_f1_sample_std']))} |

Primary paired test macro-F1 difference (recurrent - feedforward): {100.0 * paired_mean:.2f} percentage points. Paired-seed sample standard deviation: {100.0 * paired_std:.2f} percentage points. Difference: {std_units:.3f} seed standard deviations.

`VERDICT: {verdict_zh}`

The verdict uses the preregistered paired-seed threshold. If the result is feedforward win, it narrows the TXF conclusion rather than being adjusted away.

## Weighted-F1 reference table

Weighted-F1 is listed separately from the macro-F1 primary endpoint.

| Model | Test weighted-F1 mean +/- sample std | Metric status |
|---|---:|---|
| recurrent | {fmt_pct(float(recurrent_agg['test_weighted_f1_mean']))} +/- {fmt_pct(float(recurrent_agg['test_weighted_f1_sample_std']))} | measured, three seeds |
| feedforward | {fmt_pct(float(feedforward_agg['test_weighted_f1_mean']))} +/- {fmt_pct(float(feedforward_agg['test_weighted_f1_sample_std']))} | measured, three seeds |
| DeepLOB | {float(deep_lob['f1_k50']):.2f}% | published weighted-F1 reference; not used in the macro-F1 verdict |

DeepLOB source recorded by 08A: {deep_lob['source']} ({deep_lob['source_url']}). No direct macro-F1 comparison is claimed.

## Files created

- `{phase / '00_resynthesize_08a_test_isolated.py'}`
- `{phase / '01_train_capacity_matched.py'}`
- `{phase / '02_summarize_capacity_matched.py'}`
- `{protocol_path}`
- `{metrics_path}`
- `{results / 'capacity_matched_aggregate.csv'}`
- `{results / 'paired_seed_differences.csv'}`
- `{results / 'verdict.json'}`
- `{phase / 'models'}`
- `{phase / 'precondition_08a_resynthesis'}`

## Honest conclusion

The measured FI-2010 result is **{verdict_zh}** under the preregistered one-paired-seed-standard-deviation rule. This claim is limited to FI-2010 Setup 2, k=50, the stated 195-vs-179 parameter comparison, and three seeds. It neither changes the TXF result nor establishes a dataset-independent advantage.
"""
    (phase / "CAPACITY_MATCHED_FI2010_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps(verdict_record, indent=2))


if __name__ == "__main__":
    main()
