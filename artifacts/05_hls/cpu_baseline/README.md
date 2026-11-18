# CPU baseline (report section 5.1)

The report uses `results/final_vs_start/RESULT.json`.

| | |
|---|---|
| CPU | Intel Core Ultra 7 258V (8 cores), Windows laptop |
| Software | LibTorch C++ (TorchScript float32), `torch::NoGradGuard`, 8 intra-op / 8 inter-op threads, batch 1, one caller stream |
| Models | `final_core_h8_seed1_torchscript.pt` — the deployed 186-parameter core (float, one event per call: 16 features + 8-state in, 2 scores + 8-state out); `phc_stp_step_hls_seed2_torchscript.pt` — the starting dense model (1,731 parameters), the same model as the 22.360 µs FPGA starting point |
| Protocol | 100 warm-up calls, 10,000 timed calls per round, 2 rounds per run, start/final runs interleaved 3 times (6 rounds per model) |
| Script | `05_cpu_final_vs_start.py` (exports the final model, checks the trace against the PyTorch step, runs `cpp_libtorch_concurrent_benchmark.cpp` with concurrency 1) |

| Model | median of the 6 round medians | median of the 6 round p99s | p99 range over rounds |
|---|---:|---:|---:|
| Final core, 186 parameters | **14.6 µs** (30x of 490 ns) | **93.2 µs** (190x) | 34.5 – 129.9 µs |
| Starting model, 1,731 parameters | 34.25 µs | 204.4 µs | 155.9 – 246.1 µs |

Per-round rows: `results/final_vs_start/summary.csv`; every timed call: `results/final_vs_start/*_rep*.csv`.

## Earlier run (superseded in the report)

Before the final model was timed, the report quoted the starting model alone from
`results/cpu_concurrent_benchmark_summary.csv` (concurrency 1, round 1: median 45.7 µs, p99 338.8 µs),
measured on the same laptop on 2026-06-29 under 37–45% background load. Rows with concurrency 2, 4, 8 run
several streams at once. `cpu_baseline_timing_libtorch*.json` and `cpu_baseline_timing_libtorch_raw_drift_report.md`
record the run-to-run drift of the single-stream benchmark.
