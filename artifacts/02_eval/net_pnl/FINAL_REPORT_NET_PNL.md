# 16C Final Audit: Net PnL Attribution

RESULT: PASS

## Traceability

TENC_CHECKPOINT_TRACEABLE: yes  
Checkpoint: `n2ew_era/07s_diagonal_hidden8/models/c2b_seed0_tmax500/phc_diagonal_hidden8_seed0_tmax500_best.pt`  
SHA-256: `91b0d77c5dabfb6f88fe1be36caf88ada19d1f47a15da5f8ee1a5052734c11a5`

TENC_THRESHOLD_TRACEABLE: yes. There is no scalar tau: the frozen 10C rule compares the two scores, retreats the worse side one tick, and requires spread >= 2 ticks.

## Gates

CELL_A_REPRODUCES_10C: yes (all 18 published rows within 0.01 TWD).  
CELL_D_REPRODUCES_16A: yes (all 9 market-maker rows within 0.01 TWD).  
SYMMETRIC_CONSISTENT: yes.  
MONOTONICITY_HOLDS: yes (session mean and pooled, all cells/strategies/fees/splits).

## Session handling

ZERO_FILL_SESSIONS_EXCLUDED: 0. LOW_FILL_SESSIONS_COUNT (<100): 0. All val/NEW3 cells use n=6, df=5, critical=2.570582; NEW4 uses n=4, df=3, critical=3.182446.

## Two-by-two attribution

