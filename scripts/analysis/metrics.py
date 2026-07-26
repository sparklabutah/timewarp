"""Per-page quantitative metrics for TimeWarp version validation.

This module answers the reviewer question: *are the six reconstructed UI versions
representative of real temporal web evolution?* It extracts, for a single rendered
page, a battery of structural / interactive / visual metrics that can be compared
(a) across the six reconstructed versions of a TimeWarp environment and (b) against
real archived pages from the Wayback Machine (see ``fetch_wayback.py``).

Design goals
------------
* **Source-agnostic.** ``measure()`` takes a Playwright ``Page`` that has already
  navigated somewhere. It works identically for a reconstructed TimeWarp page and a
  Wayback replay page, so reconstructed-vs-archived comparisons use the exact same code.
* **Agent-faithful AX tree.** The accessibility-tree metrics come from Chrome DevTools
  Protocol ``Accessibility.getFullAXTree`` -- the *same* source BrowserGym feeds to the
  agent as its ``axtree_txt`` observation -- so "AX complexity" here means the complexity
  the agent actually perceives, not an unrelated library's notion of it.
* **Self-contained.** Runs in the repo's ``timewarp`` conda env using only Playwright,
  numpy, Pillow and tiktoken. BrowserGym's own ``flatten_axtree_to_str`` is used if it
  happens to be importable, otherwise a faithful fallback flattener is used.

Metric families (dotted key prefixes in the returned dict)
    dom.*    rendered DOM structure (node/element counts, depth, branching, tag variety)
    ax.*     accessibility tree (node counts, depth, roles, agent-observation token size)
    ui.*     interactive affordances (links, buttons, inputs, forms, action-space size)
    viz.*    visual density from a viewport screenshot (ink, palette, edges, image area)
    style.*  raw-HTML era markers (table-layout vs flex/grid, CDNs, <font>, viewport meta)
    page.*   bookkeeping (byte size, scroll height, title)
"""

from __future__ import annotations

import re
from typing import Any, Optional

# tiktoken is optional-at-runtime: AX token counts are a "nice to have" proxy for the
# agent's observation size. If it is missing we degrade gracefully rather than crash.
try:
    import tiktoken

    _ENCODING_NAME = "cl100k_base"  # BrowserGym's count_tokens default (gpt-4 family)
    _ENCODER = tiktoken.get_encoding(_ENCODING_NAME)
except Exception:  # pragma: no cover - environment without tiktoken
    _ENCODING_NAME = "none"
    _ENCODER = None

# Prefer BrowserGym's exact AX-tree flattener when the runtime provides it, so the token
# count matches the agent's real observation byte-for-byte. Fall back to our own flattener
# (see ``_flatten_axtree_fallback``) in envs that don't have BrowserGym installed.
try:
    from browsergym.utils.obs import flatten_axtree_to_str as _bg_flatten_axtree  # type: ignore
except Exception:  # pragma: no cover
    _bg_flatten_axtree = None


# Standard TimeWarp agent viewport (browsergym.timewarp GenericTimeWarpTask.viewport).
VIEWPORT = {"width": 1280, "height": 720}

# AX roles that represent an interactive affordance the agent can act on.
_AX_INTERACTIVE_ROLES = {
    "button", "link", "textbox", "searchbox", "combobox", "listbox", "checkbox",
    "radio", "switch", "slider", "spinbutton", "menuitem", "menuitemcheckbox",
    "menuitemradio", "tab", "option", "treeitem",
}


# --------------------------------------------------------------------------------------
# DOM metrics (rendered, via in-page JS so JS-inserted nodes are included)
# --------------------------------------------------------------------------------------

