# 16A Front Cancellation Endpoint

RESULT: PASS

EXISTING_ENDPOINTS_REPRODUCED: yes

MONOTONICITY_HOLDS: true

D_NEGATIVE_COUNT: 0

D_STATS: `{"count": 19956062, "max": 100.0, "median_d_over_trade_when_trade_positive": 0.0, "negative_count": 0, "p50": 0.0, "p90": 0.0, "p99": 2.0, "ratio_count": 163429, "zero_fraction": 0.9127270199902165}`

## Historical selected-side fill rates

| split   | rule         | side     |   selected |   filled |   fill_rate |
|:--------|:-------------|:---------|-----------:|---------:|------------:|
| new3    | back         | ask      |      71577 |    25524 |    0.356595 |
| new3    | back         | bid      |      66219 |    23362 |    0.352799 |
| new3    | back         | combined |     137796 |    48886 |    0.354771 |
| new3    | front        | ask      |      71577 |    31188 |    0.435727 |
| new3    | front        | bid      |      66219 |    28347 |    0.42808  |
| new3    | front        | combined |     137796 |    59535 |    0.432052 |
| new3    | proportional | ask      |      71577 |    25937 |    0.362365 |
| new3    | proportional | bid      |      66219 |    23819 |    0.3597   |
| new3    | proportional | combined |     137796 |    49756 |    0.361085 |
| new4    | back         | ask      |      27321 |    10300 |    0.376999 |
| new4    | back         | bid      |      25368 |     9273 |    0.365539 |
| new4    | back         | combined |      52689 |    19573 |    0.371482 |
| new4    | front        | ask      |      27321 |    12496 |    0.457377 |
| new4    | front        | bid      |      25368 |    11268 |    0.444182 |
| new4    | front        | combined |      52689 |    23764 |    0.451024 |
| new4    | proportional | ask      |      27321 |    10475 |    0.383405 |
| new4    | proportional | bid      |      25368 |     9425 |    0.371531 |
| new4    | proportional | combined |      52689 |    19900 |    0.377688 |
| val     | back         | ask      |      33370 |    12988 |    0.389212 |
| val     | back         | bid      |      30225 |    11255 |    0.372374 |
| val     | back         | combined |      63595 |    24243 |    0.381209 |
| val     | front        | ask      |      33370 |    16650 |    0.498951 |
| val     | front        | bid      |      30225 |    14733 |    0.487444 |
| val     | front        | combined |      63595 |    31383 |    0.493482 |
| val     | proportional | ask      |      33370 |    13220 |    0.396164 |
| val     | proportional | bid      |      30225 |    11527 |    0.381373 |
| val     | proportional | combined |      63595 |    24747 |    0.389134 |

## Deterministic aggregates

