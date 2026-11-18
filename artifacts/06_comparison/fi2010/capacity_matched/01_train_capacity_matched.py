from __future__ import annotations

import argparse
import csv
import ctypes
import json
import math
import os
import random
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from torch import nn


WINDOW = 100
TRAIN_FRACTION = 0.8
HORIZONS = [10, 20, 30, 50, 100]
HORIZON = 50
HIDDEN_DIM = 4
NUM_CLASSES = 3
SEEDS = [0, 1, 2]

PROTOCOL = {
    "protocol_status": "preregistered_before_training",
    "dataset": "FI-2010 NoAuction Zscore Setup 2 cache from 08A",
    "window": WINDOW,
    "train_fraction_head": TRAIN_FRACTION,
    "validation_fraction_tail": 1.0 - TRAIN_FRACTION,
    "test_source": "CF7+CF8+CF9; selection-after-only diagnostics",
    "horizon_k": HORIZON,
    "seeds": SEEDS,
    "hidden_dim_both_sides": HIDDEN_DIM,
    "loss": "raw_cross_entropy",
    "optimizer": "AdamW",
    "learning_rate": 1e-3,
    "weight_decay": 1e-4,
    "lr_scheduler": "CosineAnnealingLR",
    "lr_t_max": 200,
    "lr_eta_min": 1e-5,
    "max_epochs": 200,
    "patience": 10,
    "min_delta": 1e-5,
    "batch_size": 512,
    "eval_batch_size": 1024,
    "grad_clip_norm": 1.0,
    "selection_metric": "validation_macro_f1",
    "primary_diagnostic": "test_macro_f1_after_selection",
    "secondary_diagnostic": "test_weighted_f1_after_selection",
    "verdict_scale": "sample_std_of_seed_paired_test_macro_f1_differences",
    "verdict_rule": "recurrent win if mean paired delta > +1 std; feedforward win if < -1 std; otherwise tie",
    "new5_used": False,
}


class MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class DiagonalRecurrentFI2010(nn.Module):
    """FI-2010 adaptation of 07S: Linear+LN+SiLU then diagonal state update."""

    def __init__(self, feature_dim: int = 40, hidden_dim: int = HIDDEN_DIM) -> None:
        super().__init__()
        self.feature_dim = int(feature_dim)
        self.hidden_dim = int(hidden_dim)
        self.encoder = nn.Sequential(
            nn.Linear(self.feature_dim, self.hidden_dim),
            nn.LayerNorm(self.hidden_dim),
            nn.SiLU(),
        )
        self.diag_decay_param = nn.Parameter(
            torch.logit(torch.full((self.hidden_dim,), 0.90, dtype=torch.float32))
        )
        self.diag_gain_param = nn.Parameter(
            torch.logit(torch.full((self.hidden_dim,), 0.50, dtype=torch.float32))
        )
        self.readout = nn.Linear(self.hidden_dim, NUM_CLASSES)

    def forward_step(self, x_t: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
        encoded = self.encoder(x_t)
        decay = torch.sigmoid(self.diag_decay_param).view(1, -1)
        gain = torch.sigmoid(self.diag_gain_param).view(1, -1)
        return decay * state + gain * encoded

    def forward_reference(self, x_window: torch.Tensor) -> torch.Tensor:
        state = x_window.new_zeros((x_window.shape[0], self.hidden_dim))
        for timestep in range(x_window.shape[1]):
            state = self.forward_step(x_window[:, timestep, :], state)
        return self.readout(state)

    def forward(self, x_window: torch.Tensor) -> torch.Tensor:
        encoded = self.encoder(x_window)
        decay = torch.sigmoid(self.diag_decay_param)
        gain = torch.sigmoid(self.diag_gain_param)
        exponents = torch.arange(
            x_window.shape[1] - 1,
            -1,
            -1,
            device=x_window.device,
            dtype=x_window.dtype,
        ).view(1, -1, 1)
        weights = torch.pow(decay.view(1, 1, -1), exponents)
        state = torch.sum(encoded * gain.view(1, 1, -1) * weights, dim=1)
        return self.readout(state)


class FeedForwardFI2010(nn.Module):
    """Capacity-matched single-hidden-layer MLP with no temporal state."""

    def __init__(self, feature_dim: int = 40, hidden_dim: int = HIDDEN_DIM) -> None:
        super().__init__()
        self.feature_dim = int(feature_dim)
        self.hidden_dim = int(hidden_dim)
        self.hidden = nn.Linear(self.feature_dim, self.hidden_dim)
        self.activation = nn.SiLU()
        self.readout = nn.Linear(self.hidden_dim, NUM_CLASSES)

    def forward(self, x_window: torch.Tensor) -> torch.Tensor:
        return self.readout(self.activation(self.hidden(x_window[:, -1, :])))


def assert_no_new5(path: Path) -> None:
    if "new5" in str(path).lower():
        raise RuntimeError(f"NEW5 path is forbidden: {path}")


def count_parameters(model: nn.Module) -> int:
    return int(sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad))


