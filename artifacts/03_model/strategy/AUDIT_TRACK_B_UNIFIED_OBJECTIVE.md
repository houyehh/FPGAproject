# 14A Track B Unified-Objective Architecture Audit

## Protocol identity

- Only the architecture changed: recurrent PHC hidden8 (186 parameters) to Tiny MLP 16-8-3 (163 parameters).
- The first two outputs regress the same unconditional bid/ask maker-PnL labels as 11B. The third legacy no-quote output remains physically present to preserve the 163-parameter architecture and is excluded from the two-side loss.
- Labels, 16 causal features, normalized MSE, AdamW settings, 2,048-event chunks, three seeds, T_max=500, patience=20, and val-only selection match 11B.
- The threshold manifest was frozen before NEW3/NEW4 feature caches were loaded.
- NEW5 was not loaded.

## Training convergence

| seed | best_epoch | actual_stop_epoch | stop_reason | best_val_mse_normalized | walltime_s |
|---|---|---|---|---|---|
| 0 | 37 | 57 | early_stopping_triggered | 0.542164 | 156.762290 |
| 1 | 17 | 37 | early_stopping_triggered | 0.542950 | 82.848709 |
| 2 | 33 | 53 | early_stopping_triggered | 0.542442 | 115.726704 |

Selected seed: 2; tau: -5.696922255; val fills: 21388; criterion: absolute.

## Recurrent versus feedforward

| split | bound | pnl_per_fill_market_maker_recurrent | pnl_per_fill_market_maker_feedforward | fills | mean_recurrent_minus_feedforward | t_value | critical_value | recurrent_significantly_better | aggregate_recurrent_minus_feedforward |
|---|---|---|---|---|---|---|---|---|---|
| new3 | optimistic | 24.363996 | 17.984200 | 76789 | 11.202088 | 1.860327 | 2.570582 | False | 6.379796 |
| new4 | optimistic | 21.827914 | 11.733198 | 30233 | -4.021363 | -0.149479 | 3.182446 | False | 10.094716 |
| val | optimistic | 23.887014 | 15.154333 | 21617 | 9.870205 | 2.275442 | 2.570582 | False | 8.732681 |
| new3 | pessimistic | 22.292254 | 15.218570 | 75167 | 11.115186 | 2.109974 | 2.570582 | False | 7.073685 |
| new4 | pessimistic | 19.503035 | 9.857319 | 29693 | -4.264048 | -0.158093 | 3.182446 | False | 9.645715 |
| val | pessimistic | 23.073574 | 14.187960 | 21388 | 10.097479 | 2.497306 | 2.570582 | False | 8.885615 |

RECURRENT_BEATS_FEEDFORWARD_UNDER_UNIFIED_OBJECTIVE: false
BRACKET_SIGN_STABLE: true

The recurrent-minus-feedforward session mean is positive but not significant on val and NEW3, and negative on NEW4. The recurrent advantage claimed under the old objective therefore does not survive the unified-objective comparison.
