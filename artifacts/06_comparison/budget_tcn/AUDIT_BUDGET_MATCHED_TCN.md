# 14C Budget-Matched TCN

RESULT: FAIL

## Verification boundary

- Training/evaluation: measured PyTorch/Numba results.
- Hardware: Vitis HLS CSim plus csynth estimates only; no cosim, implementation, route, or board claim.
- NEW5 was not loaded.
- All thresholds were selected on val and frozen before NEW3/NEW4 load: True.

## Design points

| Design | Blocks | RF | Channels | Parameters | MAC | CSim cases / mismatch | csynth cycles / II / DSP / LUT / FF / BRAM18 | BUDGET_MET | Device DSP/LUT/FF/BRAM | Device fit | Same model at 220 DSP gate |
|---|---:|---:|---:|---:|---:|---|---|---|---|---|---|
| A | 3 | 29 | 3 | 305 | 5865 | 16 / 0 | 56 / 57 / 176 / 482926 / 148420 / 0 | no | 80.0% / 907.8% / 139.5% / 0.0% | no | no |
| B | 4 | 61 | 1 | 81 | 3587 | 16 / 0 | 40 / 41 / 176 / 319937 / 81717 / 0 | yes | 80.0% / 601.4% / 76.8% / 0.0% | no | yes |
| C | 5 | 125 | 1 | 89 | 8105 | 16 / 0 | 61 / 62 / 176 / 673405 / 168753 / 0 | no | 80.0% / 1265.8% / 158.6% / 0.0% | no | no |

MAC_FORMULA_USED: `sum over valid conv layers: output_length * input_channels * output_channels * kernel_size; plus channels * 2 readout MACs`.

`BUDGET_MET` is exactly the preregistered latency <= 49 cycles and DSP <= 176 test. `Device fit` separately checks the actual xc7z020 ceilings DSP 220, LUT 53,200, FF 106,400, and BRAM18 280; a formal budget pass is not described as deployable when this second check fails.

The 176-DSP choices are A/B/C = 3/1/1 channels. At 220 DSP the formula permits A/B/C = 4/2/1, but those wider A/B models were not trained; their task-quality effect is `not_measured`. For the same measured models, each HLS summary separately records whether a 220-DSP ceiling changes the formal latency/DSP result.

HLS evidence paths:

- A CSim: `n2ew_era\14c_budget_matched_tcn\results\revised\hls_A\hls_component\hls_project\solution1\csim\report\budget_tcn_A_csim.log`
- A csynth: `n2ew_era\14c_budget_matched_tcn\results\revised\hls_A\hls_component\hls_project\solution1\syn\report\budget_tcn_A_csynth.rpt`
- B CSim: `n2ew_era\14c_budget_matched_tcn\results\revised\hls_B\hls_component\hls_project\solution1\csim\report\budget_tcn_B_csim.log`
- B csynth: `n2ew_era\14c_budget_matched_tcn\results\revised\hls_B\hls_component\hls_project\solution1\syn\report\budget_tcn_B_csynth.rpt`
- C CSim: `n2ew_era\14c_budget_matched_tcn\results\revised\hls_C\hls_component\hls_project\solution1\csim\report\budget_tcn_C_csim.log`
- C csynth: `n2ew_era\14c_budget_matched_tcn\results\revised\hls_C\hls_component\hls_project\solution1\syn\report\budget_tcn_C_csynth.rpt`

## Training

TARGET_HORIZON: H20 maker P&L, including zero for unfilled actions, fee per fill 127.34.

LR_SCHEDULE: AdamW, initial LR 0.001, weight decay 0.0001; CosineAnnealingLR with T_max=500 and eta_min=0.00001 for every design and seed; gradient clip 1.0; batch size 2048; maximum 500 epochs.

TRAIN_SAMPLING_STRIDE: 32, applied after full causal windows were constructed; actual training samples 77206.

VALIDATION_SAMPLING_STRIDE: 1; full-event validation samples 2573395.

The convergence rule is 20 consecutive epochs without at least 0.1% cumulative relative validation-loss improvement from the current convergence reference. Tiny numerical best-checkpoint improvements do not reset this counter.

| Design | Seed | Best epoch | Stop epoch | Val loss | Stop reason | Converged |
|---|---:|---:|---:|---:|---|---|
| A | 0 | 70 | 70 | 0.54174910 | relative_improvement_below_0p1pct_for_20_epochs | True |
| A | 1 | 84 | 85 | 0.54223887 | relative_improvement_below_0p1pct_for_20_epochs | True |
| A | 2 | 81 | 81 | 0.54295165 | relative_improvement_below_0p1pct_for_20_epochs | True |
| B | 0 | 43 | 52 | 0.57886153 | relative_improvement_below_0p1pct_for_20_epochs | True |
| B | 1 | 51 | 51 | 0.57887710 | relative_improvement_below_0p1pct_for_20_epochs | True |
| B | 2 | 75 | 75 | 0.57887870 | relative_improvement_below_0p1pct_for_20_epochs | True |
| C | 0 | 32 | 32 | 0.57886651 | relative_improvement_below_0p1pct_for_20_epochs | True |
| C | 1 | 36 | 36 | 0.57886111 | relative_improvement_below_0p1pct_for_20_epochs | True |
| C | 2 | 15 | 31 | 0.57886056 | relative_improvement_below_0p1pct_for_20_epochs | True |

ALL_SEEDS_CONVERGED: yes

## Evaluation

No-spread-filter primary table. Evaluation uses stride 1, continuous sessions, all 16 agendas, both queue bounds, and inventory cap 3. The t statistic uses agendas as clusters; df is 5/5/3 for val/NEW3/NEW4.