def parameter_shapes(model: nn.Module) -> list[dict[str, object]]:
    return [
        {"name": name, "shape": list(parameter.shape), "parameters": int(parameter.numel())}
        for name, parameter in model.named_parameters()
    ]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def preflight() -> dict[str, object]:
    memory = MemoryStatusEx()
    memory.dwLength = ctypes.sizeof(MemoryStatusEx)
    memory_ok = bool(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)))
    return {
        "timestamp_unix": time.time(),
        "python": os.path.realpath(os.sys.executable),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cpu_logical": os.cpu_count(),
        "torch_threads": torch.get_num_threads(),
        "memory_query_ok": memory_ok,
        "memory_total_gb": memory.ullTotalPhys / 2**30 if memory_ok else None,
        "memory_available_gb": memory.ullAvailPhys / 2**30 if memory_ok else None,
        "new5_used": False,
    }


def load_data(cache: Path) -> dict[str, np.ndarray]:
    assert_no_new5(cache)
    with np.load(cache / "train_cf7.npz") as archive:
        train_features = archive["features"].astype(np.float32, copy=False)
        train_labels = archive["labels"].astype(np.int64, copy=False) - 1
    test_features_parts: list[np.ndarray] = []
    test_label_parts: list[np.ndarray] = []
    for name in ("test_cf7", "test_cf8", "test_cf9"):
        with np.load(cache / f"{name}.npz") as archive:
            test_features_parts.append(archive["features"].astype(np.float32, copy=False))
            test_label_parts.append(archive["labels"].astype(np.int64, copy=False) - 1)
    cut = int(math.floor(train_features.shape[0] * TRAIN_FRACTION))
    return {
        "train_features": train_features[:cut],
        "train_labels": train_labels[:cut],
        "val_features": train_features[cut:],
        "val_labels": train_labels[cut:],
        "test_features": np.concatenate(test_features_parts, axis=0),
        "test_labels": np.concatenate(test_label_parts, axis=0),
    }


def batch_windows(features: np.ndarray, starts: np.ndarray, device: torch.device) -> torch.Tensor:
    indexes = starts[:, None] + np.arange(WINDOW, dtype=np.int64)[None, :]
    array = np.ascontiguousarray(features[indexes])
    return torch.from_numpy(array).to(device=device, dtype=torch.float32)


def batch_labels(labels: np.ndarray, starts: np.ndarray, device: torch.device) -> torch.Tensor:
    horizon_idx = HORIZONS.index(HORIZON)
    array = np.ascontiguousarray(labels[starts + WINDOW - 1, horizon_idx])
    return torch.from_numpy(array).to(device=device, dtype=torch.long)


def metrics_from_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    _, _, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=[0, 1, 2], average="macro", zero_division=0
    )
    _, _, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=[0, 1, 2], average="weighted", zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
    }


@torch.no_grad()
def evaluate(
    model: nn.Module,
    features: np.ndarray,
    labels: np.ndarray,
    batch_size: int,
    device: torch.device,
) -> dict[str, float]:
    model.eval()
    starts_all = np.arange(features.shape[0] - WINDOW + 1, dtype=np.int64)
    true_parts: list[np.ndarray] = []
    pred_parts: list[np.ndarray] = []
    total_loss = 0.0
    total_rows = 0
    loss_fn = nn.CrossEntropyLoss(reduction="sum")
    for position in range(0, len(starts_all), batch_size):
        starts = starts_all[position : position + batch_size]
        x = batch_windows(features, starts, device)
        y = batch_labels(labels, starts, device)
        logits = model(x)
        total_loss += float(loss_fn(logits, y).cpu())
        total_rows += int(y.numel())
        true_parts.append(y.cpu().numpy())
        pred_parts.append(torch.argmax(logits, dim=1).cpu().numpy())
    result = metrics_from_predictions(np.concatenate(true_parts), np.concatenate(pred_parts))
    result["loss"] = total_loss / max(total_rows, 1)
    return result


def make_model(kind: str) -> nn.Module:
    if kind == "recurrent":
        return DiagonalRecurrentFI2010()
    if kind == "feedforward":
        return FeedForwardFI2010()
    raise ValueError(kind)