| split   | rule         | fee_scenario   |         A |          B |         C |          D |   model_contribution_C_minus_A |   method_contribution_B_minus_A |   total_D_minus_A |   interaction |   additive_residual |
|:--------|:-------------|:---------------|----------:|-----------:|----------:|-----------:|-------------------------------:|--------------------------------:|------------------:|--------------:|--------------------:|
| new3    | back         | market_maker   | -22.6904  | -22.3625   |  21.7977  |  22.2794   |                       44.4881  |                        0.327932 |         44.9698   |      0.15371  |            0.15371  |
| new3    | back         | proprietary    | -41.3504  | -41.0225   |   3.13774 |   3.61939  |                       44.4881  |                        0.327932 |         44.9698   |      0.15371  |            0.15371  |
| new3    | back         | retail         | -81.3504  | -81.0225   | -36.8623  | -36.3806   |                       44.4881  |                        0.327932 |         44.9698   |      0.15371  |            0.15371  |
| new3    | front        | market_maker   |  71.3863  |  76.3462   |  74.2285  |  79.6628   |                        2.84218 |                        4.95986  |          8.27652  |      0.474478 |            0.474478 |
| new3    | front        | proprietary    |  52.7263  |  57.6862   |  55.5685  |  61.0028   |                        2.84218 |                        4.95986  |          8.27652  |      0.474478 |            0.474478 |
| new3    | front        | retail         |  12.7263  |  17.6862   |  15.5685  |  21.0028   |                        2.84218 |                        4.95986  |          8.27652  |      0.474478 |            0.474478 |
| new3    | proportional | market_maker   |   5.59807 |  10.463    |  22.9599  |  24.3519   |                       17.3619  |                        4.86493  |         18.7538   |     -3.47301  |           -3.47301  |
| new3    | proportional | proprietary    | -13.0619  |  -8.197    |   4.29994 |   5.69186  |                       17.3619  |                        4.86493  |         18.7538   |     -3.47301  |           -3.47301  |
| new3    | proportional | retail         | -53.0619  | -48.197    | -35.7001  | -34.3081   |                       17.3619  |                        4.86493  |         18.7538   |     -3.47301  |           -3.47301  |
| new4    | back         | market_maker   |   9.82559 |  -4.71275  |  20.0629  |  19.4905   |                       10.2373  |                      -14.5383   |          9.66488  |     13.9659   |           13.9659   |
| new4    | back         | proprietary    |  -8.83441 | -23.3728   |   1.40292 |   0.830471 |                       10.2373  |                      -14.5383   |          9.66488  |     13.9659   |           13.9659   |
| new4    | back         | retail         | -48.8344  | -63.3728   | -38.5971  | -39.1695   |                       10.2373  |                      -14.5383   |          9.66488  |     13.9659   |           13.9659   |
| new4    | front        | market_maker   |  86.6724  |  70.4149   |  74.5786  |  73.1459   |                      -12.0938  |                      -16.2575   |        -13.5265   |     14.8248   |           14.8248   |
| new4    | front        | proprietary    |  68.0124  |  51.7549   |  55.9186  |  54.4859   |                      -12.0938  |                      -16.2575   |        -13.5265   |     14.8248   |           14.8248   |
| new4    | front        | retail         |  28.0124  |  11.7549   |  15.9186  |  14.4859   |                      -12.0938  |                      -16.2575   |        -13.5265   |     14.8248   |           14.8248   |
| new4    | proportional | market_maker   |  27.4432  |   9.00084  |  24.8091  |  21.8099   |                       -2.63409 |                      -18.4423   |         -5.63333  |     15.4431   |           15.4431   |
| new4    | proportional | proprietary    |   8.78318 |  -9.65916  |   6.14909 |   3.14985  |                       -2.63409 |                      -18.4423   |         -5.63333  |     15.4431   |           15.4431   |
| new4    | proportional | retail         | -31.2168  | -49.6592   | -33.8509  | -36.8501   |                       -2.63409 |                      -18.4423   |         -5.63333  |     15.4431   |           15.4431   |
| val     | back         | market_maker   |  -2.22724 |  13.0824   |  24.728   |  23.0736   |                       26.9552  |                       15.3096   |         25.3008   |    -16.964    |          -16.964    |
| val     | back         | proprietary    | -20.8872  |  -5.57763  |   6.068   |   4.41357  |                       26.9552  |                       15.3096   |         25.3008   |    -16.964    |          -16.964    |
| val     | back         | retail         | -60.8872  | -45.5776   | -33.932   | -35.5864   |                       26.9552  |                       15.3096   |         25.3008   |    -16.964    |          -16.964    |
| val     | front        | market_maker   |  64.7027  |  58.4747   |  70.7123  |  65.1928   |                        6.00961 |                       -6.22804  |          0.490047 |      0.70848  |            0.70848  |
| val     | front        | proprietary    |  46.0427  |  39.8147   |  52.0523  |  46.5328   |                        6.00961 |                       -6.22804  |          0.490047 |      0.70848  |            0.70848  |
| val     | front        | retail         |   6.04273 |  -0.185307 |  12.0523  |   6.53278  |                        6.00961 |                       -6.22804  |          0.490047 |      0.70848  |            0.70848  |
| val     | proportional | market_maker   |  11.4191  |  17.8218   |  25.8811  |  23.887    |                       14.462   |                        6.4027   |         12.4679   |     -8.39681  |           -8.39681  |
| val     | proportional | proprietary    |  -7.24092 |  -0.838225 |   7.22113 |   5.22701  |                       14.462   |                        6.4027   |         12.4679   |     -8.39681  |           -8.39681  |
| val     | proportional | retail         | -47.2409  | -40.8382   | -32.7789  | -34.773    |                       14.462   |                        6.4027   |         12.4679   |     -8.39681  |           -8.39681  |

MODEL_CONTRIBUTION is C-A; METHOD_CONTRIBUTION is B-A.  
ATTRIBUTION_ADDITIVE: false (max |interaction|=16.964035 TWD/fill).  
DOMINANT_SOURCE: both (market-maker cells: {'method': 5, 'model': 4}).

The interaction is material, so the two effects cannot be reported as independent additive causes. Also, C-A changes checkpoint, action semantics, and spread filter; it is a policy-stack contrast, not a pure architecture effect.

## Section 3.6 replacement values: cell C

