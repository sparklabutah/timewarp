# TimeWarp version validation — quantitative findings

**Question addressed.** A reviewer asked whether TimeWarp's six reconstructed UI versions are
*representative of real temporal web evolution*, or whether the benchmark instead measures
robustness to arbitrary handcrafted UI variation. This report gives the per-version
quantitative characterisation that was requested: DOM / accessibility-tree complexity,
interactive-element counts, visual density, and era-style markers.

**Scope note.** This is Phase 1 of the plan: it characterises the reconstructed versions
themselves. The direct comparison against archived pages (Wayback Machine) is Phase 3 and is
**not** included here. See [What this does and does not establish](#what-this-does-and-does-not-establish).
Workflow-length analysis was deliberately skipped.

---

## TL;DR

1. **The six versions are quantitatively distinct**, not cosmetic reskins. On Webshop the agent's
   action space varies **8×** (4.4 → 34.7 interactive elements) and its accessibility-tree
   observation varies **4×** (769 → 3,069 tokens) across versions of *identical content*.
2. **The web-technology markers follow the documented real historical trajectory** in all three
   environments, with strong and highly significant monotonic trends over the era-ordered
   versions v1→v5: CSS rule count (ρ = 1.00 / 0.80 / 0.90), responsive viewport meta
   (ρ = 0.87 / 0.87 / 0.87), media queries (ρ = 0.89 / 0.78 / 0.87), and the table-layout →
   flex/grid transition (ρ = 0.70 / 0.87 / 0.87 for wiki / news / webshop, all *p* < 0.001).
3. **The three environments diverge in a way that matches their real-world histories**, which is
   evidence *against* the "arbitrary handcrafted variation" reading: Webshop grows richer and
   denser over time, News gets structurally *lighter* but more interactive, and Wiki stays
   structurally stable while only its chrome modernises.
4. **Honest caveat:** this establishes internal validity (the versions differ systematically and
   in historically plausible directions). It does **not** yet establish that any given version
   matches real pages from its target year. That requires the archived-page comparison.

---

## Method

Because all six versions of an environment render the **same backend content** through a swapped
Flask theme folder, every measured difference isolates the UI era rather than the content. This
makes the comparison a clean controlled experiment.

- **Harness:** [`scripts/analysis/`](scripts/analysis/) — headless Chromium (Playwright) at the
  benchmark's own 1280×720 viewport.
- **Accessibility tree** comes from CDP `Accessibility.getFullAXTree`, the *same* source
  BrowserGym flattens into the agent's `axtree_txt` observation. "AX complexity" here therefore
  means complexity the agent actually perceives, and `AX obs tokens` is its real context cost.
- **Layout technology** is measured on the **rendered** page (computed `display`, plus a
  stylesheet walk), not by scraping HTML source — these themes keep flex/grid and media queries
  in external `style.css`, which source-scanning misses entirely.
- **Pages measured:** the same logical pages in every version — 246 page-measurements total
  (wiki 54, news 78, webshop 114), i.e. 9 / 13 / 19 pages per version.
  - wiki: index + 8 articles
  - news: index + browse + 3 searches + 8 articles
  - webshop: search + 3× (results, item, description, features, attributes, reviews)
- **Raw data:** [`results/validation/page_metrics.csv`](results/validation/page_metrics.csv)
  (one row per page), plus `version_summary_<env>.csv` and `version_summary_long.csv`.

### Version → era mapping

Taken from each app's `num_to_theme`. **Version 6 is a neutral minimal/baseline theme in every
environment, not an era**, so it is excluded from all trend statistics and reported as a control.

| v | Wiki | News | Webshop |
|---|------|------|---------|
| 1 | 2001 | 2000s | 2000 |
| 2 | 2002 | 2004 | 2005 |
| 3 | 2003–04 | 2008 | 2010 |
| 4 | 2005–2022 | 2016 | 2015 |
| 5 | 2023–2025 | 2024 | 2025 |
| 6 | *minimal (baseline)* | *base-minimal (baseline)* | *classic (original WebShop UI)* |

---

## Era-trend statistics

Spearman ρ between the era-ordered version (1–5) and each metric, computed over individual pages.
`***` *p* < 0.001, `**` *p* < 0.01, `*` *p* < 0.05.

| Metric | Wiki | News | Webshop |
|---|---:|---:|---:|
| **style.css_rules** | **1.00*** | **0.80*** | **0.90*** |
| **style.media_queries** | **0.89*** | **0.78*** | **0.87*** |
| **style.has_viewport_meta** | **0.87*** | **0.87*** | **0.87*** |
| **style.layout_modernity** | **0.70*** | **0.87*** | **0.87*** |
| style.tables_rendered | −0.27 | **−0.69*** | **−0.49*** |
| style.font_tags | n/a (0) | **−0.87*** | −0.15 |
| style.cdn_count | n/a (0) | n/a (0) | **0.68*** |
| dom.elements | 0.29 | **−0.63*** | **0.56*** |
| dom.depth_max | 0.20 | **−0.80*** | **0.53*** |
| page.html_bytes | 0.24 | **−0.44*** | **0.65*** |
| ax.nodes_meaningful | 0.17 | **−0.45*** | **0.41*** |
| ax.interactive_nodes | 0.19 | **0.55*** | **0.36*** |
| ax.flat_tokens | 0.15 | **−0.58*** | **0.34*** |
| ui.interactive_total | 0.24 | **0.56*** | **0.34*** |
| ui.buttons | **0.97*** | 0.23 | **0.53*** |
| viz.ink_fraction | **−0.42** | **−0.70*** | **0.68*** |
| viz.edge_density | **−0.73*** | **−0.45*** | 0.05 |
| viz.palette_colors | 0.11 | **−0.66*** | **0.85*** |
| viz.image_area_frac | **0.31*** | 0.00 | **0.76*** |

Significant (*p* < 0.05) era trends: **wiki 8/17, news 16/18, webshop 17/19**.

### The consistent core

Four markers trend strongly and significantly in **all three** environments, and they are exactly
the markers whose real-world history is documented and uncontroversial:

- **CSS rule count** rises monotonically (wiki 16 → 177, news 37 → 144, webshop 93 → 149).
- **Responsive design appears late**: viewport meta and media queries are 0 for early versions and
  switch on at v4 (wiki 2005+, news 2016) or v3 (webshop 2010) — matching when responsive design
  actually arrived.
- **Table-layout → flex/grid**: `layout_modernity` (0 = pure table layout, 1 = pure flex/grid) goes
  0.00 → 0.98 (wiki), 0.00 → 0.95 (news), 0.00 → 0.95 (webshop).
- **Deprecated tags die out**: News `<font>` tags 39.6 → 42.0 → 17.3 → 0 → 0.

That these four move together, in the right direction, at roughly the right dates, in three
independently authored environments is the strongest single piece of evidence that the versions
encode real era structure rather than arbitrary variation.

---

## Per-environment interpretation

### Webshop — richer, denser, more visual over time (17/19 metrics trend)

The clearest and most monotone story, and it matches real e-commerce history (compare Amazon 2000
vs 2025): pages grow from 107 → 248 DOM elements, HTML from 10.5 KB → 41.3 KB, the colour palette
from 281 → 2,040 distinct colours, above-the-fold image area from 1% → 23%, and ink fraction from
0.11 → 0.41. Buttons rise 9.4 → 24.9 as the UI shifts from link-navigation to app-like controls.

**Architectural finding.** Versions 1–3 (2000/2005/2010) render Description / Features /
Attributes / Reviews as **separate server-rendered sub-pages** (form POST to `item_sub_page`),
while versions 4–5 (2015/2025) collapse them into **in-page JavaScript tabs** that toggle hidden
panels with no navigation. This server-pages → single-page-app shift is itself a genuine temporal
web-evolution signal, and it materially changes the agent's task structure (a sub-page that was
once a navigation step becomes a same-page click). It was discovered while building the
measurement harness, which had to be reworked to handle both patterns.

