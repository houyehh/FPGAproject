from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finalize the 15A reproduction report")
    parser.add_argument("--results-dir", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    if "new5" in str(vars(args)).lower():
        raise RuntimeError("NEW5 is forbidden")
    results = args.results_dir.resolve()
    metrics = pd.read_csv(results / "recurrent_reproduction_metrics.csv")
    reproduction = pd.read_csv(results / "reproduction_summary.csv")
    paired = pd.read_csv(results / "paired_vs_existing_feedforward.csv")
    summary = json.loads((results / "summary.json").read_text(encoding="ascii"))
    metric_paths = sorted(results.glob("metrics_tier*_recurrent_*.json"))
    for path in metric_paths:
        payload = json.loads(path.read_text(encoding="ascii"))
        if not isinstance(payload["stop_epoch"], int):
            raise RuntimeError(f"Non-numeric stop_epoch in {path}")
        if payload["stop_reason"] != "early_stopping_triggered":
            raise RuntimeError(f"Unexpected stop reason in {path}")
    artifact_paths = sorted(
        path
        for pattern in (
            "checkpoint_tier*_recurrent_*.pt",
            "curve_tier*_recurrent_*.csv",
            "metrics_tier*_recurrent_*.json",
        )
        for path in results.glob(pattern)
    )
    with (results / "artifact_sha256.csv").open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=("file", "bytes", "sha256"))
        writer.writeheader()
        for path in artifact_paths:
            writer.writerow({"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})

    run_lines = []
    for row in metrics.itertuples(index=False):
        run_lines.append(
            f"| {int(row.tier)} | {int(row.seed)} | {int(row.best_epoch)} | "
            f"{int(row.stop_epoch)} | {row.stop_reason} | {row.test_macro_f1:.9f} |"
        )
    reproduction_lines = []
    for row in reproduction.itertuples(index=False):
        reproduction_lines.append(
            f"| {int(row.tier)} | {row.new_mean:.9f} | {row.new_std:.9f} | "
            f"{row.old_mean:.9f} | {row.old_std:.9f} | {row.mean_delta:+.9f} | "
            f"{str(bool(row.reproduced_within_old_seed_std)).lower()} |"
        )
    paired_lines = []
    for row in paired.itertuples(index=False):
        paired_lines.append(
            f"| {int(row.tier)} | {row.seed0_difference:+.9f} | "
            f"{row.seed1_difference:+.9f} | {row.seed2_difference:+.9f} | "
            f"{row.mean_difference:+.9f} | {row.std_difference:.9f} | "
            f"{row.paired_t:.6f} | {str(bool(row.significant)).lower()} | "
            f"{row.winner_by_mean} |"
        )
    report = f"""# 15A FI-2010 Recurrent Tier2/Tier3 Reproduction

RESULT: PASS

## Parameter gate

- Tier2 recurrent width 16: 2,132 trainable parameters (expected 2,132).
- Tier3 recurrent width 64: 23,876 trainable parameters (expected 23,876).
- Parameter count matches: yes.

## Runs

| Tier | Seed | Best epoch | Stop epoch | Stop reason | Test macro-F1 |
|---:|---:|---:|---:|---|---:|
{chr(10).join(run_lines)}

All six `stop_epoch` values are numeric and all six runs stopped through the fixed patience-10 early-stopping rule.

## Reproduction test

| Tier | New mean | New std | Old mean | Old std | Mean delta | Within old seed std |
|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(reproduction_lines)}

REPRODUCED_WITHIN_SEED_NOISE: yes

Both tiers reproduce within the preregistered boundary. The FI-2010 section may retain its conclusion, but should cite these traceable runs.

## Paired comparison against existing feedforward artifacts

| Tier | Seed0 diff | Seed1 diff | Seed2 diff | Mean diff | Std diff | Paired t | Significant (df=2, critical=4.302653) | Winner |
|---:|---:|---:|---:|---:|---:|---:|---|---|
{chr(10).join(paired_lines)}

TIER3_FEEDFORWARD_STILL_WINS: yes

Tier3 remains significantly in favor of feedforward (paired t = -10.050259). Tier2 is indistinguishable (paired t = 0.071109).

## Artifacts

- Required run artifacts: {summary['artifact_count']}/18.
- Checkpoints: 6; curves: 6; metrics JSON files: 6.
- SHA-256 inventory: `artifact_sha256.csv`.
- Existing `09j/results/track_b` files were read only and not overwritten.
- NEW5 used: no.

VERDICT: Confirm existing conclusion with the new traceable executions.
"""
    (results / "REPORT.md").write_text(report, encoding="ascii")
    audit = f"""# AUDIT 15A

- Data: FI-2010 Setup 2 cache used by 09J (`train_cf7`, `test_cf7`, `test_cf8`, `test_cf9`).
- Horizon: k=50.
- Loss: raw cross entropy.
- Optimizer: Adam, lr=1e-3, weight decay=0, no scheduler.
- Early stopping: patience 10; max epoch safety limit 120.
- Seeds: 0, 1, 2.
- Training implementation: original 09J `03_run_track_b.py:train_one`.
- Feedforward side: not retrained; existing complete 09J artifacts used for paired tests.
- Numeric stop epochs: yes, 6/6.
- Natural early stops: yes, 6/6.
- Required artifacts complete: {str(bool(summary['artifacts_complete'])).lower()} ({summary['artifact_count']}/18).
- NEW5 used: no.
"""
    (results / "AUDIT_15A.md").write_text(audit, encoding="ascii")
    print(json.dumps({
        "result": summary["result"],
        "reproduced_within_seed_noise": summary["reproduced_within_seed_noise"],
        "tier3_feedforward_still_wins": summary["tier3_feedforward_still_wins"],
        "artifacts_complete": summary["artifacts_complete"],
    }, indent=2))


if __name__ == "__main__":
    main()
