# 10E Perfect-Foresight Ceiling

status: action_space_problem

`oracle_uses_future_labels: true`; `post_hoc_diagnostic_only: true`. Future H20 labels select the action only. Realized P&L uses queue fills, placement-mid capture, and the simulator's session-end inventory mark.

## Five baselines

| config | bound | split | strategy | fills | capture_per_fill | markout_per_fill | pnl_per_fill_market_maker | roundtrip_net_twd | underpowered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_spread_filter | optimistic | new3 | symmetric | 220273.0 | 251.57872276674854 | -172.38154471950716 | -48.142821952758624 | -96.28564390551725 | False |
| no_spread_filter | optimistic | new3 | random_skew | 109558.37 | 242.5692457432399 | -170.99910919412594 | -55.76986345088606 | -111.53972690177211 | False |
| no_spread_filter | optimistic | new3 | model_skew | 49921.0 | 280.96191983333665 | -190.4529156066585 | -36.830995773321845 | -73.66199154664369 | False |
| no_spread_filter | optimistic | new3 | perfect_a_retreat | 76558.0 | 281.05227409284464 | -38.78105488649129 | 114.93121920635335 | 229.8624384127067 | False |
| no_spread_filter | optimistic | new3 | perfect_b_cancel | 53414.0 | 230.46392331598457 | 79.66450743250833 | 182.7884307484929 | 365.5768614969858 | False |
| no_spread_filter | optimistic | new4 | symmetric | 90342.0 | 243.36742600340926 | -164.78824909787252 | -48.76082309446326 | -97.52164618892652 | False |
| no_spread_filter | optimistic | new4 | random_skew | 43947.37 | 236.4648799817457 | -170.34351457842044 | -61.21863459667475 | -122.4372691933495 | False |
| no_spread_filter | optimistic | new4 | model_skew | 26405.0 | 255.72429464116644 | -164.00302972921796 | -35.61873508805151 | -71.23747017610302 | False |
| no_spread_filter | optimistic | new4 | perfect_a_retreat | 38302.0 | 259.04391415591874 | -54.790872539292984 | 76.91304161662575 | 153.8260832332515 | False |
| no_spread_filter | optimistic | new4 | perfect_b_cancel | 29745.0 | 217.7475205916961 | 29.107413010590015 | 119.5149336022861 | 239.0298672045722 | False |
| no_spread_filter | optimistic | val | symmetric | 101910.0 | 214.90138357374153 | -132.80737905995485 | -45.24599548621333 | -90.49199097242666 | False |
| no_spread_filter | optimistic | val | random_skew | 49501.47 | 200.78127711215768 | -125.60653491750189 | -52.16525780534419 | -104.33051561068838 | False |
| no_spread_filter | optimistic | val | model_skew | 31986.0 | 211.76764834615145 | -110.20133808541237 | -25.77368973926093 | -51.54737947852186 | False |
| no_spread_filter | optimistic | val | perfect_a_retreat | 48889.0 | 217.99177729141525 | -28.19448137617869 | 62.45729591523656 | 124.91459183047311 | False |
| no_spread_filter | optimistic | val | perfect_b_cancel | 42985.0 | 198.54135163429103 | 7.465394905199489 | 78.6667465394905 | 157.333493078981 | False |
| no_spread_filter | pessimistic | new3 | symmetric | 213588.0 | 251.34604940352455 | -174.98127235612486 | -50.97522295260033 | -101.95044590520067 | False |
| no_spread_filter | pessimistic | new3 | random_skew | 104698.74 | 234.80281863180565 | -174.60837981704094 | -67.14556118523535 | -134.2911223704707 | False |
| no_spread_filter | pessimistic | new3 | model_skew | 42482.0 | 258.90730191610567 | -196.33256438020808 | -64.76526246410245 | -129.5305249282049 | False |
| no_spread_filter | pessimistic | new3 | perfect_a_retreat | 68404.0 | 270.12309221682943 | -22.245775100871295 | 120.53731711595813 | 241.07463423191626 | False |
| no_spread_filter | pessimistic | new3 | perfect_b_cancel | 51694.0 | 229.47150539714474 | 78.75382055944597 | 180.88532595659072 | 361.77065191318144 | False |
| no_spread_filter | pessimistic | new4 | symmetric | 87456.0 | 243.2628979143798 | -168.1531284302964 | -52.230230515916574 | -104.46046103183315 | False |
| no_spread_filter | pessimistic | new4 | random_skew | 42171.06 | 229.0485526063712 | -172.88819439081462 | -71.17964178444333 | -142.35928356888667 | False |
| no_spread_filter | pessimistic | new4 | model_skew | 23560.0 | 238.45076400679116 | -161.65959252971138 | -50.5488285229202 | -101.0976570458404 | False |
| no_spread_filter | pessimistic | new4 | perfect_a_retreat | 35190.0 | 249.46575731741973 | -41.75618073316283 | 80.36957658425689 | 160.73915316851378 | False |
| no_spread_filter | pessimistic | new4 | perfect_b_cancel | 28985.0 | 216.7810936691392 | 26.368811454200447 | 115.80990512333966 | 231.61981024667932 | False |
| no_spread_filter | pessimistic | val | symmetric | 98703.0 | 215.02993829974773 | -134.11243832507623 | -46.42250002532852 | -92.84500005065703 | False |
| no_spread_filter | pessimistic | val | random_skew | 48043.45 | 196.1941313771969 | -125.84500884329422 | -56.99087746609737 | -113.98175493219475 | False |
| no_spread_filter | pessimistic | val | model_skew | 29690.0 | 201.52239811384305 | -104.9545301448299 | -30.772132030986867 | -61.544264061973735 | False |
| no_spread_filter | pessimistic | val | perfect_a_retreat | 46119.0 | 212.22923307096858 | -20.798369435590537 | 64.09086363537804 | 128.18172727075608 | False |
| no_spread_filter | pessimistic | val | perfect_b_cancel | 42139.0 | 197.94252355300316 | 5.545931322527824 | 76.14845487553097 | 152.29690975106195 | False |
| spread_ge_2 | optimistic | new3 | symmetric | 178569.0 | 275.6318285928689 | -165.9823373597881 | -17.690508766919237 | -35.381017533838474 | False |
| spread_ge_2 | optimistic | new3 | random_skew | 85102.02 | 268.6950152929059 | -167.90587828924123 | -26.550862996335294 | -53.10172599267059 | False |
| spread_ge_2 | optimistic | new3 | model_skew | 32426.0 | 318.9755134768396 | -181.17251588231665 | 10.462997594522903 | 20.925995189045807 | False |
| spread_ge_2 | optimistic | new3 | perfect_a_retreat | 57863.0 | 298.9457857352713 | -16.995316523512436 | 154.61046921175878 | 309.22093842351757 | False |
| spread_ge_2 | optimistic | new3 | perfect_b_cancel | 45302.0 | 253.22281576972318 | 78.25703059467573 | 204.1398463643989 | 408.2796927287978 | False |
| spread_ge_2 | optimistic | new4 | symmetric | 70071.0 | 271.2876939104622 | -160.53716944242268 | -16.589475531960446 | -33.17895106392089 | False |
| spread_ge_2 | optimistic | new4 | random_skew | 32802.41 | 266.44119763266275 | -170.72907458510002 | -31.62787695243725 | -63.2557539048745 | False |
| spread_ge_2 | optimistic | new4 | model_skew | 17146.0 | 294.8792721334422 | -158.5384346203196 | 9.000837513122605 | 18.00167502624521 | False |
| spread_ge_2 | optimistic | new4 | perfect_a_retreat | 27164.0 | 287.0600795170078 | -38.04667942865557 | 121.67340008835222 | 243.34680017670445 | False |
| spread_ge_2 | optimistic | new4 | perfect_b_cancel | 22491.0 | 249.16188697701304 | 41.425459072517896 | 163.24734604953093 | 326.49469209906187 | False |
| spread_ge_2 | optimistic | val | symmetric | 73768.0 | 240.2572931352348 | -114.39377507862488 | -1.4764819433900982 | -2.9529638867801964 | False |
| spread_ge_2 | optimistic | val | random_skew | 34557.89 | 227.87404497375405 | -111.13495114810736 | -10.600906174353357 | -21.201812348706714 | False |
| spread_ge_2 | optimistic | val | model_skew | 19966.0 | 236.2015426224582 | -91.03976760492837 | 17.821775017529802 | 35.643550035059604 | False |
| spread_ge_2 | optimistic | val | perfect_a_retreat | 34856.0 | 237.75246729400965 | -6.489557034656874 | 103.92291025935276 | 207.84582051870552 | False |
| spread_ge_2 | optimistic | val | perfect_b_cancel | 32666.0 | 225.60154288863038 | 11.853303128635279 | 110.11484601726565 | 220.2296920345313 | False |
| spread_ge_2 | pessimistic | new3 | symmetric | 172678.0 | 275.3987190029998 | -168.53391862310195 | -20.47519962010216 | -40.95039924020432 | False |
| spread_ge_2 | pessimistic | new3 | random_skew | 81492.44 | 261.0128022748147 | -170.45489747879807 | -36.7820952039833 | -73.5641904079666 | False |
| spread_ge_2 | pessimistic | new3 | model_skew | 26700.0 | 293.28464419475654 | -188.30711610486892 | -22.36247191011236 | -44.72494382022472 | False |
| spread_ge_2 | pessimistic | new3 | perfect_a_retreat | 51621.0 | 286.2439704771314 | 4.7441932546831715 | 163.64816373181455 | 327.2963274636291 | False |
| spread_ge_2 | pessimistic | new3 | perfect_b_cancel | 43770.0 | 252.61594699565913 | 77.40233036326251 | 202.67827735892163 | 405.35655471784327 | False |
| spread_ge_2 | pessimistic | new4 | symmetric | 67646.0 | 271.10989563314905 | -163.98900156698105 | -20.21910593383201 | -40.43821186766402 | False |
| spread_ge_2 | pessimistic | new4 | random_skew | 31514.74 | 259.07961688905647 | -172.3013998789604 | -40.561782989904 | -81.123565979808 | False |
| spread_ge_2 | pessimistic | new4 | model_skew | 14951.0 | 274.1087552672062 | -151.4815062537623 | -4.712750986556088 | -9.425501973112176 | False |
| spread_ge_2 | pessimistic | new4 | perfect_a_retreat | 24794.0 | 276.1595547309833 | -22.79583770267 | 126.02371702831329 | 252.04743405662657 | False |
| spread_ge_2 | pessimistic | new4 | perfect_b_cancel | 21825.0 | 248.4306987399771 | 37.97479954180985 | 159.06549828178694 | 318.1309965635739 | False |
| spread_ge_2 | pessimistic | val | symmetric | 71428.0 | 239.89611916895336 | -116.0329282634261 | -3.476809094472756 | -6.953618188945512 | False |
| spread_ge_2 | pessimistic | val | random_skew | 33860.02 | 224.3085576935932 | -110.58929321892165 | -13.620735525328453 | -27.241471050656905 | False |
| spread_ge_2 | pessimistic | val | model_skew | 18846.0 | 226.96593441579114 | -86.54356362092751 | 13.082370794863635 | 26.16474158972727 | False |
| spread_ge_2 | pessimistic | val | perfect_a_retreat | 33206.0 | 233.07233632476058 | -1.1955670661928568 | 104.53676925856772 | 209.07353851713543 | False |
| spread_ge_2 | pessimistic | val | perfect_b_cancel | 31924.0 | 225.23806540533766 | 10.625234932965794 | 108.52330033830347 | 217.04660067660694 | False |