# Runs in the page and returns a flat object. Everything is measured on the main document,
# which keeps reconstructed pages and (raw ``id_``) Wayback pages comparable.
_DOM_JS = r"""
() => {
  const vw = window.innerWidth, vh = window.innerHeight;
  const els = Array.from(document.querySelectorAll('*'));
  const out = {};

  // --- structure ---
  out.elements = els.length;
  let textNodes = 0, textChars = 0;
  const tw = document.createTreeWalker(document.documentElement || document.body,
                                       NodeFilter.SHOW_TEXT);
  let tn;
  while ((tn = tw.nextNode())) {
    const t = (tn.textContent || '').trim();
    if (t) { textNodes += 1; textChars += t.length; }
  }
  out.text_nodes = textNodes;
  out.nodes = els.length + textNodes;
  out.text_chars = textChars;

  const tags = new Set();
  let depthSum = 0, depthMax = 0, childSum = 0, childMax = 0, leaves = 0;
  for (const el of els) {
    tags.add(el.tagName.toLowerCase());
    let d = 0, p = el.parentElement;
    while (p) { d += 1; p = p.parentElement; }
    depthSum += d; if (d > depthMax) depthMax = d;
    const c = el.childElementCount;
    childSum += c; if (c > childMax) childMax = c;
    if (c === 0) leaves += 1;
  }
  out.distinct_tags = tags.size;
  out.depth_max = depthMax;
  out.depth_mean = els.length ? depthSum / els.length : 0;
  out.branching_mean = els.length ? childSum / els.length : 0;
  out.branching_max = childMax;
  out.leaf_elements = leaves;
  out.scroll_height = Math.max(document.documentElement.scrollHeight || 0,
                               document.body ? document.body.scrollHeight : 0);

  // --- interactive affordances ---
  const q = (s) => document.querySelectorAll(s).length;
  out.links = q('a[href]');
  out.buttons = q("button, input[type=submit], input[type=button], input[type=reset], [role=button]");
  out.text_inputs = q("input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=image]), textarea");
  out.selects = q('select');
  out.forms = q('form');
  out.onclick = q('[onclick]');
  out.role_elems = q('[role]');
  out.tabindex_elems = q('[tabindex]');
  out.contenteditable = q('[contenteditable="true"], [contenteditable=""]');
  out.images = q('img');

  // Union of "actionable" elements (dedup so an <a role=button> isn't counted twice),
  // then split into visible and above-the-fold -- the above-fold count approximates the
  // agent's usable action space on first view.
  const actionable = new Set();
  document.querySelectorAll(
    "a[href], button, input:not([type=hidden]), textarea, select, [role=button], " +
    "[onclick], [tabindex]"
  ).forEach(e => actionable.add(e));
  let visible = 0, aboveFold = 0;
  let imgArea = 0, imgAreaAbove = 0;
  for (const e of actionable) {
    const r = e.getBoundingClientRect();
    const vis = r.width > 0 && r.height > 0;
    if (vis) {
      visible += 1;
      if (r.top < vh && r.bottom > 0) aboveFold += 1;
    }
  }
  out.interactive_total = actionable.size;
  out.interactive_visible = visible;
  out.interactive_above_fold = aboveFold;

  // image pixel area (rendered) + fraction of first viewport covered by imagery
  for (const im of document.querySelectorAll('img')) {
    const r = im.getBoundingClientRect();
    const a = Math.max(0, r.width) * Math.max(0, r.height);
    imgArea += a;
    const iw = Math.max(0, Math.min(r.right, vw) - Math.max(r.left, 0));
    const ih = Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0));
    imgAreaAbove += iw * ih;
  }
  out.image_area = imgArea;
  out.image_area_fraction_above_fold = (vw * vh) ? imgAreaAbove / (vw * vh) : 0;

  // --- rendered layout technology (reflects APPLIED css, incl. external sheets) ---
  // Source-HTML scanning misses flex/grid/media-queries that live in linked style.css;
  // computed display + a stylesheet walk capture them where they actually take effect.
  let flex = 0, grid = 0;
  for (const el of els) {
    const d = getComputedStyle(el).display;
    if (d === 'flex' || d === 'inline-flex') flex += 1;
    else if (d === 'grid' || d === 'inline-grid') grid += 1;
  }
  out.render_flex = flex;
  out.render_grid = grid;
  out.render_tables = document.querySelectorAll('table').length;
  let mq = 0, cssRules = 0;
  for (const sheet of Array.from(document.styleSheets)) {
    try {
      const rs = sheet.cssRules;
      if (!rs) continue;
      cssRules += rs.length;
      for (const r of Array.from(rs)) {
        if (r.type === CSSRule.MEDIA_RULE) mq += 1;
      }
    } catch (e) { /* cross-origin sheet: cssRules blocked, skip */ }
  }
  out.render_media_queries = mq;
  out.render_css_rules = cssRules;
  out.render_stylesheets = document.styleSheets.length;

  // above-the-fold text volume (text-node rects intersecting the first viewport)
  let aboveChars = 0;
  const tw2 = document.createTreeWalker(document.body || document.documentElement,
                                        NodeFilter.SHOW_TEXT);
  let n2;
  while ((n2 = tw2.nextNode())) {
    const t = (n2.textContent || '').trim();
    if (!t) continue;
    const range = document.createRange();
    range.selectNodeContents(n2);
    const r = range.getBoundingClientRect();
    if (r.top < vh && r.bottom > 0 && r.width > 0) aboveChars += t.length;
  }
  out.text_chars_above_fold = aboveChars;

  return out;
}
"""


