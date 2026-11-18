# 12C Per-Tensor Fixed-Point Format Audit

status: pass

## Per-tensor allocation

Integer widths are the narrowest 18-bit formats with at least 5% positive-range headroom. Source encoder tensors are compile-time inputs to centering and are not stored in the deployed HLS core.

| tensor | max_abs | integer_bits | format | headroom_pct | saturation_count | hls_role |
| --- | --- | --- | --- | --- | --- | --- |
| source_encoder_weight | 7.764952183 | 5 | ap_fixed<18,5> | 51.468679 | 0 | compile_time_source_only |
| folded_encoder_weight | 6.689792393 | 4 | ap_fixed<18,4> | 16.376957 | 0 | deployed |
| source_encoder_bias | 3.951866150 | 4 | ap_fixed<18,4> | 50.601296 | 0 | compile_time_source_only |
| folded_encoder_bias | 4.063857276 | 4 | ap_fixed<18,4> | 49.201396 | 0 | deployed |
| layernorm_gamma | 2.384682655 | 3 | ap_fixed<18,3> | 40.382479 | 0 | deployed |
| layernorm_beta | 1.178844452 | 2 | ap_fixed<18,2> | 41.057328 | 0 | deployed |
| decay | 0.980753243 | 2 | ap_fixed<18,2> | 50.961964 | 0 | deployed |
| gain | 0.699442446 | 1 | ap_fixed<18,1> | 30.055222 | 0 | deployed |
| readout_weight | 1.079990506 | 2 | ap_fixed<18,2> | 46.000063 | 0 | deployed |
| readout_bias | 0.694520414 | 1 | ap_fixed<18,1> | 30.547429 | 0 | deployed |

ALL_SATURATION_ZERO: `true`.

The suggested decay format `ap_fixed<18,1>` was not legal under the registered 5% rule: max |a|=0.980753 leaves only about 1.9% headroom. The selected decay format is therefore `ap_fixed<18,2>`.

## Four-format comparison

Registered point: no-spread-filter/pessimistic. Significance is clustered by session (df=5/5/3).

| split | float_pnl_per_fill | q18_3_pnl_per_fill | q18_4_pnl_per_fill | grouped_pnl_per_fill | q18_3_fills | q18_4_fills | grouped_fills | float_t | q18_3_t | q18_4_t | grouped_t |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| val | 23.073574 | 16.760629 | 20.384868 | 20.619124 | 35775 | 34020 | 34054 | 9.569146 | 9.702608 | 9.386377 | 9.391522 |
| new3 | 22.292254 | 18.379403 | 17.893299 | 17.871535 | 85432 | 86370 | 86416 | 12.245200 | 12.674231 | 12.918427 | 12.809565 |
| new4 | 19.503035 | 13.937915 | 17.181696 | 17.096815 | 36763 | 36389 | 36409 | 14.378974 | 20.311723 | 22.397756 | 20.699706 |

RETENTION_ABSOLUTE: `85.692073219%` (uniform ap_fixed<18,4>: `85.495351292%`).

RETENTION_RELATIVE: `97.110097507%` (uniform ap_fixed<18,4>: `97.026980188%`).

DECISION_FLIP_RATE: `6.143837187%` = `1281174/20852994`.

IMPROVEMENT_OVER_UNIFORM_18_4: `+0.196722` percentage points absolute retention; relative-improvement retention changes by `+0.083117` percentage points.

STILL_SIGNIFICANT_ALL_SPLITS: `true`. t: val `9.391522`, NEW3 `12.809565`, NEW4 `20.699706`.

TAU_FOLD_FLIPS: `0/20852994`.

## Final HLS format table

| tensor | format | integer_bits | fractional_bits | max_abs | headroom_pct | saturation_count | storage_or_operation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| folded_encoder_weight | ap_fixed<18,4> | 4 | 14 | 6.689792392775416 | 16.376957097121085 | 0 | fold_weight ROM |
| folded_encoder_bias | ap_fixed<18,4> | 4 | 14 | 4.063857275759801 | 49.20139649041467 | 0 | fold_bias constant, cast to accumulator |
| layernorm_gamma | ap_fixed<18,3> | 3 | 15 | 2.3846826553344727 | 40.38247877104775 | 0 | gamma ROM |
| layernorm_beta | ap_fixed<18,2> | 2 | 16 | 1.1788444519042969 | 41.05732770788351 | 0 | beta constant, cast to hidden |
| decay | ap_fixed<18,2> | 2 | 16 | 0.9807532429695128 | 50.96196372099854 | 0 | recurrent decay ROM |
| gain | ap_fixed<18,1> | 1 | 17 | 0.699442446231842 | 30.05522174050705 | 0 | recurrent gain ROM |
| readout_weight | ap_fixed<18,2> | 2 | 16 | 1.0799905061721802 | 46.00006270456471 | 0 | readout weight ROM |
| readout_bias | ap_fixed<18,1> | 1 | 17 | 0.6945204138755798 | 30.5474287313746 | 0 | readout bias constant, cast to accumulator |

Unchanged runtime formats: input `ap_fixed<18,12>`, hidden `ap_fixed<18,5>`, accumulator `ap_fixed<40,16>`, variance `ap_fixed<48,24>`, and guard3 scale `ap_fixed<14,5>`.

## Registered verdict

VERDICT: `ACCEPTED: eligible for HLS rebuild`. Absolute retention `85.6921%` lies in the registered 85%-92% accepted band and all splits remain significant.

No HLS synthesis, implementation, place-and-route, bitstream generation, board access, retraining, threshold reselection, wider-than-18-bit constant format, or NEW5 access was performed.
