# A Cross-Timestep Recurrent Inference Core for Limit Order Book Market Making on an Entry-Level FPGA

A stateful recurrent inference core on a PYNQ-Z2 (AMD Zynq-7020, 53,200 LUT / 220 DSP), driving
two-sided market-making quote decisions on the Taiwan index futures (TXF) limit order book.
The path from model selection through fixed-point conversion and HLS to on-chip bit-exact
verification is complete.

| | |
|---|---|
| Inference latency | **490 ns** (49 cycles @ 100 MHz, II = 1) |
| Speedup over this project's starting implementation | 45.63x |
| Resources | DSP 176/220 (80.0%), LUT-as-logic 36.0%, CARRY4 33.1%, BRAM 4.3% |
| Model | Diagonal state space model, hidden 8, **186 parameters** |
| Task quality | **+50.80 to +75.28 TWD per fill** over a zero-signal symmetric quoter; all 9 configurations (3 cancellation rules x 3 splits) significant (min t = 6.55) |
| Verification | C simulation -> RTL co-simulation -> place-and-route -> on-chip replay of 4,096 events (0 mismatches on all three outputs; negative control caught) |

---

## Documents

| File | Pages | Contents |
|---|---:|---|
| [`report/專題成果報告.pdf`](report/) | 3 | Summary report: research question, key results, method, interpretation, contribution, limitations, reflections |
| [`report/專題成果完整報告.pdf`](report/) | 24 | Full report: introduction, related work, evaluation method, model and task, hardware, conclusions, reflections |
| [`artifacts/_appendix/附錄_完整紀錄.pdf`](artifacts/_appendix/) | 13 | Full statistical tables, all negative results, gate failure modes |

The appendix is deliberately separate and the full report cites no appendix sections: everything
the report needs is self-contained. Open the appendix for the complete numbers behind a table,
the acceleration levers that did not work, or the measurements left incomplete.

---

## Source data

| | |
|---|---|
| Instrument | TAIFEX Taiwan Stock Index Futures (TXF), 200 TWD per index point |
| Form | Limit order book event stream, 5 levels (L2), with `last_trade_price` / `last_trade_qty` / `total_match_qty` |
| Size | 19 trading sessions (day and night counted separately), 12,897,056 events; 16 sessions and 10,426,497 events are used for evaluation |
| Splits | Train 3 sessions / validation 6 / test set 1 six / test set 2 four, non-overlapping in time |

The data is not distributed here — a single session's parquet is 30 to 70 MB and the full set is
far beyond GitHub's limits. `artifacts/01_data/` holds the data contract, split registry and
deduplication audit.

---

## Layout

```
report/           Summary and full report (PDF), all figures and their generating scripts
artifacts/        The source of every number in the report: measurement code + results + audits
  _appendix/      The appendix as a standalone document
```

Each directory under `artifacts/` holds both the code and the results it produced, so the script
that generated a number sits next to the number.

---

## Report section to file

Section numbers refer to the full report.

### Chapter 3 — Evaluation method

| Section | Topic | Directory | Key files |
|---|---|---|---|
| 3.1 | Splits, feature contract, deduplication audit | `artifacts/01_data/` | `FINAL_EVALUATION_PROTOCOL.md`, `DATASET_ROLE_CONTRACT.md`, `results/dataset_registry.csv`, `common_05a.py` (the 13 raw columns are defined here) |
| 3.2 | Queue position simulation, three cancellation-allocation rules, distribution of `D` | `artifacts/02_eval/fill_simulation/` | `01_run_front_cancel_endpoint.py` (the simulator), `historical_selected_side_fill_rates.csv` (the three fill rates), `d_statistics.json`, `AUDIT_FRONT_CANCEL_ENDPOINT.md` |
| 3.3 | Three-component P&L decomposition | `artifacts/02_eval/decomposition/` | `symmetric_three_component_decomposition.csv` |
| 3.4 | Perfect-foresight ceiling: retreat one tick vs cancel | `artifacts/02_eval/action_choice/` | `perfect_foresight/results/run1/five_baseline_summary.csv`; `stage1_all_results.csv` is the earlier two-session retreat-depth pilot |
| 3.5 | Fee structure, market-maker eligibility check | `artifacts/02_eval/fees/` | `AUDIT_STAGE0_OFFICIAL_RULES.md` (the record of TXF being absent from the designated product list) |

### Chapter 4 — Model and task

| Section | Topic | Directory | Key files |
|---|---|---|---|
| 4.1 | Model comparison: three architectures under one objective | `artifacts/03_model/strategy/` | `track_b_recurrent_vs_feedforward_summary.csv` (Tiny MLP), `budget_tcn_aggregate.csv` (budget-matched TCN), `paired_vs_recurrent.csv`, and `tiny_mlp_hls/`, `tiny_mlp_hls_parallel/`, `tiny_mlp_board/` for the feedforward control's own HLS and on-board results (18 cycles, 184 DSP, WNS +0.544 ns) |
| 4.3 | Training: convergence curves, learning rate schedule | `artifacts/03_model/training/` | `02_train_toxicity.py` (the loss is on line 253), `training_curve_seed{0,1,2}.csv` |
| 4.4 | Objective, action space, label generation, threshold sweep | `artifacts/03_model/objective/` | `01_generate_queue_labels.py`, `03_select_and_evaluate.py` |
| 4.5 | Task quality: 9 configurations, decomposition of the improvement | `artifacts/03_model/task_quality/` | `model_robustness_18_cells.csv` (rows `no_spread_filter`; the `spread_ge_2` rows are a robustness check shown only in the appendix), `improvement_decomposition/improvement_decomposition.csv` (all three rules; the report tables use the `session_paired_*` columns) |
| 4.6 | Absolute P&L: three rules x three fee tiers x three splits | `artifacts/02_eval/net_pnl/` | `cell_c_report_values.csv` (the 27 cells; fee tiers simulated at 254.68 / 292 / 372 TWD per round trip), `attribution_2x2.csv`, `fee_sensitivity.csv` |
| 4.7 | Fixed point: per-tensor formats, error localization | `artifacts/04_fixedpoint/` | `AUDIT_PER_TENSOR_FORMATS.md` (deployed format: `grouped` columns; 97.11% = `RETENTION_RELATIVE`, 85.69% = `RETENTION_ABSOLUTE`), `STAGE_A_AUDIT.md` (the `<24,5>` candidate at 85.11%) |