| cell    | strategy   | split   | rule         | fee_scenario   |   roundtrip_fee |   session_count |   session_mean_pnl_per_fill |   session_std |   se_clustered |   t_vs_zero |   df |   critical_two_sided_5pct | significantly_positive   |   low_fill_session_count |
|:--------|:-----------|:--------|:-------------|:---------------|----------------:|----------------:|----------------------------:|--------------:|---------------:|------------:|-----:|--------------------------:|:-------------------------|-------------------------:|
| C_D_11b | model      | new3    | back         | market_maker   |          254.68 |               6 |                    21.7977  |      12.3007  |        5.02172 |    4.34069  |    5 |                   2.57058 | True                     |                        0 |
| C_D_11b | model      | new4    | back         | market_maker   |          254.68 |               4 |                    20.0629  |       6.92933 |        3.46467 |    5.79072  |    3 |                   3.18245 | True                     |                        0 |
| C_D_11b | model      | val     | back         | market_maker   |          254.68 |               6 |                    24.728   |      13.8297  |        5.64595 |    4.37977  |    5 |                   2.57058 | True                     |                        0 |
| C_D_11b | model      | new3    | front        | market_maker   |          254.68 |               6 |                    74.2285  |      20.4064  |        8.33088 |    8.91004  |    5 |                   2.57058 | True                     |                        0 |
| C_D_11b | model      | new4    | front        | market_maker   |          254.68 |               4 |                    74.5786  |      16.0392  |        8.01961 |    9.29953  |    3 |                   3.18245 | True                     |                        0 |
| C_D_11b | model      | val     | front        | market_maker   |          254.68 |               6 |                    70.7123  |      22.0339  |        8.99529 |    7.86104  |    5 |                   2.57058 | True                     |                        0 |
| C_D_11b | model      | new3    | proportional | market_maker   |          254.68 |               6 |                    22.9599  |      12.8383  |        5.24121 |    4.38066  |    5 |                   2.57058 | True                     |                        0 |
| C_D_11b | model      | new4    | proportional | market_maker   |          254.68 |               4 |                    24.8091  |      11.2597  |        5.62985 |    4.4067   |    3 |                   3.18245 | True                     |                        0 |
| C_D_11b | model      | val     | proportional | market_maker   |          254.68 |               6 |                    25.8811  |      15.1747  |        6.19507 |    4.1777   |    5 |                   2.57058 | True                     |                        0 |
| C_D_11b | model      | new3    | back         | proprietary    |          292    |               6 |                     3.13774 |      12.3007  |        5.02172 |    0.624834 |    5 |                   2.57058 | False                    |                        0 |
| C_D_11b | model      | new4    | back         | proprietary    |          292    |               4 |                     1.40292 |       6.92933 |        3.46467 |    0.404921 |    3 |                   3.18245 | False                    |                        0 |
| C_D_11b | model      | val     | back         | proprietary    |          292    |               6 |                     6.068   |      13.8297  |        5.64595 |    1.07475  |    5 |                   2.57058 | False                    |                        0 |
| C_D_11b | model      | new3    | front        | proprietary    |          292    |               6 |                    55.5685  |      20.4064  |        8.33088 |    6.67018  |    5 |                   2.57058 | True                     |                        0 |
| C_D_11b | model      | new4    | front        | proprietary    |          292    |               4 |                    55.9186  |      16.0392  |        8.01961 |    6.97273  |    3 |                   3.18245 | True                     |                        0 |
| C_D_11b | model      | val     | front        | proprietary    |          292    |               6 |                    52.0523  |      22.0339  |        8.99529 |    5.78662  |    5 |                   2.57058 | True                     |                        0 |
| C_D_11b | model      | new3    | proportional | proprietary    |          292    |               6 |                     4.29994 |      12.8383  |        5.24121 |    0.820409 |    5 |                   2.57058 | False                    |                        0 |
| C_D_11b | model      | new4    | proportional | proprietary    |          292    |               4 |                     6.14909 |      11.2597  |        5.62985 |    1.09223  |    3 |                   3.18245 | False                    |                        0 |
| C_D_11b | model      | val     | proportional | proprietary    |          292    |               6 |                     7.22113 |      15.1747  |        6.19507 |    1.16563  |    5 |                   2.57058 | False                    |                        0 |
| C_D_11b | model      | new3    | back         | retail         |          372    |               6 |                   -36.8623  |      12.3007  |        5.02172 |   -7.34056  |    5 |                   2.57058 | False                    |                        0 |
| C_D_11b | model      | new4    | back         | retail         |          372    |               4 |                   -38.5971  |       6.92933 |        3.46467 |  -11.1402   |    3 |                   3.18245 | False                    |                        0 |
| C_D_11b | model      | val     | back         | retail         |          372    |               6 |                   -33.932   |      13.8297  |        5.64595 |   -6.00997  |    5 |                   2.57058 | False                    |                        0 |
| C_D_11b | model      | new3    | front        | retail         |          372    |               6 |                    15.5685  |      20.4064  |        8.33088 |    1.86877  |    5 |                   2.57058 | False                    |                        0 |
| C_D_11b | model      | new4    | front        | retail         |          372    |               4 |                    15.9186  |      16.0392  |        8.01961 |    1.98496  |    3 |                   3.18245 | False                    |                        0 |
| C_D_11b | model      | val     | front        | retail         |          372    |               6 |                    12.0523  |      22.0339  |        8.99529 |    1.33985  |    5 |                   2.57058 | False                    |                        0 |
| C_D_11b | model      | new3    | proportional | retail         |          372    |               6 |                   -35.7001  |      12.8383  |        5.24121 |   -6.81142  |    5 |                   2.57058 | False                    |                        0 |
| C_D_11b | model      | new4    | proportional | retail         |          372    |               4 |                   -33.8509  |      11.2597  |        5.62985 |   -6.01275  |    3 |                   3.18245 | False                    |                        0 |
| C_D_11b | model      | val     | proportional | retail         |          372    |               6 |                   -32.7789  |      15.1747  |        6.19507 |   -5.29113  |    5 |                   2.57058 | False                    |                        0 |

