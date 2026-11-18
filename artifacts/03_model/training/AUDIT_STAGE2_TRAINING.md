# 11B Stage 2 H20 Toxicity Training

status: complete

ARCHITECTURE_UNCHANGED: `yes` (186 trainable parameters; 16 deployed PHC inputs derived from the unchanged 13 TARGET_RAW_COLUMNS; hidden dimension 8; two outputs).

Loss: normalized MSE on unconditional per-side maker P&L. MSE is used because its conditional optimum is the expected value required by the decision rule. Huber and class weighting were rejected because they would change the estimand or bias genuine zero outcomes.

Training processes every event in order with continuous recurrent state. The diagonal affine recurrence is evaluated by a mathematically equivalent associative prefix scan inside each 2,048-event TBPTT chunk; numerical state is carried across chunk boundaries while gradients are detached. No stride-32 or other event sampling is used.

|   seed |   parameter_count |   actual_stop_epoch |   best_epoch | stop_reason              |   best_val_mse_normalized |   walltime_s |
|-------:|------------------:|--------------------:|-------------:|:-------------------------|--------------------------:|-------------:|
|      0 |               186 |                 474 |          454 | early_stopping_triggered |                  0.52176  |      9766.35 |
|      1 |               186 |                 451 |          431 | early_stopping_triggered |                  0.520618 |      9640.07 |
|      2 |               186 |                 440 |          420 | early_stopping_triggered |                  0.52025  |      9056.94 |

Thresholds and OOS data were not accessed during training. NEW5 was not loaded.