| strategy   | split   | config           | rule         |   fill_count |   capture_per_fill |   mark_movement_per_fill |   gross_per_fill |   maker_pnl_per_fill |
|:-----------|:--------|:-----------------|:-------------|-------------:|-------------------:|-------------------------:|-----------------:|---------------------:|
| symmetric  | val     | no_spread_filter | back         |        98703 |            215.03  |                -134.112  |          80.9175 |            -46.4225  |
| model_11b  | val     | no_spread_filter | back         |        30587 |            234.766 |                 -84.3528 |         150.414  |             23.0736  |
| symmetric  | val     | spread_ge_2      | back         |        71428 |            239.896 |                -116.033  |         123.863  |             -3.47681 |
| model_11b  | val     | spread_ge_2      | back         |        29751 |            239.185 |                 -85.6812 |         153.504  |             26.1641  |
| symmetric  | val     | no_spread_filter | proportional |       101910 |            214.901 |                -132.807  |          82.094  |            -45.246   |
| model_11b  | val     | no_spread_filter | proportional |        30888 |            235.295 |                 -84.0682 |         151.227  |             23.887   |
| symmetric  | val     | spread_ge_2      | proportional |        73768 |            240.257 |                -114.394  |         125.864  |             -1.47648 |
| model_11b  | val     | spread_ge_2      | proportional |        30056 |            239.676 |                 -85.3407 |         154.335  |             26.9952  |
| symmetric  | val     | no_spread_filter | front        |       212278 |            217.064 |                 -71.3131 |         145.751  |             18.4109  |
| model_11b  | val     | no_spread_filter | front        |        58268 |            243.557 |                 -51.0246 |         192.533  |             65.1928  |
| symmetric  | val     | spread_ge_2      | front        |       170959 |            237.449 |                 -64.2148 |         173.235  |             45.8945  |
| model_11b  | val     | spread_ge_2      | front        |        57426 |            246.235 |                 -51.6769 |         194.558  |             67.2182  |
| symmetric  | new3    | no_spread_filter | back         |       213588 |            251.346 |                -174.981  |          76.3648 |            -50.9752  |
| model_11b  | new3    | no_spread_filter | back         |        78163 |            296.593 |                -146.974  |         149.619  |             22.2794  |
| symmetric  | new3    | spread_ge_2      | back         |       172678 |            275.399 |                -168.534  |         106.865  |            -20.4752  |
| model_11b  | new3    | spread_ge_2      | back         |        78100 |            296.784 |                -147.227  |         149.557  |             22.217   |
| symmetric  | new3    | no_spread_filter | proportional |       220273 |            251.579 |                -172.382  |          79.1972 |            -48.1428  |
| model_11b  | new3    | no_spread_filter | proportional |        79587 |            297.236 |                -145.544  |         151.692  |             24.3519  |
| symmetric  | new3    | spread_ge_2      | proportional |       178569 |            275.632 |                -165.982  |         109.649  |            -17.6905  |
| model_11b  | new3    | spread_ge_2      | proportional |        79526 |            297.429 |                -145.911  |         151.518  |             24.1777  |
| symmetric  | new3    | no_spread_filter | front        |       386484 |            253.763 |                -109.258  |         144.506  |             17.1656  |
| model_11b  | new3    | no_spread_filter | front        |       150768 |            297.24  |                 -90.2373 |         207.003  |             79.6628  |
| symmetric  | new3    | spread_ge_2      | front        |       331305 |            272.867 |                -104.234  |         168.633  |             41.2928  |
| model_11b  | new3    | spread_ge_2      | front        |       150699 |            297.363 |                 -90.412  |         206.951  |             79.6109  |
| symmetric  | new4    | no_spread_filter | back         |        87456 |            243.263 |                -168.153  |          75.1098 |            -52.2302  |
| model_11b  | new4    | no_spread_filter | back         |        32844 |            283.443 |                -136.612  |         146.83   |             19.4905  |
| symmetric  | new4    | spread_ge_2      | back         |        67646 |            271.11  |                -163.989  |         107.121  |            -20.2191  |
| model_11b  | new4    | spread_ge_2      | back         |        31716 |            289.819 |                -139.362  |         150.457  |             23.1172  |
| symmetric  | new4    | no_spread_filter | proportional |        90342 |            243.367 |                -164.788  |          78.5792 |            -48.7608  |
| model_11b  | new4    | no_spread_filter | proportional |        33406 |            284.257 |                -135.107  |         149.15   |             21.8099  |
| symmetric  | new4    | spread_ge_2      | proportional |        70071 |            271.288 |                -160.537  |         110.751  |            -16.5895  |
| model_11b  | new4    | spread_ge_2      | proportional |        32266 |            290.609 |                -137.677  |         152.932  |             25.5919  |
| symmetric  | new4    | no_spread_filter | front        |       155773 |            244.571 |                -105.79   |         138.781  |             11.4414  |
| model_11b  | new4    | no_spread_filter | front        |        58660 |            286.86  |                 -86.374  |         200.486  |             73.1459  |
| symmetric  | new4    | spread_ge_2      | front        |       128885 |            267.088 |                -101.762  |         165.326  |             37.9857  |
| model_11b  | new4    | spread_ge_2      | front        |        57360 |            291.116 |                 -87.1531 |         203.963  |             76.6227  |

