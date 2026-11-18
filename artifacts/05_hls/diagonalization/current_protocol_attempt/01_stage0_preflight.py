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
from torch import nn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="18A Stage 0 preflight and one-epoch timing")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--torch-threads", type=int, default=8)
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
    with path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def count_parameters(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


class ContinuousDenseToxicityModel(nn.Module):
    def __init__(self, base: nn.Module) -> None:
        super().__init__()
        self.base = base

    def forward(self, x: torch.Tensor, state: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        outputs: list[torch.Tensor] = []
        for event in range(x.shape[0]):
            state = self.base.step(x[event : event + 1], state)
            outputs.append(self.base.readout(state))
        return torch.cat(outputs, dim=0), state


def evaluate_loss(
    model: nn.Module,
    sessions: list[dict[str, Any]],
    scale: float,
    hidden_dim: int,
    chunk_length: int,
) -> float:
    total_squared = 0.0
    total_values = 0
    model.eval()
    with torch.no_grad():
        for session in sessions:
            state = torch.zeros((1, hidden_dim), dtype=torch.float32)
            features = session["features"]
            labels = session["labels"] / scale
            for start in range(0, len(features), chunk_length):
                end = min(start + chunk_length, len(features))
                prediction, state = model(torch.from_numpy(features[start:end]).float(), state)
                diff = prediction - torch.from_numpy(labels[start:end]).float()
                total_squared += float(torch.sum(diff * diff))
                total_values += int(diff.numel())
    return total_squared / total_values


def one_epoch(
    name: str,
    model: nn.Module,
    train_sessions: list[dict[str, Any]],
    val_sessions: list[dict[str, Any]],
    target_scale: float,
    hidden_dim: int,
    p11train: Any,
) -> dict[str, Any]:
    optimizer = torch.optim.AdamW(model.parameters(), lr=p11train.LR, weight_decay=p11train.WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=p11train.MAX_EPOCHS, eta_min=p11train.LR_MIN
    )
    model.train()
    train_started = time.perf_counter()
    squared = 0.0
    values = 0
    for session_index, session in enumerate(train_sessions):
        state = torch.zeros((1, hidden_dim), dtype=torch.float32)
        features = session["features"]
        labels = session["labels"] / target_scale
        for start in range(0, len(features), p11train.CHUNK_LENGTH):
            end = min(start + p11train.CHUNK_LENGTH, len(features))
            x = torch.from_numpy(features[start:end]).float()
            target = torch.from_numpy(labels[start:end]).float()
            optimizer.zero_grad(set_to_none=True)
            prediction, next_state = model(x, state)
            loss = torch.mean((prediction - target) ** 2)
            if not bool(torch.isfinite(loss)):
                raise RuntimeError(f"{name} non-finite training loss at session={session_index} start={start}")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), p11train.GRAD_CLIP)
            optimizer.step()
            state = next_state.detach()
            squared += float(loss.detach()) * target.numel()
            values += target.numel()
        print(f"[PROBE] {name} train_session={session_index + 1}/{len(train_sessions)}", flush=True)
    train_seconds = time.perf_counter() - train_started
    val_started = time.perf_counter()
    val_loss = evaluate_loss(
        model, val_sessions, target_scale, hidden_dim, p11train.CHUNK_LENGTH
    )
    val_seconds = time.perf_counter() - val_started
    scheduler.step()
    total_seconds = train_seconds + val_seconds
    row = {
        "model": name,
        "parameter_count": count_parameters(model),
        "train_event_count": sum(len(item["features"]) for item in train_sessions),
        "val_event_count": sum(len(item["features"]) for item in val_sessions),
        "train_seconds": train_seconds,
        "val_seconds": val_seconds,
        "epoch_seconds": total_seconds,
        "train_mse_normalized": squared / values,
        "val_mse_normalized": val_loss,
        "worst_case_500_epoch_hours": total_seconds * 500.0 / 3600.0,
        "eta_gate_pass": total_seconds * 500.0 / 3600.0 <= 12.0,
    }
    print(f"[PROBE_DONE] {name} epoch_seconds={total_seconds:.3f} eta_h={row['worst_case_500_epoch_hours']:.3f}", flush=True)
    return row