| Design | Split | Bound | Fills | Maker P&L/fill | Improvement vs symmetric | Paired agenda t | Significant |
|---|---|---|---:|---:|---:|---:|---|
| A | val | pessimistic | 34221 | 4.827383 | 51.249883 | 8.620743 | True |
| A | val | optimistic | 34700 | 5.732046 | 50.978042 | 8.814380 | True |
| A | new3 | pessimistic | 91931 | 7.466540 | 58.441763 | 17.095528 | True |
| A | new3 | optimistic | 94167 | 10.288893 | 58.431715 | 13.973902 | True |
| A | new4 | pessimistic | 37223 | 0.269274 | 52.499504 | 4.615650 | True |
| A | new4 | optimistic | 38082 | 3.159974 | 51.920797 | 4.709451 | True |
| B | val | pessimistic | 98703 | -46.422500 | 0.000000 | 0.000000 | False |
| B | val | optimistic | 101910 | -45.245995 | 0.000000 | 0.000000 | False |
| B | new3 | pessimistic | 213588 | -50.975223 | 0.000000 | 0.000000 | False |
| B | new3 | optimistic | 220273 | -48.142822 | 0.000000 | 0.000000 | False |
| B | new4 | pessimistic | 87456 | -52.230231 | 0.000000 | 0.000000 | False |
| B | new4 | optimistic | 90342 | -48.760823 | 0.000000 | 0.000000 | False |
| C | val | pessimistic | 98703 | -46.422500 | 0.000000 | 0.000000 | False |
| C | val | optimistic | 101910 | -45.245995 | 0.000000 | 0.000000 | False |
| C | new3 | pessimistic | 213588 | -50.975223 | 0.000000 | 0.000000 | False |
| C | new3 | optimistic | 220273 | -48.142822 | 0.000000 | 0.000000 | False |
| C | new4 | pessimistic | 87456 | -52.230231 | 0.000000 | 0.000000 | False |
| C | new4 | optimistic | 90342 | -48.760823 | 0.000000 | 0.000000 | False |

## Comparison

- 11B recurrent: 186 parameters, 8 state channels, slowest tau 51.96 events, 49 cycles, 176 routed DSP.
- Symmetric quoting: zero-signal baseline evaluated by the same simulator.
- Existing 128-event TCN: not_measured (14B Track B' has no completed evaluation manifest).
- Budget-matched TCNs: this report.

BEST_BUDGET_MATCHED_TCN: B

BEST_DEVICE_FEASIBLE_BUDGET_MATCHED_TCN: not_measured (none of A/B/C fits all xc7z020 resources)

| Split | Bound | Mean TCN - recurrent P&L/fill | Paired agenda t | df | Significant |
|---|---|---:|---:|---:|---|
| val | pessimistic | -72.229002 | -9.569146 | 5 | True |
| val | optimistic | -72.145316 | -9.225069 | 5 | True |
| new3 | pessimistic | -75.287140 | -12.245200 | 5 | True |
| new3 | optimistic | -73.301871 | -12.395244 | 5 | True |
| new4 | pessimistic | -66.847250 | -14.378974 | 3 | True |
| new4 | optimistic | -67.235988 | -23.023548 | 3 | True |

Pooled descriptive differences across all 16 agendas (no per-fill standard error is used):

- pessimistic: pooled TCN -50.125662, recurrent 21.814038, difference -71.939700
- optimistic: pooled TCN -47.562532, recurrent 23.672821, difference -71.235353

BUDGET_MATCHED_TCN_BEATS_RECURRENT: no

BRACKET_SIGN_STABLE: yes

The `beats` gate requires positive, significant agenda-clustered differences in every split and both queue brackets; it is not based on per-fill standard errors.

## Files created

- `n2ew_era\14c_budget_matched_tcn\budget_matched_tcn.py`
- `n2ew_era\14c_budget_matched_tcn\00_write_design_space.py`
- `n2ew_era\14c_budget_matched_tcn\01_train_budget_tcn.py`
- `n2ew_era\14c_budget_matched_tcn\02_evaluate_budget_tcn.py`
- `n2ew_era\14c_budget_matched_tcn\03_prepare_hls.py`
- `n2ew_era\14c_budget_matched_tcn\04_collect_hls.py`
- `n2ew_era\14c_budget_matched_tcn\05_finalize_report.py`
- `n2ew_era\14c_budget_matched_tcn\results\revised\design_space.csv`
- `n2ew_era\14c_budget_matched_tcn\results\revised\design_space.json`
- `n2ew_era\14c_budget_matched_tcn\results\revised\training_A`
- `n2ew_era\14c_budget_matched_tcn\results\revised\training_B`
- `n2ew_era\14c_budget_matched_tcn\results\revised\training_C`
- `n2ew_era\14c_budget_matched_tcn\results\revised\evaluation`
- `n2ew_era\14c_budget_matched_tcn\results\revised\hls_A_summary.json`
- `n2ew_era\14c_budget_matched_tcn\results\revised\hls_B_summary.json`
- `n2ew_era\14c_budget_matched_tcn\results\revised\hls_C_summary.json`

## Honest conclusion

The result above is limited to the preregistered 49-cycle/176-DSP gate and the measured three-seed H20 protocol. A csynth pass is an estimate, not routed timing. Passing the formal cycle/DSP gate does not override an xc7z020 LUT/FF overflow; therefore `RESULT` is FAIL when no design passes both checks. The unfinished 14B Track B' endpoint remains explicitly `not_measured` and was not inferred from partial seed0 training.