def verify_recurrent_vectorization(device: torch.device) -> float:
    set_seed(9187)
    model = DiagonalRecurrentFI2010().to(device).eval()
    sample = torch.randn(7, WINDOW, 40, device=device)
    with torch.no_grad():
        reference = model.forward_reference(sample)
        vectorized = model(sample)
    return float(torch.max(torch.abs(reference - vectorized)).cpu())


def save_last(
    path: Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    state: dict[str, object],
) -> None:
    torch.save(
        {
            **state,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
        },
        path,
    )


def train_one(
    kind: str,
    seed: int,
    data: dict[str, np.ndarray],
    output_dir: Path,
    model_dir: Path,
    device: torch.device,
    resume: bool,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    set_seed(seed)
    model = make_model(kind).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=PROTOCOL["learning_rate"], weight_decay=PROTOCOL["weight_decay"]
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=PROTOCOL["lr_t_max"], eta_min=PROTOCOL["lr_eta_min"]
    )
    loss_fn = nn.CrossEntropyLoss()
    best_path = model_dir / f"{kind}_seed{seed}_best.pt"
    last_path = model_dir / f"{kind}_seed{seed}_last.pt"
    curve_path = output_dir / f"training_curve_{kind}_seed{seed}.csv"
    curves: list[dict[str, object]] = [dict(row) for row in load_csv(curve_path)]
    start_epoch = 1
    best_epoch = 0
    best_val_f1 = -1.0
    patience_left = int(PROTOCOL["patience"])
    elapsed_before = 0.0
    if resume and last_path.exists():
        payload = torch.load(last_path, map_location=device, weights_only=False)
        model.load_state_dict(payload["model_state_dict"])
        optimizer.load_state_dict(payload["optimizer_state_dict"])
        scheduler.load_state_dict(payload["scheduler_state_dict"])
        start_epoch = int(payload["epoch"]) + 1
        best_epoch = int(payload["best_epoch"])
        best_val_f1 = float(payload["best_val_f1"])
        patience_left = int(payload["patience_left"])
        elapsed_before = float(payload["elapsed_seconds"])

    starts_all = np.arange(data["train_features"].shape[0] - WINDOW + 1, dtype=np.int64)
    run_start = time.time()
    stop_reason = "max_epochs"
    stop_epoch = int(PROTOCOL["max_epochs"])
    for epoch in range(start_epoch, int(PROTOCOL["max_epochs"]) + 1):
        epoch_start = time.time()
        model.train()
        np.random.shuffle(starts_all)
        train_loss_sum = 0.0
        train_rows = 0
        for position in range(0, len(starts_all), int(PROTOCOL["batch_size"])):
            starts = starts_all[position : position + int(PROTOCOL["batch_size"])]
            x = batch_windows(data["train_features"], starts, device)
            y = batch_labels(data["train_labels"], starts, device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(x)
            loss = loss_fn(logits, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), float(PROTOCOL["grad_clip_norm"]))
            optimizer.step()
            train_loss_sum += float(loss.detach().cpu()) * int(y.numel())
            train_rows += int(y.numel())
        scheduler.step()
        val = evaluate(
            model,
            data["val_features"],
            data["val_labels"],
            int(PROTOCOL["eval_batch_size"]),
            device,
        )
        elapsed = elapsed_before + time.time() - run_start
        row = {
            "model_kind": kind,
            "seed": seed,
            "epoch": epoch,
            "train_loss": train_loss_sum / max(train_rows, 1),
            "val_loss": val["loss"],
            "val_macro_f1": val["macro_f1"],
            "val_weighted_f1": val["weighted_f1"],
            "current_lr": scheduler.get_last_lr()[0],
            "epoch_seconds": time.time() - epoch_start,
            "elapsed_seconds": elapsed,
        }
        curves.append(row)
        write_csv(curve_path, curves)
        print(json.dumps(row), flush=True)
        if float(val["macro_f1"]) > best_val_f1 + float(PROTOCOL["min_delta"]):
            best_val_f1 = float(val["macro_f1"])
            best_epoch = epoch
            patience_left = int(PROTOCOL["patience"])
            torch.save(
                {
                    "model_kind": kind,
                    "seed": seed,
                    "epoch": epoch,
                    "best_val_macro_f1": best_val_f1,
                    "model_state_dict": model.state_dict(),
                    "parameter_count": count_parameters(model),
                    "selected_by": "validation_macro_f1_only",
                    "test_seen_during_selection": False,
                },
                best_path,
            )
        else:
            patience_left -= 1
        save_last(
            last_path,
            model,
            optimizer,
            scheduler,
            {
                "epoch": epoch,
                "best_epoch": best_epoch,
                "best_val_f1": best_val_f1,
                "patience_left": patience_left,
                "elapsed_seconds": elapsed,
            },
        )
        if patience_left <= 0:
            stop_reason = f"early_stopping_patience_{PROTOCOL['patience']}"
            stop_epoch = epoch
            break

    best = torch.load(best_path, map_location=device, weights_only=False)
    model.load_state_dict(best["model_state_dict"])
    val = evaluate(model, data["val_features"], data["val_labels"], int(PROTOCOL["eval_batch_size"]), device)
    test = evaluate(model, data["test_features"], data["test_labels"], int(PROTOCOL["eval_batch_size"]), device)
    summary: dict[str, object] = {
        "model_kind": kind,
        "seed": seed,
        "horizon_k": HORIZON,
        "parameter_count": count_parameters(model),
        "best_epoch": int(best["epoch"]),
        "stop_epoch": stop_epoch,
        "stop_reason": stop_reason,
        "early_stop": stop_reason.startswith("early_stopping"),
        "max_epoch_hit": stop_reason == "max_epochs",
        "val_macro_f1": val["macro_f1"],
        "val_weighted_f1": val["weighted_f1"],
        "val_accuracy": val["accuracy"],
        "test_macro_f1": test["macro_f1"],
        "test_weighted_f1": test["weighted_f1"],
        "test_accuracy": test["accuracy"],
        "checkpoint": str(best_path),
        "test_evaluated_after_val_selection": True,
        "new5_used": False,
    }
    return summary, curves


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--torch-threads", type=int, default=4)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--preregister-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for path in (args.cache_dir, args.output_dir, args.model_dir):
        assert_no_new5(path)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.model_dir.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(args.torch_threads)

    recurrent = DiagonalRecurrentFI2010()
    feedforward = FeedForwardFI2010()
    recurrent_count = count_parameters(recurrent)
    feedforward_count = count_parameters(feedforward)
    delta_pct = 100.0 * (recurrent_count - feedforward_count) / feedforward_count
    if abs(delta_pct) > 15.0:
        raise RuntimeError(f"Parameter gap {delta_pct:.6f}% exceeds 15%")
    registration = {
        **PROTOCOL,
        "recurrent_parameter_count": recurrent_count,
        "feedforward_parameter_count": feedforward_count,
        "parameter_delta_pct_vs_feedforward": delta_pct,
        "recurrent_parameter_shapes": parameter_shapes(recurrent),
        "feedforward_parameter_shapes": parameter_shapes(feedforward),
    }
    registration_path = args.output_dir / "preregistered_protocol.json"
    if args.preregister_only:
        if registration_path.exists():
            existing = json.loads(registration_path.read_text(encoding="utf-8"))
            if existing != registration:
                raise RuntimeError("Existing preregistration differs from requested protocol")
        else:
            registration_path.write_text(json.dumps(registration, indent=2) + "\n", encoding="ascii")
        print(json.dumps(registration, indent=2))
        return
    if not registration_path.exists():
        raise RuntimeError("Run --preregister-only before training")
    if json.loads(registration_path.read_text(encoding="utf-8")) != registration:
        raise RuntimeError("Training code/config differs from preregistered protocol")

    preflight_row = preflight()
    preflight_row["torch_threads"] = torch.get_num_threads()
    (args.output_dir / "training_preflight.json").write_text(
        json.dumps(preflight_row, indent=2) + "\n", encoding="ascii"
    )
    device = torch.device(args.device)
    vectorization_diff = verify_recurrent_vectorization(device)
    if vectorization_diff > 1e-5:
        raise RuntimeError(f"Vectorized recurrence differs from step loop: {vectorization_diff}")
    (args.output_dir / "recurrent_vectorization_check.json").write_text(
        json.dumps({"max_abs_diff": vectorization_diff, "tolerance": 1e-5}, indent=2) + "\n",
        encoding="ascii",
    )

    data = load_data(args.cache_dir)
    metrics_path = args.output_dir / "capacity_matched_seed_metrics.csv"
    all_metrics: list[dict[str, object]] = [dict(row) for row in load_csv(metrics_path)]
    completed = {(row["model_kind"], int(row["seed"])) for row in all_metrics}
    for kind in ("recurrent", "feedforward"):
        for seed in SEEDS:
            if (kind, seed) in completed:
                print(json.dumps({"skip_completed": {"model_kind": kind, "seed": seed}}), flush=True)
                continue
            summary, _ = train_one(
                kind, seed, data, args.output_dir, args.model_dir, device, args.resume
            )
            all_metrics.append(summary)
            write_csv(metrics_path, all_metrics)
    print(json.dumps({"metrics_path": str(metrics_path), "completed": len(all_metrics)}, indent=2))


if __name__ == "__main__":
    main()