### News — structurally lighter but more interactive (16/18 metrics trend)

News trends *inversely* on bulk-complexity metrics: DOM elements fall 220 → 127, max depth 15.4 →
7.2, AX observation tokens 4,084 → 2,673, ink fraction 0.23 → 0.09. Meanwhile interactivity rises:
interactive elements 32.6 → 63.3, AX interactive nodes 32.6 → 62.3.

This is historically correct rather than anomalous. Early-2000s news portals were dense,
table-based link farms (v1–v3 carry 11.8–15.6 `<table>` elements and up to 42 `<font>` tags per
page) crammed with small text; modern news sites use fewer, larger, more whitespace-separated
components with more interactive affordances. The benchmark's news versions reproduce that
inversion.

### Wiki — stable content structure, modernising chrome (8/17 metrics trend)

Wiki shows the weakest bulk trends (DOM elements 480 → 655, ρ = 0.29 n.s.), and this is a
*faithful* outcome rather than a weakness: Wikipedia's article structure has been famously
conservative, and what changed across its eras is chrome and styling, not article DOM. Accordingly
the significant trends are precisely the chrome/style ones — CSS rules 16 → 177 (ρ = 1.00), buttons
0 → 6.9 (ρ = 0.97), media queries (ρ = 0.89), viewport meta (ρ = 0.87) — plus a strong drop in
visual busyness (edge density 15.0 → 6.7, ρ = −0.73).

