"""Page inventory for TimeWarp version validation.

Defines, per environment, the concrete set of pages to measure. Because all six
versions of an environment render the *same backend content* through swapped theme
folders, we visit the *same logical pages* in every version -- so any measured metric
delta isolates the UI era, not the content.

Each environment exposes a generator ``<env>_targets(page, base_url, limits)`` that
**drives** the Playwright ``page`` to each target and ``yield``s a ``(page_type,
page_id)`` label once the page is loaded and settled. The orchestrator simply measures
whatever is currently on screen after each yield. This generator style keeps navigation
logic (including Webshop's click-through flow, whose URLs embed session/asin/keywords)
next to the pages it produces, and is robust to per-version markup differences.

Page types
    wiki    : index, article
    news    : index, browse, search, article
    webshop : search, results, item, description, features, attributes, reviews
"""

from __future__ import annotations

import re
from typing import Iterator
from urllib.parse import urljoin, urlparse

# How many discovered pages of each dynamic type to sample. Kept modest so a full
# six-version sweep is quick; raise via measure_pages.py --limit for tighter CIs.
DEFAULT_LIMITS = {
    "article": 12,   # wiki & news article pages sampled from the index/browse hubs
    "results": 3,    # webshop result-list pages (distinct search queries)
    "item": 3,       # webshop item pages (one per query)
}

# Deterministic seed queries -> reproducible page sets across versions and reruns.
WIKI_SEED_TITLES = [
    "Science", "History", "Geography", "Mathematics", "Technology",
    "Biology", "Physics", "Australia", "China", "Music",
]
NEWS_SEARCH_QUERIES = ["election", "technology", "climate"]
WEBSHOP_QUERIES = ["shirt", "coffee maker", "wireless headphones"]


def _settle(page, timeout: int = 8000) -> None:
    """Wait for a page to reach a stable, measurable state.

    'load' then a short 'networkidle' (best-effort) covers the static Flask pages and
    Wayback replays alike without hanging on long-poll/analytics connections.
    """
    try:
        page.wait_for_load_state("load", timeout=timeout)
    except Exception:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=2000)
    except Exception:
        pass
    try:
        page.wait_for_timeout(300)  # let late layout/fonts settle
    except Exception:
        pass


def _slug(url: str, fallback: str = "page", maxlen: int = 48) -> str:
    """Short stable id from a URL's last path segment."""
    from urllib.parse import unquote

    path = urlparse(url).path.rstrip("/")
    seg = unquote(path.rsplit("/", 1)[-1]) if path else ""
    seg = re.sub(r"[^A-Za-z0-9._-]+", "-", seg).strip("-")
    return seg[:maxlen] or fallback


def _discover_links(page, base_url: str, path_contains: str, limit: int) -> list[str]:
    """Collect up to ``limit`` distinct same-origin links whose href contains a marker.

    Order-preserving and de-duplicated so the sampled set is deterministic per version.
    """
    try:
        hrefs = page.eval_on_selector_all(
            "a[href]", "els => els.map(e => e.getAttribute('href'))"
        )
    except Exception:
        hrefs = []
    origin = "{0.scheme}://{0.netloc}".format(urlparse(base_url))
    seen: list[str] = []
    seen_set: set[str] = set()
    for h in hrefs:
        if not h or path_contains not in h:
            continue
        full = urljoin(base_url + "/", h)
        if urlparse(full).netloc != urlparse(origin).netloc:
            continue
        if full in seen_set:
            continue
        seen_set.add(full)
        seen.append(full)
        if len(seen) >= limit:
            break
    return seen


def _visit_articles(page, candidate_urls: list[str], page_type: str,
                    limit: int) -> Iterator[tuple[str, str]]:
    """Visit candidate article URLs, skipping 4xx/5xx and dupes, until ``limit`` succeed.

    Over-provisioning the candidate list and stopping at ``limit`` *successful* pages makes
    the sampled set robust to navigation pseudo-links (e.g. "Ongoing events") that 404.
    """
    yielded = 0
    seen_ids: set[str] = set()
    for url in candidate_urls:
        if yielded >= limit:
            break
        pid = _slug(url, page_type)
        if pid in seen_ids:
            continue
        try:
            resp = page.goto(url, wait_until="commit")
            _settle(page)
            if resp is not None and resp.status >= 400:
                continue
        except Exception:
            continue
        seen_ids.add(pid)
        yielded += 1
        yield (page_type, pid)


# --------------------------------------------------------------------------------------
# Wiki
# --------------------------------------------------------------------------------------

