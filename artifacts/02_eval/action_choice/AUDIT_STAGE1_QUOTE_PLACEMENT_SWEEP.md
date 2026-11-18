# 10B Stage 1 Quote Placement Sweep

status: PASS

All results are `pilot_two_sessions_only`. The 16-point operating grid was selected on the val session only. NEW3 and the optimistic queue endpoint were used only after the top-three points had been frozen.

## Primary grid: val / pessimistic / cap=3 / market-maker fee

| retreat_depth | spread_threshold | fill_count | fill_rate | spread_capture_per_fill | mark_movement_per_fill | maker_pnl_per_fill | total_maker_pnl | mean_abs_inventory | inventory_cap_stop_rate | underpowered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 10794 | 0.019159121527475786 | 196.29423753937374 | -89.45710579951825 | -20.502868260144524 | -221307.95999999996 | 1.9143519463530398 | 0.3717444669472317 | False |
| 0 | 2 | 7666 | 0.01360698773667124 | 221.17140620923558 | -74.96738846856249 | 18.86401774067309 | 144611.55999999994 | 1.9595056328953278 | 0.3228402501300172 | False |
| 0 | 3 | 728 | 0.001292184590698756 | 319.64285714285717 | -185.02747252747253 | 7.27538461538461 | 5296.479999999996 | 1.9335909419280175 | 0.13441737207283802 | True |
| 0 | 4 | 18 | 3.1949619000793414e-05 | 483.3333333333333 | 5161.111111111111 | 5517.104444444444 | 99307.88 | 2.8101944134316197 | 0.00900446762172361 | True |
| 1 | 0 | 285 | 0.0005058689675125624 | 376.49122807017545 | -510.17543859649123 | -261.02421052631576 | -74391.9 | 1.7094004653994501 | 0.2790319975434293 | True |
| 1 | 2 | 96 | 0.00017039796800423154 | 500.0 | -925.0 | -552.34 | -53024.64 | 1.8504047839229518 | 0.28806486482648697 | True |
| 1 | 3 | 28 | 4.969940733456754e-05 | 578.5714285714286 | -321.42857142857144 | 129.80285714285716 | 3634.48 | 1.9981770967381214 | 0.18125906348566792 | True |
| 1 | 4 | 3 | 5.324936500132236e-06 | 633.3333333333334 | 30533.333333333332 | 31039.326666666668 | 93117.98 | 2.9991551100753124 | 0.011008418724606709 | True |
| 2 | 0 | 44 | 7.809906866860613e-05 | 688.6363636363636 | -634.0909090909091 | -72.79454545454546 | -3202.96 | 1.5735613352810767 | 0.15863340829660608 | True |
| 2 | 2 | 25 | 4.43744708344353e-05 | 748.0 | -1104.0 | -483.34000000000003 | -12083.5 | 1.1426674736903761 | 0.05588343359005444 | True |
| 2 | 3 | 14 | 2.484970366728377e-05 | 807.1428571428571 | 1664.2857142857142 | 2344.0885714285714 | 32817.24 | 1.8734812837356916 | 0.12369117498273834 | True |
| 2 | 4 | 3 | 5.324936500132236e-06 | 866.6666666666666 | 28100.0 | 28839.326666666668 | 86517.98 | 2.9951969072768807 | 0.009879532186578674 | True |
| 3 | 0 | 12 | 2.1299746000528943e-05 | 941.6666666666666 | -2108.3333333333335 | -1294.0066666666667 | -15528.08 | 2.0046309197762815 | 0.43630399707483486 | True |
| 3 | 2 | 10 | 1.774978833377412e-05 | 940.0 | -1720.0 | -907.34 | -9073.4 | 1.7916157099826584 | 0.1947542275558364 | True |
| 3 | 3 | 7 | 1.2424851833641884e-05 | 985.7142857142857 | -1085.7142857142858 | -227.34 | -1591.38 | 1.5189807361547214 | 0.0 | True |
| 3 | 4 | 0 | 0.0 | nan | nan | nan | 0.0 | 0.0 | 0.0 | True |

## Trend summary

- Capture slope versus retreat depth: 220.756205 TWD/fill/tick; monotonic=True.
- Mark-movement slope versus retreat depth: -871.042561 TWD/fill/tick; monotonic=False.
- Gross slope versus retreat depth: -650.286356 TWD/fill/tick.
- Which grows faster: `adverse_selection`.
- Curve is flat under the preregistered 20% residual-slope rule: `False`.

## Frozen top-three confirmation

Frozen points: [(0, 2), (0, 0)].

| split | bound | retreat_depth | spread_threshold | fill_count | fill_rate | spread_capture_per_fill | mark_movement_per_fill | maker_pnl_per_fill | total_maker_pnl | mean_abs_inventory | inventory_cap_stop_rate | underpowered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| val | optimistic | 0 | 2 | 7788 | 0.013823535154343284 | 222.7914740626605 | -72.97123780174627 | 22.48023626091421 | 175076.07999999996 | 1.9524216923713185 | 0.32127294382014493 | False |
| val | optimistic | 0 | 0 | 11204 | 0.019886862849160525 | 200.3391645840771 | -92.07425919314531 | -19.075094609068188 | -213717.3600000001 | 1.8985262350746468 | 0.3682761583068122 | False |
| new3 | pessimistic | 0 | 2 | 4146 | 0.004553186956316421 | 285.8176555716353 | -173.61312108055958 | -15.13546550892427 | -62751.640000000014 | 1.9471584313579062 | 0.3681426269889992 | False |
| new3 | pessimistic | 0 | 0 | 7040 | 0.007731412487329379 | 248.5369318181818 | -183.99147727272728 | -62.79454545454546 | -442073.6 | 1.8784795474487985 | 0.36186524719104823 | False |
| new3 | optimistic | 0 | 2 | 5123 | 0.0056261400813335805 | 313.1368338863947 | -165.0204958032403 | 20.7763380831544 | 106437.17999999993 | 1.9283910864721148 | 0.35025934276404586 | False |
| new3 | optimistic | 0 | 0 | 8309 | 0.009125043516650541 | 271.80166084968107 | -179.70874954868216 | -35.24708869900108 | -292868.06000000006 | 1.890749870136431 | 0.37233779683297624 | False |

## Best powered point

`d=0, s=2`: maker P&L/fill `18.864018` TWD, fills `7666`. Profitable fee scenarios: `['proprietary', 'market_maker']`.

A profitable point exists: `True`. Extreme-event dependency flag: `False`. Sign consistent at both queue brackets: `True`.

## Boundaries

No model was retrained, no fifth split was loaded, no stride-32 sampling was used, and inventory was closed only at the session end. UNDERPOWERED rows (fewer than 1,000 fills) were excluded from operating-point selection.
