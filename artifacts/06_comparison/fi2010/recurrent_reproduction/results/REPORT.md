# 15A FI-2010 Recurrent Tier2/Tier3 Reproduction

RESULT: PASS

## Parameter gate

- Tier2 recurrent width 16: 2,132 trainable parameters (expected 2,132).
- Tier3 recurrent width 64: 23,876 trainable parameters (expected 23,876).
- Parameter count matches: yes.

## Runs

| Tier | Seed | Best epoch | Stop epoch | Stop reason | Test macro-F1 |
|---:|---:|---:|---:|---|---:|
| 2 | 0 | 32 | 42 | early_stopping_triggered | 0.631563362 |
| 2 | 1 | 51 | 61 | early_stopping_triggered | 0.634384884 |
| 2 | 2 | 75 | 85 | early_stopping_triggered | 0.654723330 |
| 3 | 0 | 16 | 26 | early_stopping_triggered | 0.647279396 |
| 3 | 1 | 18 | 28 | early_stopping_triggered | 0.640077649 |
| 3 | 2 | 29 | 39 | early_stopping_triggered | 0.626777815 |

All six `stop_epoch` values are numeric and all six runs stopped through the fixed patience-10 early-stopping rule.

## Reproduction test

| Tier | New mean | New std | Old mean | Old std | Mean delta | Within old seed std |
|---:|---:|---:|---:|---:|---:|---|
| 2 | 0.640223858 | 0.012635911 | 0.639748000 | 0.014473000 | +0.000475858 | true |
| 3 | 0.638044953 | 0.010400846 | 0.638786000 | 0.005484000 | -0.000741047 | true |

REPRODUCED_WITHIN_SEED_NOISE: yes

Both tiers reproduce within the preregistered boundary. The FI-2010 section may retain its conclusion, but should cite these traceable runs.

## Paired comparison against existing feedforward artifacts

| Tier | Seed0 diff | Seed1 diff | Seed2 diff | Mean diff | Std diff | Paired t | Significant (df=2, critical=4.302653) | Winner |
|---:|---:|---:|---:|---:|---:|---:|---|---|
| 2 | -0.012962628 | -0.006048403 | +0.021238275 | +0.000742415 | 0.018083469 | 0.071109 | false | recurrent |
| 3 | -0.061942245 | -0.073337404 | -0.087487038 | -0.074255562 | 0.012797123 | -10.050259 | true | feedforward |

TIER3_FEEDFORWARD_STILL_WINS: yes

Tier3 remains significantly in favor of feedforward (paired t = -10.050259). Tier2 is indistinguishable (paired t = 0.071109).

## Artifacts

- Required run artifacts: 18/18.
- Checkpoints: 6; curves: 6; metrics JSON files: 6.
- SHA-256 inventory: `artifact_sha256.csv`.
- Existing `09j/results/track_b` files were read only and not overwritten.
- NEW5 used: no.

VERDICT: Confirm existing conclusion with the new traceable executions.
