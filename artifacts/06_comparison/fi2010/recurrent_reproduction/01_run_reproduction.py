from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch


EXPECTED_PARAMS = {2: 2132, 3: 23876}
TIERS = ((2, 16), (3, 64))
SEEDS = (0, 1, 2)
OLD_MEAN = {2: 0.639748, 3: 0.638786}
OLD_STD = {2: 0.014473, 3: 0.005484}
CRITICAL_DF2 = 4.302653


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reproduce FI-2010 recurrent tier2/tier3")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--max-epochs", type=int, default=120)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--torch-threads", type=int, default=8)
    return parser.parse_args()


def load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("track_b_original", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_partial(output: Path, rows: list[dict[str, Any]]) -> None:
    pd.DataFrame(rows).sort_values(["tier", "seed"]).to_csv(
        output / "recurrent_reproduction_partial.csv", index=False
    )


def finalize(root: Path, output: Path, rows: list[dict[str, Any]]) -> None:
    frame = pd.DataFrame(rows).sort_values(["tier", "seed"])
    frame.to_csv(output / "recurrent_reproduction_metrics.csv", index=False)
    existing = pd.read_csv(
        root / "n2ew_era/09j_three_independent_tracks/results/track_b/track_b_run_metrics.csv"
    )
    paired_rows = []
    summary_rows = []
    reproduced = True
    for tier, group in frame.groupby("tier"):
        values = group.sort_values("seed")["test_macro_f1"].to_numpy(dtype=float)
        mean = float(values.mean())
        std = float(values.std(ddof=1))
        delta = mean - OLD_MEAN[int(tier)]
        within = abs(delta) < OLD_STD[int(tier)]
        reproduced = reproduced and within
        summary_rows.append({
            "tier": int(tier),
            "new_mean": mean,
            "new_std": std,
            "old_mean": OLD_MEAN[int(tier)],
            "old_std": OLD_STD[int(tier)],
            "mean_delta": delta,
            "reproduced_within_old_seed_std": within,
        })
        ff = existing[
            existing["tier"].eq(tier)
            & existing["architecture"].eq("feedforward")
        ].sort_values("seed")
        ff_values = ff["test_macro_f1"].to_numpy(dtype=float)
        if len(ff_values) != 3:
            raise RuntimeError(f"Expected three feedforward rows for tier {tier}")
        diff = values - ff_values
        diff_std = float(diff.std(ddof=1))
        t_value = float(diff.mean() / (diff_std / math.sqrt(3))) if diff_std > 0 else float("inf")
        paired_rows.append({
            "tier": int(tier),
            "seed0_difference": float(diff[0]),
            "seed1_difference": float(diff[1]),
            "seed2_difference": float(diff[2]),
            "mean_difference": float(diff.mean()),
            "std_difference": diff_std,
            "paired_t": t_value,
            "df": 2,
            "critical_df2": CRITICAL_DF2,
            "significant": abs(t_value) >= CRITICAL_DF2,
            "winner_by_mean": "recurrent" if diff.mean() > 0 else "feedforward",
        })
    pd.DataFrame(summary_rows).to_csv(output / "reproduction_summary.csv", index=False)
    pd.DataFrame(paired_rows).to_csv(output / "paired_vs_existing_feedforward.csv", index=False)
    tier3 = next(row for row in paired_rows if row["tier"] == 3)
    artifact_names = []
    for tier, width in TIERS:
        for seed in SEEDS:
            run_id = f"tier{tier}_recurrent_w{width}_seed{seed}"
            for prefix, suffix in (("checkpoint", ".pt"), ("curve", ".csv"), ("metrics", ".json")):
                artifact_names.append(f"{prefix}_{run_id}{suffix}")
    missing = [name for name in artifact_names if not (output / name).exists()]
    summary = {
        "result": "PASS" if not missing else "FAIL",
        "parameter_counts": EXPECTED_PARAMS,
        "reproduced_within_seed_noise": reproduced,
        "tier3_feedforward_still_wins": bool(
            tier3["winner_by_mean"] == "feedforward" and tier3["significant"]
        ),
        "artifacts_complete": not missing,
        "artifact_count": len(artifact_names) - len(missing),
        "missing_artifacts": missing,
        "new5_used": False,
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="ascii"
    )


def main() -> None:
    args = parse_args()
    if "new5" in str(vars(args)).lower():
        raise RuntimeError("NEW5 is forbidden")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="ascii", errors="replace")
    root = args.project_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(args.torch_threads)
    track = load_module(root / "n2ew_era/09j_three_independent_tracks/03_run_track_b.py")
    phase = root / "n2ew_era/08a_fi2010_public_benchmark"
    sys.path.insert(0, str(phase))
    from fi2010_phc_lite import PHCLiteFI2010Classifier
    from fi2010_tcn import TCNFI2010Classifier

    counts = {
        tier: sum(
            parameter.numel()
            for parameter in PHCLiteFI2010Classifier(hidden_dim=width).parameters()
            if parameter.requires_grad
        )
        for tier, width in TIERS
    }
    manifest = {
        "data": "FI-2010 Setup 2",
        "horizon_k": 50,
        "loss": "raw_cross_entropy",
        "optimizer": "Adam",
        "learning_rate": 0.001,
        "scheduler": "none",
        "patience": args.patience,
        "max_epochs": args.max_epochs,
        "batch_size": args.batch_size,
        "torch_threads": args.torch_threads,
        "seeds": list(SEEDS),
        "tiers": {str(tier): {"width": width, "parameters": counts[tier]} for tier, width in TIERS},
        "training_function": "09j_three_independent_tracks/03_run_track_b.py:train_one",
        "new5_used": False,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="ascii"
    )
    if counts != EXPECTED_PARAMS:
        raise RuntimeError(f"Parameter count mismatch: {counts} != {EXPECTED_PARAMS}")
    print(f"[15A] parameter_counts={counts}", flush=True)
    data = track.load_data(phase / "data/cache")
    rows: list[dict[str, Any]] = []
    for tier, width in TIERS:
        for seed in SEEDS:
            result = track.train_one(
                "recurrent",
                width,
                tier,
                seed,
                data,
                output,
                PHCLiteFI2010Classifier,
                TCNFI2010Classifier,
                args.batch_size,
                args.max_epochs,
                args.patience,
            )
            if not isinstance(result["stop_epoch"], int):
                raise RuntimeError(f"Non-numeric stop_epoch: {result}")
            rows.append(result)
            write_partial(output, rows)
            print(
                f"[15A] completed tier={tier} seed={seed} best={result['best_epoch']} "
                f"stop={result['stop_epoch']} test_macro_f1={result['test_macro_f1']:.6f}",
                flush=True,
            )
    finalize(root, output, rows)


if __name__ == "__main__":
    main()
