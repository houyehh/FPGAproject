# 10D Random-Skew Control

status: cannot_claim

Random realizations: 100; seeds recorded: yes; Numba threads: 8; runtime: 1309.3 s.

## Full-session decomposition

| config | bound | split | symmetric_pnl_per_fill | random_mean_pnl_per_fill | random_std | random_p95 | signal_pnl_per_fill | mechanical_less_quoting_contribution | signal_information_contribution | signal_beats_random_95p | signal_fill_count | random_mean_fill_count | fill_count_gap_percent | fill_rate_matched | paired_t | paired_df | paired_significantly_better |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_spread_filter | pessimistic | val | -47.50100319937473 | -59.135708159734826 | 1.9347709497339591 | -56.16271954768146 | -46.73468609828986 | -11.634704960360096 | 12.401022061444962 | True | 29690 | 48043.45 | 61.81694173122262 | False | 1.1811860052720786 | 5 | False |
| no_spread_filter | pessimistic | new3 | -53.48094635254171 | -70.57854772847747 | 1.5045922362093644 | -68.43335905456529 | -63.19093000065547 | -17.097601375935767 | 7.387617727822004 | True | 42482 | 104698.74 | 146.4543571394944 | False | 0.9478855921032516 | 5 | False |
| no_spread_filter | pessimistic | new4 | -46.748258036094114 | -65.82086100413076 | 2.270896553783292 | -61.56820414090911 | -44.48552795309535 | -19.072602968036648 | 21.335333051035413 | True | 23560 | 42171.06 | 78.99431239388794 | False | 3.6920342941508575 | 3 | True |
| no_spread_filter | optimistic | val | -46.264187257092836 | -53.60068129930135 | 1.768207077429036 | -50.9962546571975 | -36.68560191727209 | -7.336494042208514 | 16.915079382029262 | True | 31986 | 49501.47 | 54.759801163008824 | False | 1.6710041064327616 | 5 | False |
| no_spread_filter | optimistic | new3 | -50.337991965724086 | -59.59194847609296 | 1.4642098873546967 | -57.14951749688152 | -37.92753565162088 | -9.253956510368873 | 21.66441282447208 | True | 49921 | 109558.37 | 119.46349231786222 | False | 5.579584947541743 | 5 | True |
| no_spread_filter | optimistic | new4 | -42.38822335525453 | -53.56073095454723 | 2.203749611002204 | -50.19778338944118 | -27.040648422424827 | -11.1725075992927 | 26.520082532122405 | True | 26405 | 43947.37 | 66.43578867638705 | False | 5.776545937011128 | 3 | True |
| spread_ge_2 | pessimistic | val | -6.405840594128624 | -16.768994045713356 | 2.65770101829219 | -12.640824652613647 | -2.227239714128899 | -10.363153451584733 | 14.541754331584457 | True | 18846 | 33860.02 | 79.66687891329724 | False | 2.221569624645091 | 5 | False |
| spread_ge_2 | pessimistic | new3 | -21.259357836105114 | -40.53718779870103 | 2.2269564458268807 | -37.10257122975787 | -22.690403665646453 | -19.277829962595913 | 17.846784133054573 | True | 26700 | 81492.44 | 205.21513108614232 | False | 2.547745814081908 | 5 | False |
| spread_ge_2 | pessimistic | new4 | -12.335898705081945 | -33.73769278747912 | 3.1535072189593585 | -28.944568940443236 | 9.825592005047053 | -21.401794082397174 | 43.563284792526176 | True | 14951 | 31514.74 | 110.78683700086951 | False | 4.417532311304273 | 3 | True |
| spread_ge_2 | optimistic | val | -4.329801252553402 | -13.115358235093998 | 2.654475772710028 | -8.898334306173048 | 11.419079491437083 | -8.785556982540596 | 24.53443772653108 | True | 19966 | 34557.89 | 73.08369227687068 | False | 2.2011521202455495 | 5 | False |
| spread_ge_2 | optimistic | new3 | -17.895465395527253 | -30.826937655929264 | 2.0666028771447196 | -27.52775260660174 | 5.598065948138928 | -12.93147226040201 | 36.425003604068195 | True | 32426 | 85102.02 | 162.44994757293532 | False | 11.586756680939981 | 5 | True |
| spread_ge_2 | optimistic | new4 | -7.997178878224176 | -21.540934289737514 | 3.1481325424646465 | -16.625135473179462 | 27.443184381700437 | -13.543755411513338 | 48.984118671437955 | True | 17146 | 32802.41 | 91.31231774174736 | False | 4.853892405591983 | 3 | True |

## Session-clustered paired tests

