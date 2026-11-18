status: resolved

# FI-2010 Capacity-Matched Recurrent vs Feedforward

## Scope and verification boundary

- Dataset: FI-2010 NoAuction Zscore Setup 2 cache already prepared by 08A.
- Horizon: k=50, preregistered before training.
- NEW5: not accessed.
- Model training and F1 values: measured PyTorch results.
- 08A prerequisite CSim/csynth: measured Vitis HLS results; no implementation or P&R claim is made.
- Test metrics were computed only after each validation-selected checkpoint was frozen.

## Prerequisite: 08A test-isolated resynthesis

`08A_RESYNTHESIS: done`

`SELECTED_CHECKPOINT_CHANGED_VS_OLD: yes`

| Selection | Seed | Val macro-F1 | Test macro-F1 | Checkpoint |
|---|---:|---:|---:|---|
| old, invalid test-ranked median | 1 | 37.46% | 42.44% | `models\phc_fi2010_h50_seed1_raw_v2.pt` |
| corrected val-ranked median | 0 | 36.65% | 42.44% | `models\phc_fi2010_h50_seed0_raw_v2.pt` |

The corrected selection changed from seed 1 to seed 0. The isolated rerun left protected 08A files unchanged: `True`.

| HLS check for corrected seed | Result | Evidence |
|---|---:|---|
| CSim | 25,600/25,600, 0 mismatch | `n2ew_era\09b_fi2010_capacity_matched\precondition_08a_resynthesis\hls_component\hls_component\hls\csim\report\fi2010_phc_step_csim.log` |
| csynth latency | 7347 cycles / 73.470 us at 10 ns target | `n2ew_era\09b_fi2010_capacity_matched\precondition_08a_resynthesis\hls_component\hls_component\hls\syn\report\fi2010_phc_step_csynth.rpt` |
| csynth resources | DSP 33, LUT 20581, FF 11704, BRAM_18K 3 | `n2ew_era\09b_fi2010_capacity_matched\precondition_08a_resynthesis\hls_component\hls_component\hls\syn\report\fi2010_phc_step_csynth.rpt` |

These are CSim and csynth results, not routed timing or board measurements.

## Preregistered comparison

`RECURRENT: 195 parameters | stateful`

- encoder weight `[4, 40]`, bias `[4]`
- LayerNorm weight/bias `[4]` each
- diagonal decay `[4]`, diagonal gain `[4]`
- readout weight `[3, 4]`, bias `[3]`

`FEEDFORWARD: 179 parameters | stateless`

- hidden weight `[4, 40]`, bias `[4]`
- SiLU
- readout weight `[3, 4]`, bias `[3]`

`PARAM_COUNT_DELTA: 8.94%` relative to feedforward, within the preregistered +/-15% bound.

`HORIZON_K: 50`

`LR_SCHEDULE: AdamW(lr=0.001, weight_decay=0.0001); CosineAnnealingLR(T_max=200, eta_min=1e-05); identical for both sides.`

Common budget: max 200 epochs, patience 10, min_delta 1e-05, batch 512, raw cross-entropy, seeds 0/1/2.

## Per-seed results

| Model | Seed | Best epoch | Stop epoch | Stop reason | Val macro-F1 | Test macro-F1 | Test weighted-F1 |
|---|---:|---:|---:|---|---:|---:|---:|
| feedforward | 0 | 5 | 15 | early_stopping_patience_10 | 25.10% | 40.08% | 42.98% |
| feedforward | 1 | 3 | 13 | early_stopping_patience_10 | 35.27% | 40.10% | 41.72% |
| feedforward | 2 | 5 | 15 | early_stopping_patience_10 | 31.29% | 40.71% | 44.02% |
| recurrent | 0 | 2 | 12 | early_stopping_patience_10 | 24.29% | 38.23% | 41.14% |
| recurrent | 1 | 1 | 11 | early_stopping_patience_10 | 35.33% | 37.70% | 39.10% |
| recurrent | 2 | 9 | 19 | early_stopping_patience_10 | 36.83% | 39.62% | 41.86% |

`BOTH_SIDES_CONVERGED_NATURALLY: yes`

## Three-seed aggregate

| Model | Val macro-F1 mean +/- sample std | Test macro-F1 mean +/- sample std |
|---|---:|---:|
| recurrent | 32.15% +/- 6.85% | 38.52% +/- 0.99% |
| feedforward | 30.56% +/- 5.12% | 40.30% +/- 0.36% |

Primary paired test macro-F1 difference (recurrent - feedforward): -1.78 percentage points. Paired-seed sample standard deviation: 0.66 percentage points. Difference: -2.694 seed standard deviations.

`VERDICT: 前饋勝`

The verdict uses the preregistered paired-seed threshold. If the result is feedforward win, it narrows the TXF conclusion rather than being adjusted away.

## Weighted-F1 reference table

Weighted-F1 is listed separately from the macro-F1 primary endpoint.

| Model | Test weighted-F1 mean +/- sample std | Metric status |
|---|---:|---|
| recurrent | 40.70% +/- 1.43% | measured, three seeds |
| feedforward | 42.91% +/- 1.15% | measured, three seeds |
| DeepLOB | 80.35% | published weighted-F1 reference; not used in the macro-F1 verdict |

DeepLOB source recorded by 08A: Zhang, Zohren, Roberts 2018/2020 arXiv v6, Table II; parameters Table III (https://arxiv.org/pdf/1808.03668). No direct macro-F1 comparison is claimed.

## Files created

- `n2ew_era\09b_fi2010_capacity_matched\00_resynthesize_08a_test_isolated.py`
- `n2ew_era\09b_fi2010_capacity_matched\01_train_capacity_matched.py`
- `n2ew_era\09b_fi2010_capacity_matched\02_summarize_capacity_matched.py`
- `n2ew_era\09b_fi2010_capacity_matched\results\preregistered_protocol.json`
- `n2ew_era\09b_fi2010_capacity_matched\results\capacity_matched_seed_metrics.csv`
- `n2ew_era\09b_fi2010_capacity_matched\results\capacity_matched_aggregate.csv`
- `n2ew_era\09b_fi2010_capacity_matched\results\paired_seed_differences.csv`
- `n2ew_era\09b_fi2010_capacity_matched\results\verdict.json`
- `n2ew_era\09b_fi2010_capacity_matched\models`
- `n2ew_era\09b_fi2010_capacity_matched\precondition_08a_resynthesis`

## Honest conclusion

The measured FI-2010 result is **前饋勝** under the preregistered one-paired-seed-standard-deviation rule. This claim is limited to FI-2010 Setup 2, k=50, the stated 195-vs-179 parameter comparison, and three seeds. It neither changes the TXF result nor establishes a dataset-independent advantage.