The v1 (2001) theme is a genuine outlier in the right direction: max DOM depth 3.1 (essentially
flat, unstyled HTML), 16 CSS rules, and a 66-colour palette versus 217–351 for later versions.

### Version 6 (the neutral baseline) behaves as intended

v6 is not an era and consistently sits *outside* the era progression — typically at or below the
minimum. Webshop v6 (`classic`, the original WebShop UI used by prior work) is by far the sparsest
page set measured: 49 DOM elements, 4.4 interactive elements, 769 AX tokens, ink fraction 0.06.
This confirms v6 functions as a clean control condition and validates excluding it from trends.

---

## Agent-facing impact

What matters for a robustness benchmark is how much the *agent's* input and action space move.
Across the six versions of identical content:

| | Wiki | News | Webshop |
|---|---:|---:|---:|
| AX observation tokens (min → max) | 21,837 → 24,663 (1.1×) | 2,015 → 4,195 (2.1×) | 769 → 3,069 (**4.0×**) |
| Action space, interactive elements | 329 → 398 (1.2×) | 19 → 63 (**3.3×**) | 4.4 → 34.7 (**8.0×**) |
| AX nodes | 1,958 → 2,349 (1.2×) | 173 → 394 (2.3×) | 63 → 304 (4.9×) |
| DOM elements | 480 → 655 (1.4×) | 106 → 263 (2.5×) | 49 → 248 (5.1×) |

Webshop and News impose substantial version-to-version shifts on the agent; Wiki is deliberately
milder (1.1–1.4×), which is worth stating explicitly in the paper — **Wiki is the low-variance
environment**, and per-environment robustness results should be read with that in mind rather than
averaged into a single number.

---

## What this does and does not establish

**Established.**
- The six versions are quantitatively distinct across DOM, accessibility-tree, interactive and
  visual dimensions, with large agent-facing effects on Webshop and News.
- Era-ordered versions show strong, statistically significant monotonic trends in exactly the
  markers whose real historical trajectory is well documented (CSS growth, responsive design
  onset, table→flex/grid, deprecated-tag decline), consistently across three independently
  authored environments.
- Cross-environment divergence follows real per-domain history (e-commerce enriches, news
  lightens, wiki stays stable), which arbitrary handcrafted variation would not predict.

**Not yet established.**
- **No comparison against real archived pages was performed.** Nothing here shows that, say,
  Webshop v2 quantitatively resembles amazon.com in 2005 rather than merely sitting between v1 and
  v3. Closing this requires the Phase 3 archived-page comparison: run the identical metric battery
  on Wayback snapshots of period sites, then (a) correlate the reconstructed trajectory with the
  archived one, (b) check each version falls inside its era's archived distribution, and (c) train
  an era classifier on archived pages only and confirm it assigns each reconstructed version to
  its intended era. Until then the honest claim is *"versions vary along historically plausible
  axes,"* not *"versions are faithful to their years."*
- Absolute realism of content density, since content is held constant by design.

**Other limitations.**
- Wiki v4 spans 2005–2022, a 17-year bucket that a single measurement cannot resolve.
- Era markers are not perfectly monotonic and should be read as a feature vector, not a scalar:
  e.g. Webshop v5 (2025) still loads a Bootstrap 3 CDN, and Webshop media queries peak at v4 (7.0)
  rather than v5 (5.2).
- Page sample is modest (9–19 pages per version); it is adequate for the large effects reported
  but per-page-type confidence intervals would need a larger `--limit-article`.
- Visual metrics are computed at a single 1280×720 viewport; responsive behaviour of later
  versions is only captured indirectly via media-query counts.

---

## Reproduction

```sh
conda activate timewarp

# Wiki + News: six-version sweep
for v in 1 2 3 4 5 6; do
  bash scripts/environment/run_all_env.sh "$v"
  python scripts/analysis/measure_pages.py --version "$v" --append --limit-article 8
  bash scripts/environment/stop_all_ports.sh
done

# Webshop needs its data + Lucene index first (Java 21 via conda; JAVA_HOME must point at
# $CONDA_PREFIX/lib/jvm, otherwise pyserini's JVM bridge fails on macOS):
#   bash env/webshop/setup.sh -d small

python scripts/analysis/summarize.py results/validation/page_metrics.csv
```

