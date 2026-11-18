from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

MAX_EPOCHS = 500
PATIENCE = 20
LR = 1e-3
LR_MIN = 1e-5
WEIGHT_DECAY = 1e-4
GRAD_CLIP = 1.0
CHUNK_LENGTH = 2048
SEEDS = (0, 1, 2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="11B Stage 2 H20 toxicity training")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--stage1-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--feature-cache-dir", type=Path)
    parser.add_argument("--torch-threads", type=int, default=8)
    parser.add_argument("--max-epochs", type=int, default=MAX_EPOCHS)
    parser.add_argument("--patience", type=int, default=PATIENCE)
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class ContinuousToxicityModel(nn.Module):
    def __init__(self, base: nn.Module) -> None:
        super().__init__()
        self.encoder = base.encoder
        self.readout = base.readout
        self.diag_decay_param = base.diag_decay_param
        self.diag_gain_param = base.diag_gain_param

    def forward(self, x: torch.Tensor, state: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        decay = torch.sigmoid(self.diag_decay_param).view(1, -1)
        gain = torch.sigmoid(self.diag_gain_param).view(1, -1)
        b_prefix = gain * self.encoder(x)
        a_prefix = decay.expand(x.shape[0], -1)
        offset = 1
        while offset < x.shape[0]:
            previous_a = a_prefix
            previous_b = b_prefix
            a_prefix = torch.cat(
                [previous_a[:offset], previous_a[offset:] * previous_a[:-offset]], dim=0
            )
            b_prefix = torch.cat(
                [previous_b[:offset], previous_b[offset:] + previous_a[offset:] * previous_b[:-offset]],
                dim=0,
            )
            offset *= 2
        states = b_prefix + a_prefix * state
        return self.readout(states), states[-1:]


def set_seed(seed: int, threads: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(threads)


def load_split_sessions(
    split: str,
    root: Path,
    stage1: Path,
    cache_dir: Path,
    p05a: Any,
    p11s1: Any,
    p10a: Any,
    registry: pd.DataFrame,
) -> list[dict[str, Any]]:
    sessions: list[dict[str, Any]] = []
    scaler = p05a.load_scaler()
    for part in p05a.part_paths(split):
        session = part.stem.split("_")[1]
        cache_path = cache_dir / f"{split}_{session}_features.npz"
        if cache_path.exists():
            with np.load(cache_path) as cached:
                features = cached["features"].astype(np.float32)
        else:
            _, frame, _ = p11s1.load_market_and_frame(p10a, p05a, registry, part, split, 250_000)
            features, _ = p05a.normalized_features(frame, scaler)
            np.savez_compressed(cache_path, features=features.astype(np.float16))
        label_path = stage1 / "labels" / f"{split}_{session}_queue_labels.npz"
        with np.load(label_path) as payload:
            labels = np.column_stack([
                payload["pessimistic_bid_label"], payload["pessimistic_ask_label"],
            ]).astype(np.float32)
        if len(features) != len(labels):
            raise RuntimeError(f"Feature/label mismatch for {split}/{session}")
        sessions.append({"split": split, "session": session, "features": features, "labels": labels})
    return sessions


def evaluate_loss(model: nn.Module, sessions: list[dict[str, Any]], scale: float) -> float:
    total_squared = 0.0
    total_values = 0
    model.eval()
    with torch.no_grad():
        for session in sessions:
            features = session["features"]
            labels = session["labels"] / scale
            state = torch.zeros((1, 8), dtype=torch.float32)
            for start in range(0, len(features), CHUNK_LENGTH):
                end = min(start + CHUNK_LENGTH, len(features))
                x = torch.from_numpy(features[start:end]).float()
                target = torch.from_numpy(labels[start:end]).float()
                prediction, state = model(x, state)
                diff = prediction - target
                total_squared += float(torch.sum(diff * diff))
                total_values += int(diff.numel())
    return total_squared / total_values


def predict_sessions(model: nn.Module, sessions: list[dict[str, Any]], scale: float) -> dict[str, np.ndarray]:
    result: dict[str, np.ndarray] = {}
    model.eval()
    with torch.no_grad():
        for session in sessions:
            state = torch.zeros((1, 8), dtype=torch.float32)
            chunks: list[np.ndarray] = []
            features = session["features"]
            for start in range(0, len(features), CHUNK_LENGTH):
                prediction, state = model(
                    torch.from_numpy(features[start : start + CHUNK_LENGTH]).float(), state
                )
                chunks.append((prediction * scale).numpy().astype(np.float32))
            result[session["session"]] = np.concatenate(chunks)
    return result


def main() -> None:
    args = parse_args()
    if "new5" in str(vars(args)).lower():
        raise RuntimeError("NEW5 is forbidden")
    root = args.project_root.resolve()
    stage1 = args.stage1_dir.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "manifest.json").exists() or list(output.glob("training_curve_seed*.csv")):
        raise FileExistsError(f"Refusing to overwrite completed or partial training outputs: {output}")
    model_dir = output / "models"
    cache_dir = args.feature_cache_dir.resolve() if args.feature_cache_dir else output / "feature_cache"
    score_dir = output / "val_scores"
    for path in (model_dir, cache_dir, score_dir):
        path.mkdir(parents=True, exist_ok=True)

    phase05a = root / "n2ew_era/05a_phc_lite_microstructure_sequence_feasibility"
    phase07s = root / "n2ew_era/07s_diagonal_hidden8"
    for path in (phase05a, phase07s):
        sys.path.insert(0, str(path))
    import common_05a as p05a
    from models.phc_diagonal_hidden8 import PHCDiagonalSSMHidden8, count_parameters
    p11s1 = load_module("p11b_stage1", root / "n2ew_era/11b_toxicity_objective_retrain_v2/01_generate_queue_labels.py")
    p10a_path = root / "n2ew_era/10a_two_sided_market_making_pilot/01_run_pilot.py"
    p10a = load_module("p11a_p10a_train", p10a_path)
    registry_path = root / "n2ew_era/04a1_dataset_registry_patch/results/dataset_registry_expanded.csv"
    stage1_manifest = stage1 / "manifest.json"
    protected = [registry_path, p10a_path, stage1_manifest]
    before = {str(path.relative_to(root)): sha256(path) for path in protected}
    registry = pd.read_csv(registry_path)
    registry = registry[~registry.physical_path.astype(str).str.contains("NEW5", case=False)].copy()

    train_sessions = load_split_sessions("train", root, stage1, cache_dir, p05a, p11s1, p10a, registry)
    val_sessions = load_split_sessions("val", root, stage1, cache_dir, p05a, p11s1, p10a, registry)
    all_train_labels = np.concatenate([session["labels"].reshape(-1) for session in train_sessions])
    target_scale = float(np.std(all_train_labels))
    if not math.isfinite(target_scale) or target_scale <= 0:
        raise RuntimeError("Invalid target scale")

    convergence_rows: list[dict[str, Any]] = []
    run_manifests: list[dict[str, Any]] = []
    started_all = time.perf_counter()
    for seed in SEEDS:
        set_seed(seed, args.torch_threads)
        base = PHCDiagonalSSMHidden8(16, 8, 1, 0.0)
        if count_parameters(base) != 186:
            raise RuntimeError("Parameter-count drift")
        model = ContinuousToxicityModel(base)
        optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=args.max_epochs, eta_min=LR_MIN
        )
        best_loss = float("inf")
        best_epoch = -1
        wait = 0
        seed_started = time.perf_counter()
        curve: list[dict[str, Any]] = []
        stop_reason = "max_epoch_hit"
        for epoch in range(1, args.max_epochs + 1):
            epoch_started = time.perf_counter()
            model.train()
            squared = 0.0
            values = 0
            for session in train_sessions:
                state = torch.zeros((1, 8), dtype=torch.float32)
                features = session["features"]
                labels = session["labels"] / target_scale
                for start in range(0, len(features), CHUNK_LENGTH):
                    end = min(start + CHUNK_LENGTH, len(features))
                    x = torch.from_numpy(features[start:end]).float()
                    target = torch.from_numpy(labels[start:end]).float()
                    optimizer.zero_grad(set_to_none=True)
                    prediction, next_state = model(x, state)
                    loss = torch.mean((prediction - target) ** 2)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
                    optimizer.step()
                    state = next_state.detach()
                    squared += float(loss.detach()) * target.numel()
                    values += target.numel()
            val_loss = evaluate_loss(model, val_sessions, target_scale)
            train_loss = squared / values
            improved = val_loss < best_loss - 1e-8
            if improved:
                best_loss = val_loss
                best_epoch = epoch
                wait = 0
                checkpoint = {
                    "model_state_dict": model.state_dict(), "seed": seed, "epoch": epoch,
                    "best_epoch": best_epoch, "best_val_mse_normalized": best_loss,
                    "target_scale": target_scale, "feature_dim": 16, "raw_feature_count": 13,
                    "hidden_dim": 8, "parameter_count": 186, "output_dim": 2,
                    "loss": "MSE_on_std_scaled_unconditional_side_pnl",
                    "training_protocol": "continuous_stateful_TBPTT_chunk2048_no_event_sampling",
                    "max_epochs": args.max_epochs, "patience": args.patience,
                    "scheduler_t_max": args.max_epochs, "new5_loaded": False,
                }
                torch.save(checkpoint, model_dir / f"toxicity_hidden8_seed{seed}_best.pt")
            else:
                wait += 1
            scheduler.step()
            if wait >= args.patience:
                stop_reason = "early_stopping_triggered"
            row = {
                "seed": seed, "epoch": epoch, "train_mse_normalized": train_loss,
                "val_mse_normalized": val_loss, "best_val_mse": best_loss,
                "best_epoch": best_epoch, "early_stop_counter": wait,
                "lr": float(scheduler.get_last_lr()[0]),
                "epoch_walltime_s": time.perf_counter() - epoch_started,
                "cumulative_walltime_s": time.perf_counter() - seed_started,
                "stop_reason": stop_reason if wait >= args.patience or epoch == args.max_epochs else "running",
            }
            curve.append(row)
            convergence_rows.append(row)
            write_csv(output / f"training_curve_seed{seed}.csv", curve)
            print(
                f"[TRAIN] seed={seed} epoch={epoch} train={train_loss:.8f} val={val_loss:.8f} "
                f"best={best_loss:.8f}@{best_epoch} wait={wait}/{args.patience} seconds={row['epoch_walltime_s']:.1f}",
                flush=True,
            )
            if wait >= args.patience:
                break

        checkpoint_path = model_dir / f"toxicity_hidden8_seed{seed}_best.pt"
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        best_base = PHCDiagonalSSMHidden8(16, 8, 1, 0.0)
        best_model = ContinuousToxicityModel(best_base)
        best_model.load_state_dict(checkpoint["model_state_dict"])
        val_scores = predict_sessions(best_model, val_sessions, target_scale)
        for session, scores in val_scores.items():
            np.savez_compressed(score_dir / f"seed{seed}_val_{session}_scores.npz", scores=scores)
        manifest = {
            "result": "PASS", "seed": seed, "parameter_count": 186,
            "architecture_unchanged": True, "actual_stop_epoch": int(curve[-1]["epoch"]),
            "best_epoch": int(best_epoch), "stop_reason": curve[-1]["stop_reason"],
            "best_val_mse_normalized": best_loss, "target_scale": target_scale,
            "checkpoint": str(checkpoint_path.relative_to(root)).replace("\\", "/"),
            "checkpoint_sha256": sha256(checkpoint_path),
            "training_event_count": int(sum(len(x["features"]) for x in train_sessions)),
            "val_event_count": int(sum(len(x["features"]) for x in val_sessions)),
            "continuous_no_stride_sampling": True, "new5_loaded": False,
            "walltime_s": time.perf_counter() - seed_started,
        }
        (output / f"run_manifest_seed{seed}.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
        run_manifests.append(manifest)

    after = {str(path.relative_to(root)): sha256(path) for path in protected}
    hashes = [{"path": key, "before_sha256": before[key], "after_sha256": after[key], "unchanged": before[key] == after[key]} for key in before]
    write_csv(output / "protected_hashes.csv", hashes)
    if not all(row["unchanged"] for row in hashes):
        raise RuntimeError("Protected artifact changed")
    report = output / "AUDIT_STAGE2_TRAINING.md"
    summary = pd.DataFrame(run_manifests)[[
        "seed", "parameter_count", "actual_stop_epoch", "best_epoch", "stop_reason",
        "best_val_mse_normalized", "walltime_s",
    ]]
    lines = [
        "# 11B Stage 2 H20 Toxicity Training", "", "status: complete", "",
        "ARCHITECTURE_UNCHANGED: `yes` (186 trainable parameters; 16 deployed PHC inputs derived from the unchanged 13 TARGET_RAW_COLUMNS; hidden dimension 8; two outputs).", "",
        "Loss: normalized MSE on unconditional per-side maker P&L. MSE is used because its conditional optimum is the expected value required by the decision rule. Huber and class weighting were rejected because they would change the estimand or bias genuine zero outcomes.", "",
        "Training processes every event in order with continuous recurrent state. The diagonal affine recurrence is evaluated by a mathematically equivalent associative prefix scan inside each 2,048-event TBPTT chunk; numerical state is carried across chunk boundaries while gradients are detached. No stride-32 or other event sampling is used.", "",
        summary.to_markdown(index=False), "",
        "Thresholds and OOS data were not accessed during training. NEW5 was not loaded.", "",
    ]
    report.write_text("\n".join(lines), encoding="ascii")
    manifest = {
        "result": "PASS", "stage": "11B_stage2", "architecture_unchanged": True,
        "parameter_count": 186, "loss_function": "normalized_MSE",
        "continuous_no_stride_sampling": True, "runs": run_manifests,
        "new5_used": False, "protected_artifacts_unchanged": True,
        "runtime_seconds": time.perf_counter() - started_all,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"[DONE] report={report}", flush=True)


if __name__ == "__main__":
    main()
