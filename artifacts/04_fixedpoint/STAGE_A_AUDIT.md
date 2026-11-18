# 13B Stage A Audit

status: failed_hard_gate

## Measured Format

- Float state max abs: `12.1217794418`
- Float state abs p99.99: `8.08861237049`
- Candidate storage: `ap_fixed<24,5>`; measured headroom `31.9938%`
- Candidate hidden multiplier operand: `ap_fixed<18,5>`; measured headroom `31.9928%`
- Input remained separately typed as `ap_fixed<24,12>`

## Gates

| Gate | Required | Measured | Result |
| --- | --- | --- | --- |
| Candidate runtime saturation | 0 | state storage 0 + hidden operand 3 = 3 | FAIL |
| Absolute P&L retention | >= 85.69% | 85.1130251% | FAIL |
| Significant on all splits | yes | yes; all 12 config/bound/split rows pass | PASS |
| Tau fold flips | 0 | 0 / 20,852,994 | PASS |
| Helper equivalence | 0 score/state mismatches | 0 / 0, max 0 / 0 LSB | PASS |

## Decision

The candidate improves state-storage resolution from 12 to 19 fractional bits but does not improve task retention. It is 0.5769749 percentage points below the pre-registered absolute-retention floor. Three hidden-operand casts also saturate, while state storage itself has zero saturation. The existing 12C storage/hidden formats remain the selected fallback, but the failed Stage A gates require stopping before HLS. No "close enough" exception was used.

No HLS, CSim, cosim, route, bitstream generation, or board access was performed.