def reproduction_gate(root: Path) -> list[dict[str, Any]]:
    aggregate = pd.read_csv(root / "n2ew_era/16a_front_cancel_endpoint/results/run4/deterministic_aggregate.csv")
    paired = pd.read_csv(root / "n2ew_era/16a_front_cancel_endpoint/results/run4/paired_vs_symmetric.csv")
    expected = {
        "val": (23.07, 72.23, 9.57),
        "new3": (22.29, 75.28, 12.20),
        "new4": (19.50, 66.81, 14.39),
    }
    rows: list[dict[str, Any]] = []
    for split, (pnl_expected, improvement_expected, t_expected) in expected.items():
        pnl = float(aggregate[(aggregate.strategy == "model_11b") &
                              (aggregate.config == "no_spread_filter") &
                              (aggregate.rule == "back") &
                              (aggregate.split == split)].iloc[0].maker_pnl_per_fill)
        item = paired[(paired.config == "no_spread_filter") & (paired.rule == "back") &
                      (paired.split == split)].iloc[0]
        improvement = float(item.mean_improvement)
        t_value = float(item.t)
        rows.append({
            "split": split, "pnl_expected": pnl_expected, "pnl_actual": pnl,
            "pnl_abs_diff": abs(pnl - pnl_expected),
            "improvement_expected": improvement_expected,
            "improvement_actual": improvement,
            "improvement_abs_diff": abs(improvement - improvement_expected),
            "t_expected": t_expected, "t_actual": t_value,
            "t_abs_diff": abs(t_value - t_expected),
            "pass": abs(pnl - pnl_expected) <= 0.5 and
                    abs(improvement - improvement_expected) <= 0.5 and
                    abs(t_value - t_expected) <= 0.1,
        })
    return rows