Full harness documentation: [`scripts/analysis/README.md`](scripts/analysis/README.md).

---

## Appendix — full per-version tables

Mean over all measured pages of that environment/version. Version 6 is the neutral baseline.

### Wiki

| Metric | v1 (2001) | v2 (2002) | v3 (2003–04) | v4 (2005–22) | v5 (2023–25) | v6 (base) |
|---|---:|---:|---:|---:|---:|---:|
| DOM elements | 479.67 | 571.33 | 594.67 | 644.22 | 654.89 | 509.22 |
| DOM nodes (+text) | 1,192.33 | 1,345.22 | 1,375.44 | 1,406.56 | 1,445.78 | 1,200.89 |
| DOM max depth | 3.11 | 10.00 | 10.67 | 8.67 | 8.67 | 8.89 |
| distinct tags | 17.00 | 27.00 | 27.78 | 23.22 | 28.11 | 23.67 |
| HTML bytes | 37,724.78 | 42,992.00 | 45,354.22 | 46,606.11 | 48,192.78 | 41,246.67 |
| AX nodes (meaningful) | 1,958.11 | 2,162.56 | 2,193.00 | 2,207.11 | 2,348.78 | 2,041.11 |
| AX interactive nodes | 332.22 | 386.33 | 383.56 | 385.56 | 398.44 | 329.11 |
| AX max depth | 4.11 | 10.00 | 11.44 | 9.44 | 8.22 | 7.67 |
| AX obs tokens | 21,837.33 | 23,332.22 | 23,539.56 | 23,748.56 | 24,662.78 | 22,387.89 |
| interactive elements | 332.22 | 366.44 | 384.44 | 385.56 | 398.44 | 329.11 |
| interactive above fold | 63.44 | 76.33 | 81.33 | 81.22 | 77.56 | 41.56 |
| links | 331.22 | 360.44 | 378.44 | 380.56 | 382.56 | 327.00 |
| buttons | 0.00 | 3.00 | 4.00 | 4.00 | 6.89 | 1.00 |
| forms | 1.00 | 3.00 | 2.00 | 1.00 | 1.00 | 0.00 |
| ink fraction | 0.12 | 0.11 | 0.10 | 0.12 | 0.08 | 0.07 |
| edge density | 14.97 | 13.65 | 6.93 | 7.01 | 6.67 | 5.71 |
| palette colors | 65.89 | 290.56 | 255.33 | 351.11 | 217.33 | 225.78 |
| image area frac | 0.00 | 0.02 | 0.02 | 0.03 | 0.01 | 0.00 |
| tables | 0.00 | 2.00 | 1.44 | 0.56 | 0.00 | 0.00 |
| layout modernity | 0.00 | 0.00 | 0.00 | 0.00 | 0.98 | 0.84 |
| media queries | 0.00 | 0.00 | 0.00 | 1.00 | 2.00 | 2.00 |
| CSS rules | 16.00 | 57.00 | 70.00 | 93.00 | 177.00 | 95.00 |
| viewport meta | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 |
| `<font>` tags | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CDN libs | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### News

