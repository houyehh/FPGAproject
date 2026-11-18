"""Decompose the model's improvement over symmetric quoting into capture and mark-movement.

Reads the per-session deterministic results produced by phase 16A and writes, for every
(rule, split) cell, the pooled fill-weighted per-fill capture and mark movement of both
strategies and the difference between them.

Two estimands are produced for every cell:
  pooled          - fill-weighted per-fill means over all sessions, model minus symmetric
  session_paired  - per-session differences averaged with equal weight per session

The session-paired total matches the statistic used for the significance tests in report
section 4.5, so the report quotes the session-paired decomposition.

Usage:
    python 01_decompose_improvement.py --input <16a deterministic_all.csv> --output <csv>
"""
import argparse, csv
from collections import defaultdict


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--config", default="no_spread_filter")
    args = ap.parse_args()

    agg = defaultdict(lambda: {"capture": 0.0, "gross": 0.0, "fills": 0})
    with open(args.input, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["config"] != args.config:
                continue
            key = (row["rule"], row["split"], row["strategy"])
            agg[key]["capture"] += float(row["capture_total"])
            agg[key]["gross"] += float(row["gross_pnl"])
            agg[key]["fills"] += int(row["fill_count"])

    # per-session per-fill values, for the session-paired estimand
    per = defaultdict(dict)
    with open(args.input, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["config"] != args.config:
                continue
            n = int(row["fill_count"])
            if not n:
                continue
            cap = float(row["capture_total"]) / n
            gross = float(row["gross_pnl"]) / n
            per[(row["rule"], row["split"], row["session"])][row["strategy"]] = (cap, gross - cap)

    rules = ["back", "proportional", "front"]
    splits = ["val", "new3", "new4"]
    out = []
    for rule in rules:
        for split in splits:
            s = agg[(rule, split, "symmetric")]
            m = agg[(rule, split, "model_11b")]
            if not s["fills"] or not m["fills"]:
                continue
            s_cap, m_cap = s["capture"] / s["fills"], m["capture"] / m["fills"]
            s_gross, m_gross = s["gross"] / s["fills"], m["gross"] / m["fills"]
            p_total = m_gross - s_gross
            p_cap = m_cap - s_cap
            dc, dm = [], []
            for (r2, sp2, _sess), v in per.items():
                if (r2, sp2) != (rule, split) or len(v) < 2:
                    continue
                dc.append(v["model_11b"][0] - v["symmetric"][0])
                dm.append(v["model_11b"][1] - v["symmetric"][1])
            n_sess = len(dc)
            sp_cap = sum(dc) / n_sess
            sp_mark = sum(dm) / n_sess
            sp_total = sp_cap + sp_mark
            out.append({
                "rule": rule, "split": split, "config": args.config, "sessions": n_sess,
                "pooled_total_improvement": round(p_total, 6),
                "pooled_capture_contribution": round(p_cap, 6),
                "pooled_mark_movement_contribution": round(p_total - p_cap, 6),
                "session_paired_total_improvement": round(sp_total, 6),
                "session_paired_capture_contribution": round(sp_cap, 6),
                "session_paired_mark_movement_contribution": round(sp_mark, 6),
                "session_paired_capture_share_pct": round(sp_cap / sp_total * 100, 2),
                "additive_check_session_paired": round(sp_cap + sp_mark - sp_total, 9),
            })

    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    print(f"rows: {len(out)}")
    print("max additive residual (session-paired): %.3e" % max(
        abs(r["additive_check_session_paired"]) for r in out))
    print("session-paired capture share: %.2f%% to %.2f%%" % (
        min(r["session_paired_capture_share_pct"] for r in out),
        max(r["session_paired_capture_share_pct"] for r in out)))
    print("both contributions positive in every cell: %s" % all(
        r["session_paired_capture_contribution"] > 0
        and r["session_paired_mark_movement_contribution"] > 0 for r in out))


if __name__ == "__main__":
    main()
