#!/usr/bin/env python
"""Summarize page-metric CSVs into per-version tables (Phase 1 deliverable).

Reads one or more ``page_metrics.csv`` files produced by ``measure_pages.py`` and emits,
for each environment, a compact ``version x headline-metric`` table of means (the exact
"per-version statistics" a reviewer asks for: DOM/AX complexity, interactive-element
counts, visual density, era-style markers). Also writes a tidy long-format CSV
(``env, version, page_type, metric, mean, std, n``) for downstream plotting/stats.

Usage:
    python scripts/analysis/summarize.py results/validation/page_metrics.csv
    python scripts/analysis/summarize.py a.csv b.csv --out-dir results/validation
"""

from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

# Headline metrics per family, in the order they should appear in the summary table.
HEADLINE = [
    # DOM complexity
    ("dom.elements", "DOM elements"),
    ("dom.nodes", "DOM nodes (+text)"),
    ("dom.depth_max", "DOM max depth"),
    ("dom.distinct_tags", "distinct tags"),
    ("page.html_bytes", "HTML bytes"),
    # Accessibility tree (agent observation)
    ("ax.nodes_meaningful", "AX nodes (meaningful)"),
    ("ax.interactive_nodes", "AX interactive nodes"),
    ("ax.depth_max", "AX max depth"),
    ("ax.flat_tokens", "AX obs tokens"),
    # Interactive affordances (action space)
    ("ui.interactive_total", "interactive elements"),
    ("ui.interactive_above_fold", "interactive above fold"),
    ("ui.links", "links"),
    ("ui.buttons", "buttons"),
    ("ui.forms", "forms"),
    # Visual density
    ("viz.ink_fraction", "ink fraction"),
    ("viz.edge_density", "edge density"),
    ("viz.palette_colors", "palette colors"),
    ("viz.image_area_fraction_above_fold", "image area frac"),
    # Era-style markers
    ("style.tables_rendered", "tables"),
    ("style.layout_modernity", "layout modernity"),
    ("style.media_queries_rendered", "media queries"),
    ("style.css_rules", "CSS rules"),
    ("style.has_viewport_meta", "viewport meta"),
    ("style.font_tags", "<font> tags"),
    ("style.cdn_count", "CDN libs"),
]


def load(paths: list[str]) -> pd.DataFrame:
    frames = []
    for p in paths:
        df = pd.read_csv(p)
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    # version may be read as int or str; normalize to str for stable grouping/sorting
    df["version"] = df["version"].astype(str)
    return df


def summarize(df: pd.DataFrame, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    present = [(c, label) for c, label in HEADLINE if c in df.columns]
    metric_cols = [c for c, _ in present]

    # ---- tidy long-format summary (per env x version x page_type x metric) ----
    long_rows = []
    grp = df.groupby(["env", "version", "page_type"])
    for (env, version, pt), sub in grp:
        for c in metric_cols:
            vals = pd.to_numeric(sub[c], errors="coerce").dropna()
            if len(vals):
                long_rows.append({
                    "env": env, "version": version, "page_type": pt, "metric": c,
                    "mean": vals.mean(), "std": vals.std(ddof=0), "n": len(vals),
                })
    long_df = pd.DataFrame(long_rows)
    long_path = os.path.join(out_dir, "version_summary_long.csv")
    long_df.to_csv(long_path, index=False)

    # ---- wide per-env summary table (version x headline metric, mean over pages) ----
    label_map = dict(present)
    for env in sorted(df["env"].unique()):
        sub = df[df["env"] == env]
        means = {}
        for c in metric_cols:
            vals = pd.to_numeric(sub[c], errors="coerce")
            means[label_map[c]] = sub.assign(_v=vals).groupby("version")["_v"].mean()
        table = pd.DataFrame(means).T  # rows = metrics, cols = versions
        table = table[sorted(table.columns, key=_ver_key)]
        wide_path = os.path.join(out_dir, f"version_summary_{env}.csv")
        table.round(3).to_csv(wide_path)

        print(f"\n{'=' * 78}\n{env.upper()} — mean per version "
              f"(pages: {len(sub)}, versions: {', '.join(table.columns)})\n{'=' * 78}")
        with pd.option_context("display.width", 200, "display.max_rows", 100,
                               "display.float_format", lambda x: f"{x:,.2f}"):
            print(table)

    print(f"\n[done] wrote long summary -> {long_path}")
    print(f"[done] wrote per-env wide summaries -> {out_dir}/version_summary_<env>.csv")


def _ver_key(v: str):
    try:
        return (0, int(v))
    except ValueError:
        return (1, v)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+", help="one or more page_metrics.csv files")
    ap.add_argument("--out-dir", default="results/validation")
    args = ap.parse_args()

    df = load(args.csv)
    if df.empty:
        print("[error] no rows", file=sys.stderr)
        return 1
    summarize(df, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
