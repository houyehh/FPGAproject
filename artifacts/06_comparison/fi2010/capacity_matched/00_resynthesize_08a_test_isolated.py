from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import torch
from torch import nn


class PHCLiteFI2010ClassifierV2(nn.Module):
    """Frozen v2 architecture required by the Stage 1 v2 checkpoints."""

    def __init__(self, feature_dim: int = 40, hidden_dim: int = 16, num_classes: int = 3) -> None:
        super().__init__()
        self.feature_dim = int(feature_dim)
        self.hidden_dim = int(hidden_dim)
        self.num_classes = int(num_classes)
        self.enc_linear = nn.Linear(self.feature_dim, self.hidden_dim)
        self.enc_norm = nn.LayerNorm(self.hidden_dim)
        self.gate = nn.Linear(self.hidden_dim, self.hidden_dim)
        self.candidate = nn.Linear(self.hidden_dim, self.hidden_dim)
        self.gain_from_encoded = nn.Linear(self.hidden_dim, self.hidden_dim)
        self.gain_from_prev_state = nn.Linear(self.hidden_dim, self.hidden_dim, bias=False)
        self.synapse = nn.Linear(self.hidden_dim, self.hidden_dim)
        self.loop_norm = nn.LayerNorm(self.hidden_dim)
        self.readout = nn.Linear(self.hidden_dim, self.num_classes)
        self.register_buffer("decay", torch.zeros(self.hidden_dim, dtype=torch.float32))
        self.register_buffer("alpha_scalar", torch.tensor(0.0, dtype=torch.float32))

    def forward_step(self, x_t: torch.Tensor, state_prev: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        encoded_pre = self.enc_norm(self.enc_linear(x_t))
        encoded = encoded_pre * torch.sigmoid(encoded_pre)
        gate_t = torch.sigmoid(self.gate(encoded))
        candidate_t = torch.tanh(self.candidate(encoded))
        state_temporal = self.decay * state_prev + gate_t * candidate_t
        gain_t = torch.sigmoid(self.gain_from_encoded(encoded) + self.gain_from_prev_state(state_prev))
        message_pre = self.synapse(state_temporal)
        message = message_pre * torch.sigmoid(message_pre)
        z = self.loop_norm(state_temporal + self.alpha_scalar * gain_t * message)
        return self.readout(z), z

    def forward(self, x_window: torch.Tensor) -> torch.Tensor:
        state = x_window.new_zeros((x_window.shape[0], self.hidden_dim))
        logits = x_window.new_zeros((x_window.shape[0], self.num_classes))
        for timestep in range(x_window.shape[1]):
            logits, state = self.forward_step(x_window[:, timestep, :], state)
        return logits


def assert_no_new5(path: Path) -> None:
    if "new5" in str(path).lower():
        raise RuntimeError(f"NEW5 path is forbidden: {path}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_selected(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row["selected_for_stage2"].lower() == "true"]
    if len(selected) != 1:
        raise RuntimeError(f"Expected one selected row in {path}, got {len(selected)}")
    return selected[0]


def load_prepare_module(source_phase: Path):
    sys.path.insert(0, str(source_phase))
    script = source_phase / "05_prepare_stage2_hls.py"
    spec = importlib.util.spec_from_file_location("fi2010_stage2_prepare_fixed", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-phase", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_phase.resolve()
    output = args.output_dir.resolve()
    assert_no_new5(source)
    assert_no_new5(output)
    if output == source or source in output.parents:
        raise RuntimeError("Output must not be inside or equal to the frozen 08A phase")

    results = output / "results"
    models = output / "models"
    hls_src = output / "hls_src"
    hls_component = output / "hls_component"
    for path in (results, models, hls_src, hls_component):
        path.mkdir(parents=True, exist_ok=True)

    protected = [
        source / "05_prepare_stage2_hls.py",
        source / "06_collect_stage2_hls_results.py",
        source / "results" / "stage2_checkpoint_selection.csv",
        source / "results" / "stage2_hls_manifest.json",
        source / "hls_src" / "fi2010_phc_weights.hpp",
        source / "hls_component" / "hls_component" / "hls" / "syn" / "report" / "fi2010_phc_step_csynth.rpt",
    ]
    hashes_before = {str(path): sha256_file(path) for path in protected}
    old_selected = read_selected(source / "results" / "stage2_checkpoint_selection.csv")

    shutil.copy2(source / "results" / "stage1_metrics_v2.csv", results / "stage1_metrics_v2.csv")
    for seed in (0, 1, 2):
        checkpoint = source / "models" / f"phc_fi2010_h50_seed{seed}_raw_v2.pt"
        shutil.copy2(checkpoint, models / checkpoint.name)
    module = load_prepare_module(source)
    module.ROOT = output
    module.RESULTS = results
    module.MODELS = models
    module.HLS_SRC = hls_src
    module.HLS_COMPONENT = hls_component
    module.CACHE = source / "data" / "cache"
    module.PHCLiteFI2010Classifier = PHCLiteFI2010ClassifierV2
    module.main()

    new_selected = read_selected(results / "stage2_checkpoint_selection.csv")
    manifest = json.loads((results / "stage2_hls_manifest.json").read_text(encoding="utf-8"))
    if int(new_selected["seed"]) != 0 or int(manifest["seed"]) != 0:
        raise RuntimeError("Corrected val-only selection did not select seed0")
    if "VAL macro F1" not in new_selected["selection_rule"]:
        raise RuntimeError("Selection rule does not identify val-only ranking")

    input_csv = (results / "fi2010_phc_stage2_test_vectors.csv").resolve().as_posix()
    output_csv = (results / "fi2010_phc_stage2_csim_out.csv").resolve().as_posix()
    csim_tcl = f"""open_project hls_component
set_top fi2010_phc_step
add_files ../hls_src/fi2010_phc_hls.cpp
add_files ../hls_src/fi2010_phc_hls.hpp
add_files ../hls_src/fi2010_phc_weights.hpp
add_files -tb ../hls_src/fi2010_phc_testbench.cpp
open_solution -flow_target vivado hls
set_part xc7z020-clg400-1
create_clock -period 10 -name default
csim_design -clean -argv "{input_csv} {output_csv}"
exit
"""
    (hls_component / "run_csim_only.tcl").write_text(csim_tcl, encoding="ascii")

    hashes_after = {str(path): sha256_file(path) for path in protected}
    unchanged = hashes_before == hashes_after
    if not unchanged:
        raise RuntimeError("A protected 08A artifact changed during isolated preparation")

    audit = {
        "status": "prepared_for_isolated_csim_csynth",
        "source_phase": str(source),
        "output_dir": str(output),
        "old_selection": old_selected,
        "corrected_selection": new_selected,
        "selected_checkpoint_changed_vs_old": old_selected["checkpoint"] != new_selected["checkpoint"],
        "protected_08a_hashes_before": hashes_before,
        "protected_08a_hashes_after": hashes_after,
        "protected_08a_unchanged": unchanged,
        "new5_used": False,
    }
    (results / "precondition_prepare_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="ascii"
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
