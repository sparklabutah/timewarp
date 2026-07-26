#!/usr/bin/env python
"""Measure per-page metrics for one or more TimeWarp environments at a given version.

Phase 1 of the version-validation analysis. Starts a headless Chromium, walks the page
inventory (``inventory.py``) for each requested environment, extracts the full metric
battery (``metrics.py``) from every page, and appends the results to a wide CSV
(one row per page, one column per metric).

Prerequisites
    * The target environment(s) must already be running at a known version, e.g.:
          bash scripts/environment/run_all_env.sh 3
      which exports TW_WIKI / TW_NEWS / TW_WEBSHOP. Pass those URLs via the flags below
      or let this script read them from the environment.
    * Run with the repo's ``timewarp`` conda env (has playwright, numpy, Pillow, tiktoken).

Typical usage -- sweep all six versions of every environment:
    for v in 1 2 3 4 5 6; do
      bash scripts/environment/run_all_env.sh $v
      python scripts/analysis/measure_pages.py --version $v --append
      bash scripts/environment/stop_all_ports.sh
    done

The ``--version`` label is recorded verbatim; it is metadata, not used to start anything.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import inventory  # noqa: E402
import metrics  # noqa: E402

DEFAULT_OUT = "results/validation/page_metrics.csv"
META_COLS = ["source", "env", "version", "page_type", "page_id", "url"]


def resolve_base_urls(args) -> dict[str, str]:
    """Map env name -> base URL from CLI flags, falling back to TW_* env vars."""
    urls = {}
    candidates = {
        "wiki": args.wiki_url or os.environ.get("TW_WIKI"),
        "news": args.news_url or os.environ.get("TW_NEWS"),
        "webshop": args.webshop_url or os.environ.get("TW_WEBSHOP"),
    }
    envs = ["wiki", "news", "webshop"] if args.env == "all" else [args.env]
    for e in envs:
        if candidates[e]:
            urls[e] = candidates[e].rstrip("/")
        else:
            print(f"[warn] no base URL for '{e}' (set --{e}-url or TW_{e.upper()}); skipping",
                  file=sys.stderr)
    return urls


def measure_env(page, env: str, base_url: str, version: str, limits: dict,
                screenshot: bool) -> list[dict]:
    """Walk one environment's inventory and return a metric row per page."""
    rows: list[dict] = []
    gen = inventory.TARGETS[env](page, base_url, limits)
    for page_type, page_id in gen:
        t0 = time.time()
        try:
            m = metrics.measure(page, screenshot=screenshot)
        except Exception as e:
            m = {"measure.error": type(e).__name__}
        row = {
            "source": "reconstructed",
            "env": env,
            "version": version,
            "page_type": page_type,
            "page_id": page_id,
            "url": page.url,
        }
        row.update(m)
        rows.append(row)
        print(f"  [{env} v{version}] {page_type:<12} {page_id:<24} "
              f"dom={m.get('dom.elements','?')} ax={m.get('ax.nodes_meaningful','?')} "
              f"ui={m.get('ui.interactive_total','?')} ({time.time()-t0:.1f}s)")
    return rows


def write_csv(rows: list[dict], out_path: str, append: bool) -> None:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    # Stable column order: metadata first, then metric columns grouped by family.
    metric_cols: set[str] = set()
    for r in rows:
        metric_cols.update(k for k in r if k not in META_COLS)

    existing_header = None
    if append and os.path.exists(out_path):
        with open(out_path, newline="") as f:
            existing_header = next(csv.reader(f), None)

    if existing_header:
        header = existing_header
        extra = sorted(c for c in metric_cols if c not in header)
        if extra:
            # New metric columns appeared; rewrite file with the widened header.
            with open(out_path, newline="") as f:
                old_rows = list(csv.DictReader(f))
            header = header + extra
            _dump(out_path, header, old_rows + rows, "w")
            return
        mode = "a"
    else:
        header = META_COLS + sorted(metric_cols)
        mode = "w"
    _dump(out_path, header, rows, mode)


def _dump(out_path: str, header: list[str], rows: list[dict], mode: str) -> None:
    with open(out_path, mode, newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        if mode == "w":
            w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", choices=["wiki", "news", "webshop", "all"], default="all")
    ap.add_argument("--version", required=True,
                    help="version label recorded in the CSV (e.g. 1..6)")
    ap.add_argument("--wiki-url", default=None)
    ap.add_argument("--news-url", default=None)
    ap.add_argument("--webshop-url", default=None)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--append", action="store_true",
                    help="append to --out instead of overwriting")
    ap.add_argument("--limit-article", type=int, default=None,
                    help="override number of article pages sampled per env")
    ap.add_argument("--no-screenshot", action="store_true",
                    help="skip visual-density metrics (faster)")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    limits = dict(inventory.DEFAULT_LIMITS)
    if args.limit_article is not None:
        limits["article"] = args.limit_article

    base_urls = resolve_base_urls(args)
    if not base_urls:
        print("[error] no environments to measure; is anything running?", file=sys.stderr)
        return 2

    from playwright.sync_api import sync_playwright

    all_rows: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            viewport=metrics.VIEWPORT,
            ignore_https_errors=True,
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        )
        page = context.new_page()
        page.set_default_timeout(12000)
        for env, base_url in base_urls.items():
            print(f"[info] measuring {env} at {base_url} (version {args.version})")
            try:
                rows = measure_env(page, env, base_url, args.version, limits,
                                   screenshot=not args.no_screenshot)
                all_rows.extend(rows)
            except Exception as e:
                print(f"[error] {env} failed: {type(e).__name__}: {e}", file=sys.stderr)
        browser.close()

    if not all_rows:
        print("[error] no rows measured", file=sys.stderr)
        return 1

    write_csv(all_rows, args.out, append=args.append)
    print(f"\n[done] wrote {len(all_rows)} rows -> {args.out}")
    # quick per-env / per-page-type tally
    tally: dict[tuple[str, str], int] = {}
    for r in all_rows:
        tally[(r["env"], r["page_type"])] = tally.get((r["env"], r["page_type"]), 0) + 1
    for (env, pt), n in sorted(tally.items()):
        print(f"    {env:<8} {pt:<12} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