## Session-clustered model improvements

| config           | rule         | split   |   session_count | paired_differences                                                                  |   mean_improvement |   session_std |   se_clustered |        t |   df |   critical | positive   | significant   |
|:-----------------|:-------------|:--------|----------------:|:------------------------------------------------------------------------------------|-------------------:|--------------:|---------------:|---------:|-----:|-----------:|:-----------|:--------------|
| no_spread_filter | back         | val     |               6 | 84.3565519381;43.8093477811;67.24347813;61.3404274676;95.1574495471;81.4667595905   |            72.229  |      18.489   |        7.54811 |  9.56915 |    5 |    2.57058 | True       | True          |
| no_spread_filter | back         | new3    |               6 | 68.4227872764;102.030256646;78.8868867263;69.1195917769;57.180283395;76.0323335763  |            75.2787 |      15.1111  |        6.16907 | 12.2026  |    5 |    2.57058 | True       | True          |
| no_spread_filter | back         | new4    |               4 | 70.0691945598;52.9953394675;71.2483554539;72.9318086506                             |            66.8112 |       9.28516 |        4.64258 | 14.391   |    3 |    3.18245 | True       | True          |
| no_spread_filter | proportional | val     |               6 | 87.8205957882;44.1521748778;64.63396467;59.9764630141;94.8178304709;81.4708654125   |            72.1453 |      19.1564  |        7.82057 |  9.22507 |    5 |    2.57058 | True       | True          |
| no_spread_filter | proportional | new3    |               6 | 67.7270848429;99.3624363444;79.3235047081;68.0658943135;57.3501956634;67.9584473716 |            73.2979 |      14.539   |        5.93553 | 12.349   |    5 |    2.57058 | True       | True          |
| no_spread_filter | proportional | new4    |               4 | 68.8407342344;58.8790598695;68.5710043281;72.4984536759                             |            67.1973 |       5.82761 |        2.91381 | 23.0617  |    3 |    3.18245 | True       | True          |
| no_spread_filter | front        | val     |               6 | 68.846733805;30.6323353839;54.8432180937;29.8279879296;75.024073252;45.6371276041   |            50.8019 |      18.9845  |        7.75038 |  6.55476 |    5 |    2.57058 | True       | True          |
| no_spread_filter | front        | new3    |               6 | 54.2907047752;81.9987795616;69.843449704;58.5323562246;50.4092074478;57.6279442445  |            62.1171 |      11.7159  |        4.78298 | 12.9871  |    5 |    2.57058 | True       | True          |
| no_spread_filter | front        | new4    |               4 | 58.616076386;71.4801138034;60.681037741;58.648679885                                |            62.3565 |       6.15863 |        3.07932 | 20.2501  |    3 |    3.18245 | True       | True          |
| spread_ge_2      | back         | val     |               6 | 59.523980023;4.99939099736;29.272143535;24.3851006014;49.7493045944;29.3007924113   |            32.8718 |      19.338   |        7.89471 |  4.16377 |    5 |    2.57058 | True       | True          |
| spread_ge_2      | back         | new3    |               6 | 43.0409397194;65.2360062529;45.8892912491;36.4487467331;30.3408134976;36.9832963784 |            42.9898 |      12.1833  |        4.97381 |  8.64324 |    5 |    2.57058 | True       | True          |
| spread_ge_2      | back         | new4    |               4 | 48.8181552155;19.1418930419;43.4874074499;43.0224450732                             |            38.6175 |      13.2473  |        6.62365 |  5.83024 |    3 |    3.18245 | True       | True          |
| spread_ge_2      | proportional | val     |               6 | 61.3311407317;3.83097893525;25.7810836754;22.3378075556;50.3169796751;28.2477403386 |            31.9743 |      20.6661  |        8.43688 |  3.78982 |    5 |    2.57058 | True       | True          |
| spread_ge_2      | proportional | new3    |               6 | 42.7881043277;61.7412607158;46.2770353255;35.5802268367;30.3275117976;27.3524214479 |            40.6778 |      12.571   |        5.1321  |  7.92614 |    5 |    2.57058 | True       | True          |
| spread_ge_2      | proportional | new4    |               4 | 47.1184471204;23.471063406;41.334456039;42.610316182                                |            38.6336 |      10.4084  |        5.2042  |  7.42354 |    3 |    3.18245 | True       | True          |
| spread_ge_2      | front        | val     |               6 | 48.1897089864;9.4775629523;28.2485399337;8.41253030105;42.1523639859;12.7616044133  |            24.8737 |      17.3683  |        7.09059 |  3.50799 |    5 |    2.57058 | True       | True          |
| spread_ge_2      | front        | new3    |               6 | 34.9643669202;51.9765488083;43.6906905546;32.8673986149;30.044363728;22.2802892968  |            35.9706 |      10.4783  |        4.27776 |  8.40874 |    5 |    2.57058 | True       | True          |
| spread_ge_2      | front        | new4    |               4 | 43.8335514813;40.5420441844;39.4954164635;34.8590733517                             |            39.6825 |       3.70902 |        1.85451 | 21.3978  |    3 |    3.18245 | True       | True          |

