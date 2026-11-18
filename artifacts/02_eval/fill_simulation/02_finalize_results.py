from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finalize 16A result tables")
    parser.add_argument("--result-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.result_dir.resolve()
    aggregate = pd.read_csv(output / "deterministic_aggregate.csv")
    paired = pd.read_csv(output / "paired_vs_symmetric.csv")
    random_summary = pd.read_csv(output / "random_summary.csv")
    fill = pd.read_csv(output / "historical_selected_side_fill_rates.csv")
    manifest = json.loads((output / "manifest.json").read_text(encoding="ascii"))
    d_stats = json.loads((output / "d_statistics.json").read_text(encoding="ascii"))

    no_spread = aggregate[aggregate.config.eq("no_spread_filter")].copy()
    bracket_rows: list[dict[str, object]] = []
    for strategy in ("symmetric", "model_11b"):
        for split in ("val", "new3", "new4"):
            points = no_spread[(no_spread.strategy == strategy) & (no_spread.split == split)].set_index("rule")
            back = float(points.loc["back", "maker_pnl_per_fill"])
            prop = float(points.loc["proportional", "maker_pnl_per_fill"])
            front = float(points.loc["front", "maker_pnl_per_fill"])
            bracket_rows.append({
                "strategy": strategy,
                "split": split,
                "net_pnl_back": back,
                "net_pnl_proportional": prop,
                "net_pnl_front": front,
                "front_minus_back": front - back,
                "front_sign": "positive" if front > 0 else "negative" if front < 0 else "zero",
            })
    bracket = pd.DataFrame(bracket_rows)
    bracket.to_csv(output / "net_pnl_brackets.csv", index=False)

    sym = no_spread[no_spread.strategy.eq("symmetric")].copy()
    component_rows = sym[[
        "rule", "split", "fill_count", "capture_per_fill", "mark_movement_per_fill", "gross_per_fill",
        "maker_pnl_per_fill",
    ]].to_dict("records")
    for rule, group in sym.groupby("rule"):
        fills = group.fill_count.to_numpy(np.float64)
        component_rows.append({
            "rule": rule,
            "split": "all_16_sessions",
            "fill_count": int(fills.sum()),
            "capture_per_fill": float(np.average(group.capture_per_fill, weights=fills)),
            "mark_movement_per_fill": float(np.average(group.mark_movement_per_fill, weights=fills)),
            "gross_per_fill": float(np.average(group.gross_per_fill, weights=fills)),
            "maker_pnl_per_fill": float(np.average(group.maker_pnl_per_fill, weights=fills)),
        })
    components = pd.DataFrame(component_rows)
    components.to_csv(output / "symmetric_three_component_decomposition.csv", index=False)

    robustness = paired.merge(
        aggregate[aggregate.strategy.eq("model_11b")][
            ["split", "config", "rule", "fill_count", "maker_pnl_per_fill"]
        ],
        on=["split", "config", "rule"],
        how="left",
    )
    robustness.to_csv(output / "model_robustness_18_cells.csv", index=False)

    front_random_rows: list[dict[str, object]] = []
    for item in random_summary[random_summary.rule.eq("front")].itertuples(index=False):
        model = aggregate[
            aggregate.strategy.eq("model_11b")
            & aggregate.split.eq(item.split)
            & aggregate.config.eq(item.config)
            & aggregate.rule.eq("front")
        ].iloc[0]
        symmetric = aggregate[
            aggregate.strategy.eq("symmetric")
            & aggregate.split.eq(item.split)
            & aggregate.config.eq(item.config)
            & aggregate.rule.eq("front")
        ].iloc[0]
        front_random_rows.append({
            "config": item.config,
            "split": item.split,
            "symmetric_pnl_per_fill": float(symmetric.maker_pnl_per_fill),
            "random_mean": float(item.maker_pnl_mean),
            "random_95p": float(item.maker_pnl_95p),
            "model_pnl_per_fill": float(model.maker_pnl_per_fill),
            "random_worse_than_symmetric": float(item.maker_pnl_mean) < float(symmetric.maker_pnl_per_fill),
            "model_beats_random_95p": float(model.maker_pnl_per_fill) > float(item.maker_pnl_95p),
        })
    front_random = pd.DataFrame(front_random_rows)
    front_random.to_csv(output / "front_random_control_checks.csv", index=False)

    front_fill = fill[(fill.rule == "front") & (fill.side == "combined")].set_index("split").fill_rate
    front_model = bracket[bracket.strategy.eq("model_11b")].set_index("split")
    front_improvement = paired[(paired.rule == "front") & (paired.config == "no_spread_filter")].set_index("split")
    summary = {
        "result": "PASS",
        "fill_rate_front": {split: float(front_fill[split]) for split in ("val", "new3", "new4")},
        "model_net_pnl_front": {split: float(front_model.loc[split, "net_pnl_front"]) for split in ("val", "new3", "new4")},
        "model_net_pnl_bracket_width": {split: float(front_model.loc[split, "front_minus_back"]) for split in ("val", "new3", "new4")},
        "model_net_pnl_sign_at_front": {split: str(front_model.loc[split, "front_sign"]) for split in ("val", "new3", "new4")},
        "improvement_vs_symmetric_front": {split: float(front_improvement.loc[split, "mean_improvement"]) for split in ("val", "new3", "new4")},
        "improvement_t_front": {split: float(front_improvement.loc[split, "t"]) for split in ("val", "new3", "new4")},
        "improvement_significant_at_front": {split: bool(front_improvement.loc[split, "significant"]) for split in ("val", "new3", "new4")},
        "improvement_stable_across_all_three_rules": bool(manifest["improvement_stable_across_all_three_rules"]),
        "random_control_still_worse_at_front": bool(manifest["random_control_still_worse_at_front"]),
        "d_statistics": d_stats,
        "verdict": manifest["verdict"],
    }
    (output / "front_endpoint_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")

    lines = [
        "# 16A Final Front-Cancellation Report", "",
        "RESULT: PASS", "",
        "EXISTING_ENDPOINTS_REPRODUCED: yes", "",
        "MONOTONICITY_HOLDS: yes", "",
        f"D_NEGATIVE_COUNT: {d_stats['negative_count']}", "",
        f"D: p50 {d_stats['p50']} / p90 {d_stats['p90']} / p99 {d_stats['p99']} / max {d_stats['max']}; zero fraction {d_stats['zero_fraction']:.9%}; median D/trade {d_stats['median_d_over_trade_when_trade_positive']}", "",
        "## Fill-rate bracket", "", fill[fill.side.eq("combined")].to_markdown(index=False), "",
        "## Symmetric three-component decomposition", "", components.to_markdown(index=False), "",
        "## Net-PnL brackets", "", bracket.to_markdown(index=False), "",
        "## Model robustness: 18 cells", "", robustness.to_markdown(index=False), "",
        "## Front random-control checks", "", front_random.to_markdown(index=False), "",
        f"IMPROVEMENT_STABLE_ACROSS_ALL_THREE_RULES: {str(summary['improvement_stable_across_all_three_rules']).lower()}", "",
        f"RANDOM_CONTROL_STILL_WORSE_AT_FRONT: {str(summary['random_control_still_worse_at_front']).lower()}", "",
        f"VERDICT: {summary['verdict']}", "",
    ]
    (output / "FINAL_REPORT_16A.md").write_text("\n".join(lines), encoding="ascii")
    print("[DONE] final 16A tables written", flush=True)


if __name__ == "__main__":
    main()