| config | bound | split | session_count | paired_session_differences | difference_mean | difference_std | se_clustered | t | critical | signal_significantly_better |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_spread_filter | pessimistic | val | 6 | 12.7535433142;17.9732906354;-24.1429929426;38.6687056145;-10.3294128644;39.4829986116 | 12.401022061444955 | 25.716674769220923 | 10.498788510949602 | 1.1811860052720786 | 2.5705818356 | False |
| no_spread_filter | pessimistic | new3 | 6 | 16.8591308545;10.4009708305;-7.26442081475;-6.05925849009;-9.36246810513;39.751752092 | 7.387617727822016 | 19.09079956342668 | 7.793786285357204 | 0.9478855921032516 | 2.5705818356 | False |
| no_spread_filter | pessimistic | new4 | 4 | 34.1082485977;27.9573795947;9.95768994138;13.3180140703 | 21.335333051035413 | 11.557494514520696 | 5.778747257260348 | 3.6920342941508575 | 3.1824463053 | True |
| no_spread_filter | optimistic | val | 6 | 19.6656647648;33.1954595455;-22.0791004452;35.5886849914;-4.01992432789;39.1396917635 | 16.91507938202926 | 24.79545878142406 | 10.122703658783553 | 1.6710041064327616 | 2.5705818356 | False |
| no_spread_filter | optimistic | new3 | 6 | 25.0162879969;25.7447479731;16.4207283299;8.53996318455;18.0534081287;36.2113413337 | 21.664412824472084 | 9.51087894456108 | 3.882800069925811 | 5.579584947541743 | 2.5705818356 | True |
| no_spread_filter | optimistic | new4 | 4 | 37.6175620451;30.4203990007;17.9981622153;20.0442068675 | 26.5200825321224 | 9.181986197739576 | 4.590993098869788 | 5.776545937011128 | 3.1824463053 | True |
| spread_ge_2 | pessimistic | val | 6 | 12.7280027942;22.0100653605;-15.2708130064;31.6245777675;14.8634680552;21.2952250185 | 14.541754331584459 | 16.03365372038676 | 6.545711721237452 | 2.221569624645091 | 2.5705818356 | False |
| spread_ge_2 | pessimistic | new3 | 6 | 32.0049299689;19.3055008806;2.06015232158;8.20951975738;1.78238113827;43.7182207315 | 17.84678413305458 | 17.15850711399789 | 7.004931196201671 | 2.547745814081908 | 2.5705818356 | False |
| spread_ge_2 | pessimistic | new4 | 4 | 39.2254355131;72.2176757749;27.4401197617;35.3699081203 | 43.56328479252616 | 19.72290488110279 | 9.861452440551394 | 4.417532311304273 | 3.1824463053 | True |
| spread_ge_2 | optimistic | val | 6 | 69.1267205885;25.618048869;-15.0553620893;31.870021519;14.2014315051;21.4457659668 | 24.53443772653108 | 27.30245356662874 | 11.146179994045182 | 2.2011521202455495 | 2.5705818356 | False |
| spread_ge_2 | optimistic | new3 | 6 | 46.2272020077;44.6692291995;36.9251030391;26.8261045871;31.8751147983;32.0272679927 | 36.4250036040682 | 7.700400997957878 | 3.1436755433025287 | 11.586756680939981 | 2.5705818356 | True |
| spread_ge_2 | optimistic | new4 | 4 | 44.6907905211;78.6347776541;37.5347158735;35.0761906371 | 48.984118671437955 | 20.183438188702013 | 10.091719094351006 | 4.853892405591983 | 3.1824463053 | True |

## Exact 10A headline decomposition

| config | bound | symmetric_pnl_per_fill | random_mean_pnl_per_fill | random_std | random_p95 | signal_pnl_per_fill | original_10a_signal_minus_symmetric | mechanical_less_quoting_contribution | signal_information_contribution | signal_beats_random_95p | signal_fill_count | random_mean_fill_count | fill_count_gap_percent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_10a_cap1_two_sessions | pessimistic | -47.350885341074026 | -61.21705784838466 | 1.42218564592397 | -59.11591654223213 | -30.58563911924507 | 16.765246221828956 | -13.866172507310637 | 30.631418729139593 | True | 13988 | 21563.66 | 54.158278524449535 |
| legacy_10a_cap1_two_sessions | optimistic | -45.24150842945873 | -52.43063814996671 | 1.3187473657596076 | -50.11723233618347 | -18.505138833532623 | 26.73636959592611 | -7.189129720507978 | 33.925499316434085 | True | 15054 | 22199.94 | 47.46871263451574 |

Fill-rate matched at every main comparison: `False`. Verdict: `cannot_claim`.

The random control produced 54.76% to 205.22% more fills than signal skew across the main comparisons. Signal skew therefore suppresses the model-identified worse, fill-prone side more often than an independent 50/50 retreat. The P&L gap mixes this selection-rate effect with information and is not a matched-rate causal estimate.

Signal exceeded the random 95th percentile in 12/12 comparisons, but only 6/12 session-clustered tests were significant. Both the preregistered fill-rate and clustered-inference gates were therefore not met.

The exact 10A +16.77/+26.74 headline used cap=1 and two pilot sessions; it is therefore decomposed separately rather than being conflated with the cap=3 all-session analysis.

For the exact headline, the arithmetic decompositions are +16.765 = -13.866 mechanical +30.631 signal (pessimistic) and +26.736 = -7.189 mechanical +33.925 signal (optimistic). Because fill-count gaps are 54.16% and 47.47%, these are descriptive identities, not valid matched-rate causal attributions.

No model was retrained, NEW5 was not loaded, and all inference used continuous events with session-end marking only.