## Random-side-cancel control

| split   | config           | rule         |   realizations |   maker_pnl_mean |   maker_pnl_std |   maker_pnl_95p |   mean_fill_count |
|:--------|:-----------------|:-------------|---------------:|-----------------:|----------------:|----------------:|------------------:|
| new3    | no_spread_filter | back         |            100 |        -68.5662  |         1.54133 |      -66.2108   |           96946.6 |
| new3    | no_spread_filter | front        |            100 |        -59.111   |         1.54674 |      -56.6367   |          102531   |
| new3    | no_spread_filter | proportional |            100 |        -68.1198  |         1.50377 |      -65.6861   |           97116.5 |
| new3    | spread_ge_2      | back         |            100 |        -37.6198  |         1.93133 |      -34.0238   |           77989.5 |
| new3    | spread_ge_2      | front        |            100 |        -28.3832  |         1.90628 |      -24.9303   |           83150.9 |
| new3    | spread_ge_2      | proportional |            100 |        -37.1666  |         1.91092 |      -33.7145   |           78149.8 |
| new4    | no_spread_filter | back         |            100 |        -72.0081  |         2.18265 |      -68.3699   |           38972.9 |
| new4    | no_spread_filter | front        |            100 |        -61.8359  |         2.05226 |      -58.2729   |           41435   |
| new4    | no_spread_filter | proportional |            100 |        -71.0725  |         2.19634 |      -67.4998   |           39076   |
| new4    | spread_ge_2      | back         |            100 |        -40.1875  |         2.87552 |      -34.3452   |           30137   |
| new4    | spread_ge_2      | front        |            100 |        -29.6523  |         2.58715 |      -24.3338   |           32393.3 |
| new4    | spread_ge_2      | proportional |            100 |        -39.01    |         2.86216 |      -33.3718   |           30237.3 |
| val     | no_spread_filter | back         |            100 |        -56.626   |         1.92651 |      -53.2174   |           45873.7 |
| val     | no_spread_filter | front        |            100 |        -45.8215  |         1.898   |      -42.9887   |           50567   |
| val     | no_spread_filter | proportional |            100 |        -56.2008  |         1.93447 |      -52.9372   |           45926.1 |
| val     | spread_ge_2      | back         |            100 |        -13.137   |         2.51477 |       -8.65388  |           33206   |
| val     | spread_ge_2      | front        |            100 |         -4.77017 |         2.41796 |       -0.500577 |           37098.7 |
| val     | spread_ge_2      | proportional |            100 |        -12.7566  |         2.5449  |       -8.47042  |           33251.1 |

IMPROVEMENT_STABLE_ACROSS_ALL_THREE_RULES: true

RANDOM_CONTROL_STILL_WORSE_AT_FRONT: true

VERDICT: strengthened
