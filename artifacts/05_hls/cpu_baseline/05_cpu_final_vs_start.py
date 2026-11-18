"""CPU latency: final deployed core (186 params) vs starting model (1,731 params).

Same machine, same LibTorch C++ harness (cpp_libtorch_concurrent_benchmark.exe),
same protocol (batch 1, 100 warm-up, 10,000 timed calls, 1 stream), interleaved
start/final/start/final... so background load hits both models equally.

Run from the project root with the project venv:
    .venv\\Scripts\\python.exe n2ew_era\\06f_phc_lite_manual_hls\\05_cpu_final_vs_start.py
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "n2ew_era" / "06f_phc_lite_manual_hls"
OUT = HERE / "results" / "cpu_final_vs_start"
EXE = HERE / "results" / "libtorch_build" / "cpp_libtorch_concurrent_benchmark.exe"
TORCH_LIB = ROOT / ".venv" / "Lib" / "site-packages" / "torch" / "lib"
START_TS = HERE / "models" / "phc_stp_step_hls_seed2_torchscript.pt"
FINAL_CKPT = (ROOT / "n2ew_era" / "11b_toxicity_objective_retrain_v2" / "results" / "run1"
              / "stage2" / "models" / "toxicity_hidden8_seed1_best.pt")
FINAL_TS = HERE / "models" / "final_core_h8_seed1_torchscript.pt"
REPEATS = 3          # each repeat = 1 start run + 1 final run, each with 2 rounds
ROUNDS = 2
ITERS = 10000
WARMUP = 100

sys.path.insert(0, str(ROOT / "n2ew_era" / "07s_diagonal_hidden8"))
from models.phc_diagonal_hidden8 import PHCDiagonalSSMHidden8  # noqa: E402


class FinalStep(nn.Module):
    """One event: x_cat[1,32] = 16 features | 8 state | 8 unused padding.

    The harness feeds a [1,32] tensor (the starting model's input width); the
    padding keeps the exe unchanged. Output = 2 scores | 8 new state.
    """

    def __init__(self, base: PHCDiagonalSSMHidden8) -> None:
        super().__init__()
        self.encoder = base.encoder
        self.readout = base.readout
        self.register_buffer("decay", torch.sigmoid(base.diag_decay_param.detach()).view(1, -1))
        self.register_buffer("gain", torch.sigmoid(base.diag_gain_param.detach()).view(1, -1))

    def forward(self, x_cat: torch.Tensor) -> torch.Tensor:
        x = x_cat[:, :16]
        state = x_cat[:, 16:24]
        new_state = self.decay * state + self.gain * self.encoder(x)
        return torch.cat([self.readout(new_state), new_state], dim=1)


def export_final() -> dict:
    ckpt = torch.load(FINAL_CKPT, map_location="cpu", weights_only=False)
    base = PHCDiagonalSSMHidden8(16, 8, 1, 0.0)
    base.load_state_dict(ckpt["model_state_dict"], strict=True)
    base.eval()
    n_params = sum(p.numel() for p in base.parameters())
    if n_params != 186:
        raise RuntimeError(f"expected 186 parameters, got {n_params}")
    step = FinalStep(base).eval()
    torch.manual_seed(0)
    x_cat = torch.randn(1, 32)
    with torch.no_grad():
        ref_state = base.step(x_cat[:, :16], x_cat[:, 16:24])
        ref = torch.cat([base.readout(ref_state), ref_state], dim=1)
        traced = torch.jit.freeze(torch.jit.trace(step, x_cat, strict=True).eval())
        out = traced(x_cat)
    diff = float((ref - out).abs().max())
    if diff > 1e-6:
        raise RuntimeError(f"trace mismatch {diff}")
    traced.save(str(FINAL_TS))
    return {"final_params": n_params, "trace_max_abs_diff": diff, "checkpoint": str(FINAL_CKPT.relative_to(ROOT))}


def run(model: Path, tag: str) -> list[dict]:
    env = dict(os.environ)
    env["PATH"] = str(TORCH_LIB) + os.pathsep + env.get("PATH", "")
    js = OUT / f"{tag}.json"
    raw = OUT / f"{tag}.csv"
    cmd = [str(EXE), str(model), str(js), str(raw), "1", str(ROUNDS), str(ITERS), str(WARMUP)]
    subprocess.run(cmd, check=True, env=env, cwd=str(ROOT))
    return json.loads(js.read_text(encoding="utf-8"))["round_summaries"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = export_final()
    rows = []
    for rep in range(1, REPEATS + 1):
        for name, model in (("start_1731", START_TS), ("final_186", FINAL_TS)):
            for r in run(model, f"{name}_rep{rep}"):
                rows.append({"model": name, "repeat": rep, **r})
                print(name, rep, r["round"], "p50", r["p50_us"], "p99", r["p99_us"], flush=True)
    with (OUT / "summary.csv").open("w", newline="", encoding="ascii") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    agg = {}
    for name in ("start_1731", "final_186"):
        sel = [r for r in rows if r["model"] == name]
        agg[name] = {
            "runs": len(sel),
            "median_of_p50_us": statistics.median(r["p50_us"] for r in sel),
            "median_of_p99_us": statistics.median(r["p99_us"] for r in sel),
            "range_p50_us": [min(r["p50_us"] for r in sel), max(r["p50_us"] for r in sel)],
        }
    fpga_us = 0.49
    for name in agg:
        agg[name]["ratio_p50_vs_490ns"] = agg[name]["median_of_p50_us"] / fpga_us
        agg[name]["ratio_p99_vs_490ns"] = agg[name]["median_of_p99_us"] / fpga_us
    result = {**meta, "cpu": os.environ.get("PROCESSOR_IDENTIFIER", ""), "protocol":
              f"LibTorch C++, 1 stream, {WARMUP} warm-up, {ITERS} timed calls, {ROUNDS} rounds x {REPEATS} interleaved repeats",
              "aggregate": agg}
    (OUT / "RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