### Chapter 5 — Hardware

| Section | Topic | Directory | Key files |
|---|---|---|---|
| 5.1 | CPU baseline: final core vs starting model, same harness (LibTorch C++, Intel Core Ultra 7 258V) | `artifacts/05_hls/cpu_baseline/` | `results/final_vs_start/RESULT.json` (final core median 14.6 µs, p99 93.2 µs), `05_cpu_final_vs_start.py`, `README.md` |
| 5.2 | Diagonalization ablation under the early protocol (not used in the report; appendix D.1.2) | `artifacts/05_hls/diagonalization/` | `PHC_DIAGONAL_SSM_ABLATION_REPORT.md` (line 16 states the single-variable condition; section 7f holds the three-seed results), `models/phc_diagonal_ssm.py` |
| 5.2 | Attempt to redo the diagonalization ablation under the current protocol (stopped: dense epoch 1,760.9 s vs diagonal 12.0 s) | `artifacts/05_hls/diagonalization/current_protocol_attempt/` | `AUDIT_STAGE0.md`, `epoch_timing.csv` |
| 5.2 | Why h = 16 does not fit; capacity ablation h = 16 vs h = 8 under the early protocol (appendix A.5, not used in the report) | `artifacts/05_hls/capacity/` | `h8_vs_h16_early_protocol/results/phc_hidden8_vs_hidden16_summary.csv`, `h16_full_pipeline/STAGE1_REPORT.md` (h = 16 fully pipelined: 146 cycles, DSP 781 = 355%, LUT 199%, never routed) |
| 5.4 | Budget-matched TCN and the resource-sharing sweep | `artifacts/06_comparison/budget_tcn/` | `sweep_results_consolidated.csv` (13 configurations, `device_feasible` is `no` for every one), `design_space.csv` |
| 5.4 | FI-2010 public benchmark (recurrent vs TCN) and its independent reproduction | `artifacts/06_comparison/fi2010/` | `capacity_matched/results/capacity_matched_aggregate.csv`, `recurrent_reproduction/results/AUDIT_RECURRENT_REPRODUCTION.md` |
| 5.5 | Four-layer verification, on-board resources and timing | `artifacts/07_board/` | `board_summary_POSITIVE.txt` (WNS 0.290, 0 failing endpoints, DSP 176, CARRY4 4,398), `board_summary_NEGATIVE_CONTROL.txt`, `utilization_routed_POSITIVE.txt`, `hls_src/` (hand-written HLS) |

### Results kept in the repo but not discussed in the report

| Topic | File | Result |
|---|---|---|
| Random side-selection control | `artifacts/03_model/task_quality/random_side_control/AUDIT_RANDOM_SKEW_CONTROL.md`, `front_random_control_checks.csv` | Cancelling a random side is worse than not cancelling at all (−7.34 to −21.40 TWD per fill); the model beats the random 95th percentile in 12/12 configurations. Fill rates were not matched (random fills +54.76% to +205.22%), so the audit returns `cannot_claim` for side-selection information beyond quoting less. |
| Fixed-point acceptance gate | `artifacts/04_fixedpoint/AUDIT_PER_TENSOR_FORMATS.md` | Registered before HLS: absolute P&L retention must fall in 85–92%. Deployed format 85.69% (pass); the `<24,5>` storage candidate 85.11% (fail, not taken to HLS). |
| TCN resource sharing | `artifacts/06_comparison/budget_tcn/sweep_results_consolidated.csv` | Trading latency for area never fits: lowest LUT (42,723) needs 286 DSP; the configuration within the DSP limit (203) needs 65,122 LUT at 5,454 cycles (111x the recurrent core); fabric-only multipliers (12 DSP) need 141,610 LUT. |
| Capture share of the improvement, all rules | `artifacts/03_model/task_quality/improvement_decomposition/improvement_decomposition.csv` | back 35 / 64 / 65%, proportional 36 / 66 / 65%, front 54 / 74 / 69% (validation / test 1 / test 2). |

---

## Figures

All figures and their generating scripts are in `report/figures/`. Each row below names the result
file a figure's values come from.

| Figure | File | Data source |
|---|---|---|
| Fig. 1 | `figA1_feature_label.png` | Schematic (values from sections 4.4 and 3.2) |
| Fig. 2 | `figA2_convergence.png` | `artifacts/03_model/training/training_curve_seed*.csv` |
| Fig. 3 | `figA4_acceleration_ladder.png` | Report section 5.2 |
| Fig. 4 | `figA5_core_architecture.png` | Report section 5.3 |
| Fig. 5 | `figA6_tcn_feasibility.png` | `artifacts/06_comparison/budget_tcn/sweep_results_consolidated.csv` |
| Fig. 6 | `figA7_three_comparisons.png` | The result files of the three comparisons |
| Appendix Fig. A | `fig5_net_pnl_grid.png` | `artifacts/02_eval/net_pnl/cell_c_report_values.csv` |
| Appendix Fig. B | `figA3_improvement_18cells.png` | `artifacts/03_model/task_quality/model_robustness_18_cells.csv` |