## Session-clustered oracle tests

| config | bound | split | strategy | session_count | session_mean_pnl_per_fill | session_std | se_clustered | t_vs_zero | df | critical | significantly_positive | underpowered_sessions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_spread_filter | optimistic | new3 | perfect_a_retreat | 6 | 109.47602241655558 | 18.09159915045316 | 7.38586442492998 | 14.822370966766485 | 5 | 2.5705818356 | True | 0 |
| no_spread_filter | optimistic | new3 | perfect_b_cancel | 6 | 171.5407759649369 | 38.400333741776905 | 15.676870603322218 | 10.942284356712381 | 5 | 2.5705818356 | True | 0 |
| no_spread_filter | optimistic | new4 | perfect_a_retreat | 4 | 91.47619973770573 | 54.86407378823755 | 27.432036894118774 | 3.334648465616403 | 3 | 3.1824463053 | True | 0 |
| no_spread_filter | optimistic | new4 | perfect_b_cancel | 4 | 161.7104306657621 | 98.5882697976744 | 49.2941348988372 | 3.2805207150430524 | 3 | 3.1824463053 | True | 1 |
| no_spread_filter | optimistic | val | perfect_a_retreat | 6 | 75.93962435746879 | 33.636143779911315 | 13.731898195945496 | 5.530162201456668 | 5 | 2.5705818356 | True | 0 |
| no_spread_filter | optimistic | val | perfect_b_cancel | 6 | 114.40526210319301 | 60.39267502846234 | 24.655206336909384 | 4.640207043488654 | 5 | 2.5705818356 | True | 0 |
| no_spread_filter | pessimistic | new3 | perfect_a_retreat | 6 | 113.6303613494465 | 21.944995640229397 | 8.959006954360579 | 12.683365681967652 | 5 | 2.5705818356 | True | 0 |
| no_spread_filter | pessimistic | new3 | perfect_b_cancel | 6 | 169.6584115541105 | 37.44738282713675 | 15.287830021524401 | 11.097612369789632 | 5 | 2.5705818356 | True | 0 |
| no_spread_filter | pessimistic | new4 | perfect_a_retreat | 4 | 95.41414396668017 | 61.12109570751928 | 30.56054785375964 | 3.122134603844874 | 3 | 3.1824463053 | False | 0 |
| no_spread_filter | pessimistic | new4 | perfect_b_cancel | 4 | 158.48386589368704 | 98.87749286874606 | 49.43874643437303 | 3.2056610922379445 | 3 | 3.1824463053 | True | 1 |
| no_spread_filter | pessimistic | val | perfect_a_retreat | 6 | 82.09293834265522 | 38.331638653764706 | 15.648825951077974 | 5.245948712018247 | 5 | 2.5705818356 | True | 0 |
| no_spread_filter | pessimistic | val | perfect_b_cancel | 6 | 111.61076245623235 | 59.4205908496942 | 24.25835463274032 | 4.6009205548341985 | 5 | 2.5705818356 | True | 0 |
| spread_ge_2 | optimistic | new3 | perfect_a_retreat | 6 | 148.12096706113394 | 20.580868594162066 | 8.402104419828072 | 17.62903192580947 | 5 | 2.5705818356 | True | 0 |
| spread_ge_2 | optimistic | new3 | perfect_b_cancel | 6 | 191.36563015182162 | 42.70870666877032 | 17.43575648544807 | 10.97547045415184 | 5 | 2.5705818356 | True | 0 |
| spread_ge_2 | optimistic | new4 | perfect_a_retreat | 4 | 132.94383724571992 | 52.52591367431337 | 26.262956837156686 | 5.0620285472819155 | 3 | 3.1824463053 | True | 0 |
| spread_ge_2 | optimistic | new4 | perfect_b_cancel | 4 | 184.08319398666848 | 83.60107084111043 | 41.800535420555214 | 4.403847753015777 | 3 | 3.1824463053 | True | 1 |
| spread_ge_2 | optimistic | val | perfect_a_retreat | 6 | 116.04906363980172 | 33.27470843566356 | 13.584342834543133 | 8.542854450397465 | 5 | 2.5705818356 | True | 0 |
| spread_ge_2 | optimistic | val | perfect_b_cancel | 6 | 132.35645310694215 | 44.80213754620164 | 18.290396062363673 | 7.236390762433698 | 5 | 2.5705818356 | True | 0 |
| spread_ge_2 | pessimistic | new3 | perfect_a_retreat | 6 | 155.54371064067513 | 26.417219640247332 | 10.784784756939361 | 14.422514138781684 | 5 | 2.5705818356 | True | 0 |
| spread_ge_2 | pessimistic | new3 | perfect_b_cancel | 6 | 190.33109289937633 | 40.2941122746745 | 16.450002451894825 | 11.570277479043943 | 5 | 2.5705818356 | True | 0 |
| spread_ge_2 | pessimistic | new4 | perfect_a_retreat | 4 | 136.43364238680715 | 57.3437672167727 | 28.67188360838635 | 4.7584471341429815 | 3 | 3.1824463053 | True | 1 |
| spread_ge_2 | pessimistic | new4 | perfect_b_cancel | 4 | 178.42696317286877 | 83.14049508088615 | 41.57024754044308 | 4.292179472813575 | 3 | 3.1824463053 | True | 1 |
| spread_ge_2 | pessimistic | val | perfect_a_retreat | 6 | 121.15089868505886 | 39.184381707253195 | 15.996956844869585 | 7.573371601856475 | 5 | 2.5705818356 | True | 0 |
| spread_ge_2 | pessimistic | val | perfect_b_cancel | 6 | 130.7249465341079 | 46.004314460116476 | 18.781182732304526 | 6.960421417403856 | 5 | 2.5705818356 | True | 0 |