def dom_metrics(page) -> dict[str, Any]:
    try:
        raw = page.evaluate(_DOM_JS)
    except Exception as e:  # pragma: no cover
        return {"dom.error": type(e).__name__}
    # split raw keys into dom.* / ui.* families
    dom_keys = {"elements", "nodes", "text_nodes", "text_chars", "distinct_tags",
                "depth_max", "depth_mean", "branching_mean", "branching_max",
                "leaf_elements", "scroll_height"}
    ui_keys = {"links", "buttons", "text_inputs", "selects", "forms", "onclick",
               "role_elems", "tabindex_elems", "contenteditable", "images",
               "interactive_total", "interactive_visible", "interactive_above_fold"}
    viz_keys = {"image_area", "image_area_fraction_above_fold",
                "text_chars_above_fold"}
    # rendered-layout keys -> style.* (stripping the render_ prefix)
    style_map = {
        "render_flex": "style.flex_rendered",
        "render_grid": "style.grid_rendered",
        "render_tables": "style.tables_rendered",
        "render_media_queries": "style.media_queries_rendered",
        "render_css_rules": "style.css_rules",
        "render_stylesheets": "style.stylesheets",
    }
    out: dict[str, Any] = {}
    for k, v in raw.items():
        if k in style_map:
            out[style_map[k]] = v
        elif k in dom_keys:
            out[f"dom.{k}"] = v
        elif k in ui_keys:
            out[f"ui.{k}"] = v
        elif k in viz_keys:
            out[f"viz.{k}"] = v
        else:
            out[f"dom.{k}"] = v
    return out


# --------------------------------------------------------------------------------------
# Accessibility-tree metrics (CDP: the same tree BrowserGym flattens for the agent)
# --------------------------------------------------------------------------------------

def _flatten_axtree_fallback(nodes: list[dict], id_to_node: dict, roots: list[str]) -> str:
    """Faithful-enough stand-in for browsergym.utils.obs.flatten_axtree_to_str.

    Produces an indented ``role 'name'`` outline over the non-ignored nodes. The exact
    string differs from BrowserGym's (which adds bids/properties), but its token count is
    a good proxy for the agent's observation size when BrowserGym isn't installed.
    """
    lines: list[str] = []

    def walk(node_id: str, depth: int) -> None:
        node = id_to_node.get(node_id)
        if node is None:
            return
        ignored = node.get("ignored", False)
        role = (node.get("role") or {}).get("value", "")
        name = (node.get("name") or {}).get("value", "")
        if not ignored and role:
            name = re.sub(r"\s+", " ", str(name)).strip()
            lines.append("\t" * depth + (f"{role} {name!r}" if name else role))
            depth += 1
        for child_id in node.get("childIds", []) or []:
            walk(child_id, depth)

    for r in roots:
        walk(r, 0)
    return "\n".join(lines)


