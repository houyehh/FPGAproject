from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROOT = PROJECT_ROOT / "n2ew_era" / "07i_tiny_mlp_manual_hls"
RESULTS = ROOT / "results"
PHASE07H = PROJECT_ROOT / "n2ew_era" / "07h_tiny_mlp_fixed_point_validation"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    sys.stdout.reconfigure(errors="replace")
    RESULTS.mkdir(parents=True, exist_ok=True)
    mixed = load_module("tiny_mlp_mixed_07i", PHASE07H / "01_validate_mixed_precision.py")
    base = mixed.base
    config = next(item for item in mixed.CONFIGS if item.name == "uniform28_14_accargmax")
    weights = np.load(PHASE07H / "models" / "tiny_mlp_h8_seed1_folded_float_weights.npz")

    payload = mixed.helpers.load_payload("val")
    raw_x, _ = mixed.helpers.base_features(payload)
    raw_x = np.asarray(raw_x[:25_600], dtype=np.float64)
    x_q, overflow = base.quantize(raw_x, config.data)
    if overflow:
        raise RuntimeError(f"input quantization overflow_count={overflow}")
    logits, audit = mixed.mixed_forward(
        raw_x,
        weights["w1"].astype(np.float64),
        weights["b1"].astype(np.float64),
        weights["w2"].astype(np.float64),
        weights["b2"].astype(np.float64),
        config,
    )
    if audit["total_overflow_count"]:
        raise RuntimeError(f"fixed-point overflow audit failed: {audit}")
    logits_q = np.rint(logits * float(1 << base.ACC_FRAC_BITS)).astype(np.int64)
    action = np.argmax(logits_q, axis=1).astype(np.int64)

    columns = {"row_id": np.arange(len(raw_x), dtype=np.int64)}
    columns.update({f"x{i}_q": x_q[:, i] for i in range(16)})
    columns.update({f"logit{o}_q": logits_q[:, o] for o in range(3)})
    columns["action"] = action
    output = RESULTS / "tiny_mlp_q28_test_vectors.csv"
    pd.DataFrame(columns).to_csv(output, index=False)
    print(f"[OK] vectors={len(raw_x)} output={output}")
    print(f"[OK] overflow_count={audit['total_overflow_count']}")


if __name__ == "__main__":
    main()