## Model share of ceiling

| config | bound | split | symmetric_pnl_per_fill | model_pnl_per_fill | perfect_a_pnl_per_fill | perfect_b_pnl_per_fill | model_gain_vs_symmetric | perfect_a_gain_vs_symmetric | perfect_b_gain_vs_symmetric | model_share_of_ceiling_a | model_share_of_ceiling_b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_spread_filter | optimistic | new3 | -48.142821952758624 | -36.830995773321845 | 114.93121920635335 | 182.7884307484929 | 11.311826179436778 | 163.07404115911197 | 230.93125270125154 | 0.06936619770402198 | 0.048983522356198926 |
| no_spread_filter | optimistic | new4 | -48.76082309446326 | -35.61873508805151 | 76.91304161662575 | 119.5149336022861 | 13.142088006411754 | 125.67386471108901 | 168.27575669674937 | 0.10457295983237272 | 0.07809852271290142 |
| no_spread_filter | optimistic | val | -45.24599548621333 | -25.77368973926093 | 62.45729591523656 | 78.6667465394905 | 19.4723057469524 | 107.70329140144989 | 123.91274202570384 | 0.18079582799723304 | 0.15714530587107148 |
| no_spread_filter | pessimistic | new3 | -50.97522295260033 | -64.76526246410245 | 120.53731711595813 | 180.88532595659072 | -13.790039511502115 | 171.51254006855845 | 231.86054890919104 | -0.08040251462656808 | -0.05947557519542935 |
| no_spread_filter | pessimistic | new4 | -52.230230515916574 | -50.5488285229202 | 80.36957658425689 | 115.80990512333966 | 1.6814019929963706 | 132.59980710017345 | 168.04013563925622 | 0.012680274804066222 | 0.01000595474765598 |
| no_spread_filter | pessimistic | val | -46.42250002532852 | -30.772132030986867 | 64.09086363537804 | 76.14845487553097 | 15.65036799434165 | 110.51336366070656 | 122.57095490085949 | 0.14161516287198303 | 0.12768414839388598 |
| spread_ge_2 | optimistic | new3 | -17.690508766919237 | 10.462997594522903 | 154.61046921175878 | 204.1398463643989 | 28.15350636144214 | 172.30097797867802 | 221.83035513131813 | 0.16339725224848167 | 0.1269145800392194 |
| spread_ge_2 | optimistic | new4 | -16.589475531960446 | 9.000837513122605 | 121.67340008835222 | 163.24734604953093 | 25.59031304508305 | 138.26287562031268 | 179.8368215814914 | 0.18508448439447536 | 0.1422974050588802 |
| spread_ge_2 | optimistic | val | -1.4764819433900982 | 17.821775017529802 | 103.92291025935276 | 110.11484601726565 | 19.2982569609199 | 105.39939220274286 | 111.59132796065575 | 0.18309647292650794 | 0.17293688778149474 |
| spread_ge_2 | pessimistic | new3 | -20.47519962010216 | -22.36247191011236 | 163.64816373181455 | 202.67827735892163 | -1.887272290010202 | 184.1233633519167 | 223.1534769790238 | -0.010250042447915969 | -0.008457283819008581 |
| spread_ge_2 | pessimistic | new4 | -20.21910593383201 | -4.712750986556088 | 126.02371702831329 | 159.06549828178694 | 15.506354947275923 | 146.24282296214528 | 179.28460421561897 | 0.10603156198160725 | 0.08649016470274828 |
| spread_ge_2 | pessimistic | val | -3.476809094472756 | 13.082370794863635 | 104.53676925856772 | 108.52330033830347 | 16.55917988933639 | 108.01357835304047 | 112.00010943277623 | 0.15330646518545107 | 0.14784967597978468 |