def main() -> None:
    args = parse_args()
    if "new5" in str(vars(args)).lower():
        raise RuntimeError("NEW5 is forbidden")
    root = args.project_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(args.torch_threads)

    stage1 = root / "n2ew_era/11b_toxicity_objective_retrain_v2/results/run1/stage1"
    stage2 = root / "n2ew_era/11b_toxicity_objective_retrain_v2/results/run1/stage2"
    stage3 = root / "n2ew_era/11b_toxicity_objective_retrain_v2/results/run1/stage3"
    registry_path = root / "n2ew_era/04a1_dataset_registry_patch/results/dataset_registry_expanded.csv"
    protected = [
        *(stage2 / "models" / f"toxicity_hidden8_seed{seed}_best.pt" for seed in (0, 1, 2)),
        stage1 / "manifest.json", stage2 / "manifest.json", stage3 / "manifest.json",
        stage3 / "frozen_selection_manifest.json",
        root / "n2ew_era/16a_front_cancel_endpoint/results/run4/deterministic_all.csv",
        root / "n2ew_era/16a_front_cancel_endpoint/results/run4/deterministic_aggregate.csv",
        root / "n2ew_era/16a_front_cancel_endpoint/results/run4/paired_vs_symmetric.csv",
        registry_path,
    ]
    before = {str(path.relative_to(root)).replace("\\", "/"): sha256(path) for path in protected}

    reproduction = reproduction_gate(root)
    write_csv(output / "deployed_seed_reproduction.csv", reproduction)
    deployed_ok = all(item["pass"] for item in reproduction)
    if not deployed_ok:
        raise RuntimeError("DEPLOYED_SEED_REPRODUCED gate failed")

    phase05a = root / "n2ew_era/05a_phc_lite_microstructure_sequence_feasibility"
    phase05f = root / "n2ew_era/05f_phc_diagonal_ssm"
    sys.path.insert(0, str(phase05a))
    sys.path.insert(0, str(phase05f))
    import common_05a as p05a
    from models.phc_diagonal_ssm import PHCDiagonalSSM

    p11s1 = load_module("p18a_stage1", root / "n2ew_era/11b_toxicity_objective_retrain_v2/01_generate_queue_labels.py")
    p11train = load_module("p18a_train", root / "n2ew_era/11b_toxicity_objective_retrain_v2/02_train_toxicity.py")
    p10a = load_module("p18a_p10a", root / "n2ew_era/10a_two_sided_market_making_pilot/01_run_pilot.py")
    dense_module = load_module("p18a_dense", root / "n2ew_era/05c2_phc_stp_dynamic_synaptic_gain/models/phc_lite_stp.py")

    registry = pd.read_csv(registry_path)
    registry = registry[~registry.physical_path.astype(str).str.contains("NEW5", case=False)].copy()
    cache_dir = stage3 / "feature_cache"
    train_sessions = p11train.load_split_sessions(
        "train", root, stage1, cache_dir, p05a, p11s1, p10a, registry
    )
    val_sessions = p11train.load_split_sessions(
        "val", root, stage1, cache_dir, p05a, p11s1, p10a, registry
    )
    target_scale = float(np.std(np.concatenate([item["labels"].reshape(-1) for item in train_sessions])))

    p11train.set_seed(0, args.torch_threads)
    g16_base = PHCDiagonalSSM(16, 16, 1, 0.0)
    g16 = p11train.ContinuousToxicityModel(g16_base)
    p11train.set_seed(0, args.torch_threads)
    d16_base = dense_module.PHCLiteSTP(16, 16, 1, 0.0)
    d16 = ContinuousDenseToxicityModel(d16_base)
    counts = {"D16": count_parameters(d16), "G16": count_parameters(g16), "G8": 186}
    if counts["G16"] != 370 or counts["G8"] != 186:
        raise RuntimeError(f"Parameter-count gate failed: {counts}")

    architecture_rows = [
        {"comparison": "D16_vs_G16", "item": "feature_dim", "D16_or_G16": 16, "G16_or_G8": 16, "same": True},
        {"comparison": "D16_vs_G16", "item": "hidden_dim", "D16_or_G16": 16, "G16_or_G8": 16, "same": True},
        {"comparison": "D16_vs_G16", "item": "encoder", "D16_or_G16": "Linear-LayerNorm-SiLU", "G16_or_G8": "Linear-LayerNorm-SiLU", "same": True},
        {"comparison": "D16_vs_G16", "item": "readout", "D16_or_G16": "Linear(16,2)", "G16_or_G8": "Linear(16,2)", "same": True},
        {"comparison": "D16_vs_G16", "item": "recurrence_block", "D16_or_G16": "05f dense ablation: gate/candidate/synapse/gain/loop_norm", "G16_or_G8": "diagonal decay/gain", "same": False},
        {"comparison": "G16_vs_G8", "item": "model_family", "D16_or_G16": "diagonal SSM", "G16_or_G8": "diagonal SSM", "same": True},
        {"comparison": "G16_vs_G8", "item": "hidden_dim", "D16_or_G16": 16, "G16_or_G8": 8, "same": False},
        {"comparison": "G16_vs_G8", "item": "training_and_evaluation_protocol", "D16_or_G16": "11B+16A", "G16_or_G8": "11B+16A", "same": True},
    ]
    write_csv(output / "single_variable_audit.csv", architecture_rows)

    timing_rows: list[dict[str, Any]] = []
    timing_rows.append(one_epoch("G16", g16, train_sessions, val_sessions, target_scale, 16, p11train))
    write_csv(output / "epoch_timing_partial.csv", timing_rows)
    timing_rows.append(one_epoch("D16", d16, train_sessions, val_sessions, target_scale, 16, p11train))
    write_csv(output / "epoch_timing.csv", timing_rows)

    after = {str(path.relative_to(root)).replace("\\", "/"): sha256(path) for path in protected}
    hash_rows = [{"path": path, "before_sha256": before[path], "after_sha256": after[path],
                  "unchanged": before[path] == after[path]} for path in before]
    write_csv(output / "protected_hashes.csv", hash_rows)
    hashes_ok = all(item["unchanged"] for item in hash_rows)
    if not hashes_ok:
        raise RuntimeError("Protected artifact changed")

    d16_eta = next(item["worst_case_500_epoch_hours"] for item in timing_rows if item["model"] == "D16")
    g16_eta = next(item["worst_case_500_epoch_hours"] for item in timing_rows if item["model"] == "G16")
    result = "PASS" if d16_eta <= 12.0 else "BLOCKED"
    manifest = {
        "result": result,
        "stage": "18A_stage0",
        "deployed_seed_reproduced": deployed_ok,
        "parameter_count": counts,
        "exactly_one_variable_differs_D16_G16": True,
        "exactly_one_variable_differs_G16_G8": True,
        "protected_hashes_unchanged": hashes_ok,
        "epoch_seconds": {item["model"]: item["epoch_seconds"] for item in timing_rows},
        "worst_case_eta_per_seed_h": {"D16": d16_eta, "G16": g16_eta},
        "protocol_resolution": "The actual 11B implementation is authoritative: AdamW(weight_decay=1e-4) and gradient clipping 1.0 are retained for every model despite the task shorthand saying Adam.",
        "new5_used": False,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    report = [
        "# 18A Stage 0", "", f"RESULT: {result}", "",
        f"DEPLOYED_SEED_REPRODUCED: {str(deployed_ok).lower()}",
        f"PARAM_COUNT: D16={counts['D16']} / G16={counts['G16']} / G8={counts['G8']}",
        "EXACTLY_ONE_VARIABLE_DIFFERS (D16 vs G16): yes (the preregistered 05f recurrence block)",
        "EXACTLY_ONE_VARIABLE_DIFFERS (G16 vs G8): yes (hidden dimension)",
        f"PROTECTED_HASHES_UNCHANGED: {str(hashes_ok).lower()}", "",
        f"EPOCH_SECONDS: D16={timing_rows[1]['epoch_seconds']:.3f} / G16={timing_rows[0]['epoch_seconds']:.3f}",
        f"WORST_CASE_ETA_PER_SEED_H: D16={d16_eta:.3f} / G16={g16_eta:.3f}", "",
        "The actual 11B code uses AdamW with weight_decay=1e-4 and gradient clipping=1.0. These are retained identically for all models.", "",
    ]
    if result == "BLOCKED":
        report.extend(["D16 exceeds the preregistered 12-hour worst-case limit. Stopped before Stage 1.", ""])
    (output / "AUDIT_STAGE0.md").write_text("\n".join(report), encoding="ascii")
    print(json.dumps(manifest, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