def wiki_targets(page, base_url: str, limits: dict) -> Iterator[tuple[str, str]]:
    base = base_url.rstrip("/")

    page.goto(base, wait_until="commit")
    _settle(page)
    yield ("index", "home")

    # Curated seed titles first (all resolve, content-rich, identical across versions),
    # then discovered index links as backfill/variety. _visit_articles skips any 404s.
    candidates = [f"{base}/wiki/{t.replace(' ', '%20')}" for t in WIKI_SEED_TITLES]
    discovered = _discover_links(page, base, "/wiki/", 3 * limits["article"])
    candidates += [u for u in discovered if u not in candidates]
    yield from _visit_articles(page, candidates, "article", limits["article"])


# --------------------------------------------------------------------------------------
# News
# --------------------------------------------------------------------------------------

def news_targets(page, base_url: str, limits: dict) -> Iterator[tuple[str, str]]:
    base = base_url.rstrip("/")

    page.goto(base, wait_until="commit")
    _settle(page)
    yield ("index", "home")

    try:
        page.goto(f"{base}/browse", wait_until="commit")
        _settle(page)
        yield ("browse", "page1")
    except Exception:
        pass

    for q in NEWS_SEARCH_QUERIES:
        try:
            page.goto(f"{base}/search?q={q.replace(' ', '+')}", wait_until="commit")
            _settle(page)
            yield ("search", q.replace(" ", "-"))
        except Exception:
            continue

    # Article links appear on the index and browse hubs (href contains /news/).
    # Over-provision candidates from both, then visit until we have `limit` good pages.
    page.goto(f"{base}/browse", wait_until="commit")
    _settle(page)
    candidates = _discover_links(page, base, "/news/", 3 * limits["article"])
    page.goto(base, wait_until="commit")
    _settle(page)
    for u in _discover_links(page, base, "/news/", 3 * limits["article"]):
        if u not in candidates:
            candidates.append(u)
    yield from _visit_articles(page, candidates, "article", limits["article"])


# --------------------------------------------------------------------------------------
# Webshop (UI-driven: session/asin/keywords are embedded in URLs, so we click through)
# --------------------------------------------------------------------------------------

def _webshop_search(page, base: str, query: str) -> bool:
    """From the search page, run a text search. Returns True if results loaded."""
    page.goto(base, wait_until="commit")
    _settle(page)
    # The primary search box is the visible non-hidden text input on the search page.
    box = None
    for sel in ('input[name="search_query"]:visible', 'input[type="text"]:visible',
                'input[type="search"]:visible', 'textarea:visible'):
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                box = loc
                break
        except Exception:
            continue
    if box is None:
        return False
    try:
        box.fill(query)
        box.press("Enter")
        _settle(page)
        return True
    except Exception:
        return False


def webshop_targets(page, base_url: str, limits: dict) -> Iterator[tuple[str, str]]:
    base = base_url.rstrip("/")

    page.goto(base, wait_until="commit")
    _settle(page)
    yield ("search", "home")

    n_results = min(limits["results"], len(WEBSHOP_QUERIES))
    for qi in range(n_results):
        query = WEBSHOP_QUERIES[qi]
        qid = query.replace(" ", "-")
        if not _webshop_search(page, base, query):
            continue
        yield ("results", qid)

        if qi >= limits["item"]:
            continue
        # Open the first product -> item page; remember its URL for sub-tab re-entry.
        # Navigate by href rather than clicking: modern themes animate continuously
        # (hero carousel, <marquee>), so Playwright's actionability wait can time out on
        # a perfectly valid link. Following the href is deterministic and equivalent.
        try:
            link = page.locator('a[href*="item_page"]').first
            if link.count() == 0:
                continue
            href = link.get_attribute("href")
            if not href:
                continue
            page.goto(urljoin(base + "/", href), wait_until="commit")
            _settle(page)
            item_url = page.url
            yield ("item", qid)
        except Exception:
            continue

        # Visit each detail sub-tab. Older themes (2000-2010) POST to a separate sub-page;
        # modern themes (2015/2025) toggle an in-page panel via a data-tab button and never
        # navigate. Re-loading the item page before each click keeps BOTH patterns robust
        # (go_back() would leave the item page entirely for the in-page-tab themes).
        for sub in ("Description", "Features", "Attributes", "Reviews"):
            try:
                page.goto(item_url, wait_until="commit")
                _settle(page)
                btn = page.locator(
                    f'[data-tab="{sub.lower()}"], button:has-text("{sub}"), a:has-text("{sub}")'
                ).first
                if btn.count() == 0:
                    continue
                try:
                    btn.click(timeout=5000)
                except Exception:
                    # animated themes can fail the actionability wait; bypass it
                    btn.click(force=True, timeout=5000)
                _settle(page)
                yield (sub.lower(), qid)
            except Exception:
                continue


TARGETS = {
    "wiki": wiki_targets,
    "news": news_targets,
    "webshop": webshop_targets,
}


__all__ = ["TARGETS", "DEFAULT_LIMITS", "wiki_targets", "news_targets", "webshop_targets"]
