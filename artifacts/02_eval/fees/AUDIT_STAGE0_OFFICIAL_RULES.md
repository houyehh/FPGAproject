# 11C Stage 0 Official Rule Audit

status: resolved_ineligible

Checked on 2026-11-13 against current TAIFEX public pages.

| Item | Finding | Official source |
|---|---|---|
| TX/TXF market-making eligibility | **Not listed.** The current futures market-maker product table lists BRF, BTF, E4F, G2F, GDF, M1F, SHF, SOF, STF, TGF, and XIF, but not TX/TXF. | https://www.taifex.com.tw/cht/4/marketMakerAndProductDetail |
| Continuous-quote thresholds and reductions for TXF | `not_found_in_public_docs`; no applicable TXF row exists in the current product-specific rules. The frequently cited 4 h/80% and 5 h/100% schedule belongs to specified contracts and cannot be transferred to TXF. | https://www.taifex.com.tw/cht/4/marketMechanisms |
| Definition of continuous quoting for TXF | `not_found_in_public_docs` because TXF is not a designated market-making contract in the current list. | same as above |
| Reduced volume scope | The general rule defines market-making volume as quote executions plus limited non-quote executions; reductions apply only when contract-specific obligations are met. A TXF-specific scope was not found. | https://www.taifex.com.tw/cht/4/marketMakerOpRule (Article 9) |
| Maximum spread/minimum size/two-sided duty for TXF | `not_found_in_public_docs`; general Article 6 requires contract-specific quote method, timing, size, and spread compliance, but no current TXF specification was found. | https://www.taifex.com.tw/cht/4/marketMakerOpRule (Article 6) |
| Product maintenance cost for TXF | `not_found_in_public_docs`. Historic attachments contain contract-specific costs for other products; they are not evidence for TXF. | https://www.taifex.com.tw/cht/4/marketMechanisms |
| Eligible entities | Futures proprietary firms and qualified specified legal entities may apply, subject to TAIFEX approval, designated contracts, internal controls, and required filings. | https://www.taifex.com.tw/cht/4/marketMakerOpRule (Article 2) |

`MM_ELIGIBILITY_VIOLATED: true` for the experiment's TXFA6/TXFB6 instrument. The market-maker fee assumed by 11B is therefore not an attainable endogenous tier under the current public TXF rules. It remains a hypothetical cost scenario only.

Consequences for later stages:

- Quote-time behavior can still be measured in Stage 1.
- `ACHIEVED_TIER`, `ACHIEVED_REDUCTION`, and `ENDOGENOUS_FEE` must be `not_applicable` rather than inferred from another product.
- The fee-tier commitment sweep in Stage 2 is not identified by official TXF rules and must not be presented as an empirical TAIFEX result.
