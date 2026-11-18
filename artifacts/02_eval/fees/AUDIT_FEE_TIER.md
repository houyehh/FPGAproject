# 11C Endogenous Fee-Tier Audit

status: resolved_negative

## Stage 0: official-rule finding

The current TAIFEX futures market-maker product list does not include TX/TXF. It lists BRF, BTF, E4F, G2F, GDF, M1F, SHF, SOF, STF, TGF, and XIF. The general market-maker rules require contract-specific quote method, timing, minimum size, and maximum spread compliance, but no current TXF specification or TXF maintenance cost was found in the public documents.

`MM_ELIGIBILITY_VIOLATED: true`. The 4 h/80% and 5 h/100% reduction schedule found in product-specific documents cannot be transferred to TXF. Eligible applicants in general are approved futures proprietary firms and specified legal entities, but entity eligibility does not make an undesignated contract eligible.

Official sources:

- https://www.taifex.com.tw/cht/4/marketMakerAndProductDetail
- https://www.taifex.com.tw/cht/4/marketMakerOpRule
- https://www.taifex.com.tw/cht/4/marketMechanisms

## Stage 1: frozen 11B quote behavior

The frozen 11B seed-1 checkpoint and `tau=-16.799044036865237` were evaluated continuously on all 16 sessions without retraining or threshold reselection.

| split | sessions | mean simultaneous two-sided quote hours | mean any-side quote hours | mean longest continuous two-sided interval | interruptions |
|---|---:|---:|---:|---:|---:|
| val | 6 | 1.0826 | 2.2858 | 0.6345 h | 70,162 |
| NEW3 | 6 | 1.2287 | 2.5727 | 0.0450 h | 177,609 |
| NEW4 | 4 | 0.6002 | 1.3072 | 0.0438 h | 66,303 |

Only one session reached four hours of simultaneous two-sided quoting (`20260126Night`, 4.3896 h). Quote interruptions were frequent; most longest continuous two-sided intervals were measured in seconds or minutes rather than hours.

Measurement boundary: `20260123Night` and `20260126Night` each contained one negative timestamp delta. Those two intervals were clipped to zero when accumulating quote duration. This caveat affects the precision of the duration diagnostic, but not the regulatory finding that TXF is absent from the current designated-product list.

- `ACHIEVED_TIER: not_applicable_TXF_not_designated`
- `ACHIEVED_REDUCTION: not_applicable`
- `ENDOGENOUS_FEE: not_applicable`
- `STILL_PROFITABLE: no` under an applicable demonstrated fee tier

The 11B task-quality result remains valid: the toxicity model significantly improves on symmetric quoting. Its **economic profitability claim does not remain valid**, because it was positive only under a market-maker fee scenario that is not available for TXF under the current public product list. Under the proprietary fee scenario, 11B was not significantly profitable; under retail fees it was negative.

## Stage 2: commitment sweep

Stage 2 is `blocked_by_regulatory_non_identification`. No official TXF tier or fee function exists to map `K` to an endogenous fee. Running the sweep with another contract's schedule would create a hypothetical result while presenting it as an exchange-rule result, so it was not done.

- `BEST_K: not_measured`
- `TRADEOFF_EXISTS: not_measured`
- `BRACKET_SIGN_STABLE: not_measured`

## Verdict

`VERDICT: 11B conclusion overturned` for economic profitability. The model's predictive and relative-to-symmetric advantage survives; the claim that it is profitable at an attainable TXF market-maker fee does not.

NEW5 was not loaded. Existing 11B artifacts and the frozen checkpoint were hash-checked and unchanged.