def ax_metrics(page) -> dict[str, Any]:
    try:
        cdp = page.context.new_cdp_session(page)
        result = cdp.send("Accessibility.getFullAXTree")
        nodes = result.get("nodes", [])
    except Exception as e:  # pragma: no cover
        return {"ax.error": type(e).__name__}

    id_to_node = {n["nodeId"]: n for n in nodes}
    child_ids = set()
    for n in nodes:
        for c in n.get("childIds", []) or []:
            child_ids.add(c)
    roots = [n["nodeId"] for n in nodes if n["nodeId"] not in child_ids]

    total = len(nodes)
    meaningful = 0
    roles: dict[str, int] = {}
    interactive = 0
    for n in nodes:
        if n.get("ignored", False):
            continue
        meaningful += 1
        role = (n.get("role") or {}).get("value", "")
        if role:
            roles[role] = roles.get(role, 0) + 1
            if role in _AX_INTERACTIVE_ROLES:
                interactive += 1

    # depth over meaningful structure
    depth_max = 0

    def depth_walk(node_id: str, depth: int) -> None:
        nonlocal depth_max
        if depth > depth_max:
            depth_max = depth
        node = id_to_node.get(node_id)
        if node is None:
            return
        step = 0 if node.get("ignored", False) else 1
        for c in node.get("childIds", []) or []:
            depth_walk(c, depth + step)

    for r in roots:
        depth_walk(r, 0)

    out: dict[str, Any] = {
        "ax.nodes_total": total,
        "ax.nodes_meaningful": meaningful,
        "ax.distinct_roles": len(roles),
        "ax.interactive_nodes": interactive,
        "ax.depth_max": depth_max,
    }

    # agent-observation size: flatten to text and count tokens (proxy for context cost)
    try:
        if _bg_flatten_axtree is not None:
            text = _bg_flatten_axtree(
                {"nodes": nodes}, extra_properties=None, with_visible=False,
                with_clickable=False, with_center_coords=False,
                with_bounding_box_coords=False, filter_visible_only=False,
            )
        else:
            text = _flatten_axtree_fallback(nodes, id_to_node, roots)
        out["ax.flat_chars"] = len(text)
        if _ENCODER is not None:
            out["ax.flat_tokens"] = len(_ENCODER.encode(text))
        out["ax.flat_tokens_encoding"] = _ENCODING_NAME
    except Exception as e:  # pragma: no cover
        out["ax.flat_error"] = type(e).__name__
    return out


# --------------------------------------------------------------------------------------
# Raw-HTML era markers (source-level signals of web era)
# --------------------------------------------------------------------------------------

_CDN_PATTERNS = {
    "bootstrap": re.compile(r"bootstrap(?:cdn)?|bootstrap(?:\.min)?\.css", re.I),
    "jquery": re.compile(r"jquery", re.I),
    "fontawesome": re.compile(r"font-?awesome", re.I),
    "google_fonts": re.compile(r"fonts\.(?:googleapis|gstatic)\.com", re.I),
}


def html_metrics(html: str) -> dict[str, Any]:
    if not html:
        return {"style.error": "empty_html"}
    low = html.lower()

    def count(pat: str) -> int:
        return len(re.findall(pat, low))

    doctype = ""
    m = re.search(r"<!doctype[^>]*>", low)
    if m:
        doctype = m.group(0)
    is_html5 = doctype.strip() == "<!doctype html>"

    out: dict[str, Any] = {
        "page.html_bytes": len(html.encode("utf-8")),
        "style.doctype_html5": int(is_html5),
        "style.has_viewport_meta": int(bool(re.search(r'<meta[^>]+name=["\']?viewport', low))),
        "style.tables": count(r"<table\b"),
        "style.font_tags": count(r"<font\b"),
        "style.center_tags": count(r"<center\b"),
        "style.marquee_tags": count(r"<marquee\b"),
        "style.blink_tags": count(r"<blink\b"),
        "style.bgcolor_attrs": count(r"\bbgcolor\s*="),
        "style.inline_style_attrs": count(r'\bstyle\s*='),
        "style.script_tags": count(r"<script\b"),
        "style.link_stylesheets": count(r'<link[^>]+stylesheet'),
        "style.inline_style_blocks": count(r"<style\b"),
        "style.flex_mentions": count(r"display\s*:\s*flex|:\s*flex\b"),
        "style.grid_mentions": count(r"display\s*:\s*grid|grid-template"),
        "style.media_queries": count(r"@media\b"),
        "style.svg_tags": count(r"<svg\b"),
        "style.picture_srcset": count(r"<picture\b|\bsrcset="),
        "style.aria_attrs": count(r'\baria-[a-z]+\s*='),
        "style.data_attrs": count(r'\bdata-[a-z0-9-]+\s*='),
    }
    for name, pat in _CDN_PATTERNS.items():
        out[f"style.cdn_{name}"] = int(bool(pat.search(html)))
    out["style.cdn_count"] = sum(out[f"style.cdn_{n}"] for n in _CDN_PATTERNS)
    # Source-only modernity ratio (inline styles). The authoritative rendered version is
    # computed in measure() from applied CSS; this stays as a secondary signal.
    modern = out["style.flex_mentions"] + out["style.grid_mentions"]
    out["style.layout_modernity_src"] = modern / (modern + out["style.tables"] + 1)
    return out