At the market-maker fee, back is positive and significantly above zero on all three splits: val 24.727999 (t=4.379773, df=5), NEW3 21.797744 (t=4.340690, df=5), NEW4 20.062916 (t=5.790723, df=3). All nine market-maker rule/split cells are significantly positive.

## Fee sensitivity

| fee_scenario   | rule         | split   | pnl_positive   | significantly_positive   |   pnl_per_fill |
|:---------------|:-------------|:--------|:---------------|:-------------------------|---------------:|
| market_maker   | back         | new3    | True           | True                     |       21.7977  |
| market_maker   | back         | new4    | True           | True                     |       20.0629  |
| market_maker   | back         | val     | True           | True                     |       24.728   |
| market_maker   | front        | new3    | True           | True                     |       74.2285  |
| market_maker   | front        | new4    | True           | True                     |       74.5786  |
| market_maker   | front        | val     | True           | True                     |       70.7123  |
| market_maker   | proportional | new3    | True           | True                     |       22.9599  |
| market_maker   | proportional | new4    | True           | True                     |       24.8091  |
| market_maker   | proportional | val     | True           | True                     |       25.8811  |
| proprietary    | back         | new3    | True           | False                    |        3.13774 |
| proprietary    | back         | new4    | True           | False                    |        1.40292 |
| proprietary    | back         | val     | True           | False                    |        6.068   |
| proprietary    | front        | new3    | True           | True                     |       55.5685  |
| proprietary    | front        | new4    | True           | True                     |       55.9186  |
| proprietary    | front        | val     | True           | True                     |       52.0523  |
| proprietary    | proportional | new3    | True           | False                    |        4.29994 |
| proprietary    | proportional | new4    | True           | False                    |        6.14909 |
| proprietary    | proportional | val     | True           | False                    |        7.22113 |
| retail         | back         | new3    | False          | False                    |      -36.8623  |
| retail         | back         | new4    | False          | False                    |      -38.5971  |
| retail         | back         | val     | False          | False                    |      -33.932   |
| retail         | front        | new3    | True           | False                    |       15.5685  |
| retail         | front        | new4    | True           | False                    |       15.9186  |
| retail         | front        | val     | True           | False                    |       12.0523  |
| retail         | proportional | new3    | False          | False                    |      -35.7001  |
| retail         | proportional | new4    | False          | False                    |      -33.8509  |
| retail         | proportional | val     | False          | False                    |      -32.7789  |

PROFITABLE_AT_PROPRIETARY_FEE: positive in all rule/split cells, but back and proportional are not significant.  
PROFITABLE_AT_RETAIL_FEE: no for back/proportional; front is positive but not significant.

## Symmetric baseline signs

| split   | rule         |   session_mean_pnl_per_fill | sign     |
|:--------|:-------------|----------------------------:|:---------|
| new3    | back         |                    -53.4809 | negative |
| new3    | front        |                     12.1114 | positive |
| new3    | proportional |                    -50.338  | negative |
| new4    | back         |                    -46.7483 | negative |
| new4    | front        |                     12.2221 | positive |
| new4    | proportional |                    -42.3882 | negative |
| val     | back         |                    -47.501  | negative |
| val     | front        |                     19.9104 | positive |
| val     | proportional |                    -46.2642 | negative |

VERDICT: conditional. Significant profitability is supported under the market-maker fee only; it is not a fee-invariant claim.