## Tail removal

| config | bound | split | strategy | fill_count | removed_count | original_pnl_per_fill | trimmed_pnl_per_fill | original_positive | trimmed_positive | robust_to_tail_removal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_spread_filter | pessimistic | val | perfect_a_retreat | 46119 | 462 | 64.09086363537875 | 42.32292134831525 | True | True | True |
| no_spread_filter | pessimistic | val | perfect_b_cancel | 42139 | 422 | 76.14845487553175 | 42.7537267780528 | True | True | True |
| no_spread_filter | optimistic | val | perfect_a_retreat | 48889 | 489 | 62.45729591523728 | 45.098016528926294 | True | True | True |
| no_spread_filter | optimistic | val | perfect_b_cancel | 42985 | 430 | 78.66674653949127 | 45.98158383268781 | True | True | True |
| spread_ge_2 | pessimistic | val | perfect_a_retreat | 33206 | 333 | 104.53676925856846 | 85.68892951662528 | True | True | True |
| spread_ge_2 | pessimistic | val | perfect_b_cancel | 31924 | 320 | 108.52330033830422 | 74.62494114669099 | True | True | True |
| spread_ge_2 | optimistic | val | perfect_a_retreat | 34856 | 349 | 103.92291025935349 | 80.17441736459334 | True | True | True |
| spread_ge_2 | optimistic | val | perfect_b_cancel | 32666 | 327 | 110.11484601726637 | 84.90218435944281 | True | True | True |
| no_spread_filter | pessimistic | new3 | perfect_a_retreat | 68404 | 685 | 120.53731711595984 | 101.25463370693772 | True | True | True |
| no_spread_filter | pessimistic | new3 | perfect_b_cancel | 51694 | 517 | 180.88532595659234 | 155.2478812747931 | True | True | True |
| no_spread_filter | optimistic | new3 | perfect_a_retreat | 76558 | 766 | 114.93121920635512 | 95.03043487439471 | True | True | True |
| no_spread_filter | optimistic | new3 | perfect_b_cancel | 53414 | 535 | 182.7884307484945 | 157.95283836683913 | True | True | True |
| spread_ge_2 | pessimistic | new3 | perfect_a_retreat | 51621 | 517 | 163.64816373181634 | 153.3151346274282 | True | True | True |
| spread_ge_2 | pessimistic | new3 | perfect_b_cancel | 43770 | 438 | 202.6782773589233 | 164.91745407551164 | True | True | True |
| spread_ge_2 | optimistic | new3 | perfect_a_retreat | 57863 | 579 | 154.61046921176066 | 138.45324069548388 | True | True | True |
| spread_ge_2 | optimistic | new3 | perfect_b_cancel | 45302 | 454 | 204.13984636440063 | 164.69308954691573 | True | True | True |
| no_spread_filter | pessimistic | new4 | perfect_a_retreat | 35190 | 352 | 80.36957658425911 | 75.67107985533248 | True | True | True |
| no_spread_filter | pessimistic | new4 | perfect_b_cancel | 28985 | 290 | 115.80990512334189 | 53.12698031016074 | True | True | True |
| no_spread_filter | optimistic | new4 | perfect_a_retreat | 38302 | 384 | 76.9130416166279 | 80.05226752466056 | True | True | True |
| no_spread_filter | optimistic | new4 | perfect_b_cancel | 29745 | 298 | 119.51493360228825 | 78.15122151662523 | True | True | True |
| spread_ge_2 | pessimistic | new4 | perfect_a_retreat | 24794 | 248 | 126.02371702831537 | 101.05159129797333 | True | True | True |
| spread_ge_2 | pessimistic | new4 | perfect_b_cancel | 21825 | 219 | 159.06549828178902 | 133.40701471813608 | True | True | True |
| spread_ge_2 | optimistic | new4 | perfect_a_retreat | 27164 | 272 | 121.67340008835437 | 114.94766919530176 | True | True | True |
| spread_ge_2 | optimistic | new4 | perfect_b_cancel | 22491 | 225 | 163.2473460495331 | 138.23531662624853 | True | True | True |

Bracket sign stable: `True`; unstable cases: `none`.

Perfect A profitable under the preregistered all-split clustered gate: `False`. Perfect B: `True`.

Perfect A is economically positive in all 12 aggregate cells but clears the session-clustered significance gate in 11/12; its sole miss is no-spread/pessimistic/NEW4 (t=3.122 versus 3.182). Perfect B clears 12/12. No perfect-B aggregate is underpowered (minimum split/bracket fill count 21,825).

Across full sessions with no spread filter, current model mark movement is -318.9 to -320.6 TWD/roundtrip, Perfect A reduces it to -52.8 to -78.7, and Perfect B turns it positive at +82.5 to +86.3. Thus the oracle space is large, but most of it requires cancellation rather than merely retreating one tick.

The model share of the oracle gain is -8.04% to 18.51% for Perfect A and -5.95% to 17.29% for Perfect B across the preregistered split/bracket/config cells. Negative shares occur where model skew underperforms symmetric quoting.

Every positive oracle cell remains positive after removing the largest 1% absolute fill contributions: `True`.

Verdict: `action_space_problem`. Recommendation: Add a cancel action before investing in new features.

No model was retrained, NEW5 was not loaded, and existing phase artifacts were not modified.