# --------------------------------------------------------------------------------------
# Visual-density metrics (from a viewport screenshot)
# --------------------------------------------------------------------------------------

def screenshot_metrics(png_bytes: bytes) -> dict[str, Any]:
    if not png_bytes:
        return {}
    try:
        import io

        import numpy as np
        from PIL import Image

        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        arr = np.asarray(img, dtype=np.int16)  # H x W x 3
    except Exception as e:  # pragma: no cover
        return {"viz.error": type(e).__name__}

    h, w, _ = arr.shape
    flat = arr.reshape(-1, 3)

    # palette size: quantize to 5 bits/channel (32 levels) and count distinct buckets
    q = (arr >> 3).astype(np.int32)  # 0..31
    codes = (q[..., 0] << 10) | (q[..., 1] << 5) | q[..., 2]
    palette = int(np.unique(codes).size)

    # background = modal color; "ink" = fraction of pixels far from it (content/edges)
    vals, counts = np.unique(codes.reshape(-1), return_counts=True)
    bg_code = int(vals[int(np.argmax(counts))])
    bg_rgb = np.array([(bg_code >> 10) & 31, (bg_code >> 5) & 31, bg_code & 31]) * 8
    dist = np.abs(flat - bg_rgb).sum(axis=1)
    ink_fraction = float((dist > 24).mean())

    # edge density: mean gradient magnitude of luminance (visual busyness)
    lum = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2])
    gx = np.abs(np.diff(lum, axis=1))
    gy = np.abs(np.diff(lum, axis=0))
    edge_density = float((gx.mean() + gy.mean()) / 2.0)

    return {
        "viz.palette_colors": palette,
        "viz.ink_fraction": ink_fraction,
        "viz.edge_density": edge_density,
        "viz.mean_luminance": float(lum.mean()),
        "viz.luminance_std": float(lum.std()),
        "viz.px_width": w,
        "viz.px_height": h,
    }


# --------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------

def measure(page, *, html: Optional[str] = None, screenshot: bool = True) -> dict[str, Any]:
    """Measure the page currently loaded in ``page``.

    Parameters
    ----------
    page : playwright.sync_api.Page
        A page that has already navigated to the target and settled.
    html : str, optional
        Raw HTML for source-level markers. If omitted, ``page.content()`` is used.
        (For Wayback ``id_`` fetches you may pass the archived source explicitly.)
    screenshot : bool
        Capture a viewport screenshot for visual-density metrics.

    Returns a flat dict of ``family.metric -> value``. Each family is wrapped in its own
    try/except so a single failure never loses the whole row.
    """
    out: dict[str, Any] = {}
    out.update(dom_metrics(page))
    out.update(ax_metrics(page))

    if html is None:
        try:
            html = page.content()
        except Exception:
            html = ""
    out.update(html_metrics(html))

    # Authoritative table-layout-vs-modern ratio from APPLIED css (0 = pure table layout,
    # 1 = pure flex/grid). Trends up over web eras and is CSS-location independent.
    flex = out.get("style.flex_rendered", 0)
    grid = out.get("style.grid_rendered", 0)
    tables = out.get("style.tables_rendered", out.get("style.tables", 0))
    modern = flex + grid
    out["style.layout_modernity"] = modern / (modern + tables + 1)

    try:
        out["page.title"] = page.title()
    except Exception:
        out["page.title"] = ""

    if screenshot:
        try:
            png = page.screenshot(clip={"x": 0, "y": 0, **VIEWPORT})
            out.update(screenshot_metrics(png))
        except Exception as e:
            out["viz.error"] = type(e).__name__
    return out


__all__ = [
    "measure", "dom_metrics", "ax_metrics", "html_metrics", "screenshot_metrics",
    "VIEWPORT",
]