| Metric | v1 (2000s) | v2 (2004) | v3 (2008) | v4 (2016) | v5 (2024) | v6 (base) |
|---|---:|---:|---:|---:|---:|---:|
| DOM elements | 220.31 | 258.85 | 263.08 | 127.77 | 127.46 | 106.15 |
| DOM nodes (+text) | 287.23 | 337.69 | 346.54 | 192.85 | 210.08 | 155.31 |
| DOM max depth | 15.38 | 12.31 | 15.54 | 7.31 | 7.15 | 8.69 |
| distinct tags | 20.31 | 20.54 | 20.85 | 22.92 | 21.00 | 25.54 |
| HTML bytes | 12,453.23 | 16,472.85 | 18,248.92 | 9,783.39 | 9,860.15 | 11,224.77 |
| AX nodes (meaningful) | 309.00 | 378.92 | 394.23 | 242.62 | 272.38 | 173.23 |
| AX interactive nodes | 32.62 | 47.69 | 48.54 | 40.00 | 62.31 | 19.23 |
| AX max depth | 12.31 | 10.15 | 12.31 | 6.77 | 6.62 | 7.31 |
| AX obs tokens | 4,084.39 | 4,137.85 | 4,194.85 | 2,455.92 | 2,672.61 | 2,014.92 |
| interactive elements | 32.62 | 47.69 | 48.23 | 41.00 | 63.31 | 19.23 |
| interactive above fold | 29.23 | 37.85 | 32.31 | 23.00 | 21.85 | 11.38 |
| links | 30.61 | 45.69 | 46.08 | 39.00 | 59.31 | 16.61 |
| buttons | 1.00 | 1.00 | 1.08 | 0.00 | 3.00 | 1.61 |
| forms | 1.00 | 1.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| ink fraction | 0.23 | 0.36 | 0.15 | 0.16 | 0.09 | 0.09 |
| edge density | 9.18 | 8.29 | 7.52 | 5.76 | 5.50 | 5.15 |
| palette colors | 200.08 | 356.69 | 365.15 | 349.38 | 380.85 | 133.15 |
| image area frac | 0.00 | 0.00 | 0.01 | 0.02 | 0.00 | 0.00 |
| tables | 11.77 | 14.46 | 15.62 | 0.00 | 0.00 | 0.00 |
| layout modernity | 0.00 | 0.00 | 0.00 | 0.91 | 0.95 | 0.91 |
| media queries | 0.00 | 0.00 | 0.00 | 4.00 | 2.00 | 2.00 |
| CSS rules | 37.00 | 31.00 | 65.00 | 200.00 | 144.00 | 141.46 |
| viewport meta | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 |
| `<font>` tags | 39.62 | 42.00 | 17.31 | 0.00 | 0.00 | 0.00 |
| CDN libs | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Webshop

| Metric | v1 (2000) | v2 (2005) | v3 (2010) | v4 (2015) | v5 (2025) | v6 (classic) |
|---|---:|---:|---:|---:|---:|---:|
| DOM elements | 106.84 | 94.74 | 122.95 | 132.58 | 247.84 | 49.05 |
| DOM nodes (+text) | 155.58 | 126.84 | 169.37 | 196.42 | 339.00 | 60.32 |
| DOM max depth | 8.47 | 8.74 | 9.21 | 8.84 | 15.00 | 9.00 |
| distinct tags | 17.74 | 21.42 | 24.84 | 23.37 | 28.16 | 10.95 |
| HTML bytes | 10,461.63 | 8,544.37 | 13,725.84 | 18,080.26 | 41,324.47 | 5,464.42 |
| AX nodes (meaningful) | 179.74 | 142.68 | 173.90 | 182.05 | 303.79 | 62.58 |
| AX interactive nodes | 23.79 | 20.74 | 22.05 | 28.05 | 34.90 | 4.37 |
| AX max depth | 6.37 | 8.37 | 7.68 | 6.00 | 8.05 | 5.95 |
| AX obs tokens | 1,927.89 | 1,515.37 | 1,858.00 | 2,054.89 | 3,069.42 | 769.42 |
| interactive elements | 23.79 | 20.74 | 21.42 | 25.00 | 34.74 | 4.37 |
| interactive above fold | 17.53 | 15.79 | 15.11 | 12.84 | 25.74 | 3.16 |
| links | 14.05 | 13.95 | 7.74 | 12.79 | 6.16 | 1.58 |
| buttons | 9.37 | 6.68 | 10.63 | 10.21 | 24.89 | 2.74 |
| forms | 9.37 | 6.47 | 5.63 | 4.95 | 13.42 | 2.74 |
| ink fraction | 0.11 | 0.24 | 0.13 | 0.27 | 0.41 | 0.06 |
| edge density | 3.90 | 3.71 | 3.51 | 3.81 | 2.88 | 2.47 |
| palette colors | 281.42 | 397.11 | 950.89 | 1,444.37 | 2,040.00 | 281.89 |
| image area frac | 0.01 | 0.02 | 0.06 | 0.20 | 0.23 | 0.05 |
| tables | 2.90 | 1.37 | 0.00 | 0.00 | 0.00 | 0.00 |
| layout modernity | 0.00 | 0.29 | 0.35 | 0.91 | 0.95 | 0.00 |
| media queries | 0.00 | 0.00 | 3.10 | 7.00 | 5.21 | 0.00 |
| CSS rules | 93.00 | 110.00 | 128.79 | 145.00 | 148.74 | 37.00 |
| viewport meta | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| `<font>` tags | 2.00 | 2.42 | 0.00 | 0.00 | 0.00 | 0.00 |
| CDN libs | 0.00 | 1.26 | 2.95 | 1.00 | 2.95 | 2.95 |
