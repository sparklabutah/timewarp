"""Query TimeWarp's environment content offline, to spot-check gold answers.

The three sites are backed by static content: the wiki and news Flask apps read
pre-parsed article indexes (``env/wiki/wiki_index.pkl``,
``env/news/news_index.pkl``) and WebShop reads a product catalogue
(``env/webshop/data/items_shuffle_1000.json``). Reading them directly is much
cheaper than booting the servers and driving a browser.

    # is there an article, and what does it say about a term?
    python scripts/annotation/env_lookup.py wiki --title "Borough" --grep Alaska
    python scripts/annotation/env_lookup.py wiki --search borough --limit 10

    # news articles, optionally restricted to a year
    python scripts/annotation/env_lookup.py news --search Morocco --year 2009

    # products by name, with price and category
    python scripts/annotation/env_lookup.py shop --search "Type-C to HDMI"

The wiki index is ~470MB and takes a while to load, so batch your questions
into one invocation with repeated --title/--search/--grep flags rather than
running the command once per question.
"""

import argparse
import html
import json
import pickle
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WIKI_INDEX = REPO_ROOT / "env" / "wiki" / "wiki_index.pkl"
NEWS_INDEX = REPO_ROOT / "env" / "news" / "news_index.pkl"
SHOP_ITEMS = REPO_ROOT / "env" / "webshop" / "data" / "items_shuffle_1000.json"

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t]+")


def to_text(markup: str) -> str:
    """Strip tags from the pre-parsed HTML the apps serve."""
    text = _TAG.sub(" ", markup or "")
    text = html.unescape(text)
    text = _WS.sub(" ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def show_matches(name: str, text: str, patterns: list, context: int) -> None:
    for pattern in patterns:
        hits = list(re.finditer(re.escape(pattern), text, re.IGNORECASE))
        print(f"  grep {pattern!r}: {len(hits)} hit(s)")
        for hit in hits[:5]:
            start = max(0, hit.start() - context)
            end = min(len(text), hit.end() + context)
            snippet = text[start:end].replace("\n", " ")
            print(f"    ...{snippet}...")


def load_wiki() -> dict:
    if not WIKI_INDEX.exists():
        raise SystemExit(f"{WIKI_INDEX} missing -- run ./setup.sh to download it")
    print(f"loading {WIKI_INDEX.name} (large, be patient)...", file=sys.stderr)
    with WIKI_INDEX.open("rb") as handle:
        return pickle.load(handle)


def load_news() -> dict:
    if not NEWS_INDEX.exists():
        raise SystemExit(f"{NEWS_INDEX} missing -- run ./setup.sh to download it")
    with NEWS_INDEX.open("rb") as handle:
        payload = pickle.load(handle)
    return payload.get("index", payload)


def run_articles(index: dict, args, extra=None) -> None:
    print(f"{len(index)} articles indexed\n")

    for needle in args.search or []:
        matches = [key for key in index if needle.lower() in key]
        print(f"search {needle!r}: {len(matches)} title match(es)")
        for key in sorted(matches)[: args.limit]:
            record = index[key]
            suffix = f"  [{extra(record)}]" if extra else ""
            print(f"  - {record.get('title', key)}{suffix}")
        print()

    for title in args.title or []:
        record = index.get(title.lower())
        if record is None:
            close = [k for k in index if title.lower() in k][:5]
            print(f"title {title!r}: NOT FOUND" + (f" (close: {close})" if close else ""))
            print()
            continue
        text = to_text(record.get("html", ""))
        print(f"title {title!r}: found, {len(text)} chars" + (f"  [{extra(record)}]" if extra else ""))
        if args.grep:
            show_matches(title, text, args.grep, args.context)
        else:
            print(f"  {text[: args.chars]}")
        print()

    for needle in args.grep_all or []:
        hits = [
            index[key].get("title", key)
            for key in index
            if needle.lower() in to_text(index[key].get("html", "")).lower()
        ]
        print(f"grep-all {needle!r}: {len(hits)} article(s)")
        for title in hits[: args.limit]:
            print(f"  - {title}")
        print()


def run_shop(args) -> None:
    if not SHOP_ITEMS.exists():
        raise SystemExit(f"{SHOP_ITEMS} missing -- run env/webshop/setup.sh")
    items = json.loads(SHOP_ITEMS.read_text())
    print(f"{len(items)} products indexed\n")

    for needle in args.search or []:
        matches = [
            item
            for item in items
            if needle.lower() in (item.get("name") or "").lower()
            or needle.lower() in (item.get("full_description") or "").lower()
        ]
        print(f"search {needle!r}: {len(matches)} product(s)")
        for item in matches[: args.limit]:
            print(f"  - {item.get('name', '')[:100]}")
            print(
                f"      price={item.get('pricing') or 'n/a'} "
                f"list={item.get('list_price') or 'n/a'} "
                f"rating={item.get('average_rating') or 'n/a'} "
                f"category={(item.get('product_category') or '')[:60]}"
            )
            if args.grep:
                blob = json.dumps(item)
                for pattern in args.grep:
                    found = re.findall(
                        r".{0,80}" + re.escape(pattern) + r".{0,80}", blob, re.IGNORECASE
                    )
                    print(f"      grep {pattern!r}: {len(found)} hit(s)")
                    for snippet in found[:3]:
                        print(f"        ...{snippet}...")
            if args.full:
                print(f"      {json.dumps(item, indent=2)[: args.chars]}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="site", required=True)

    def common(p):
        p.add_argument("--search", action="append", help="substring match (repeatable)")
        p.add_argument("--grep", action="append", help="find a term inside the matched records")
        p.add_argument("--limit", type=int, default=20)
        p.add_argument("--chars", type=int, default=1500)
        p.add_argument("--context", type=int, default=110)

    wiki = sub.add_parser("wiki")
    common(wiki)
    wiki.add_argument("--title", action="append", help="exact article title (repeatable)")
    wiki.add_argument("--grep-all", action="append", help="scan every article's body (slow)")

    news = sub.add_parser("news")
    common(news)
    news.add_argument("--title", action="append")
    news.add_argument("--grep-all", action="append")
    news.add_argument("--year", type=int, help="restrict to a publication year (from 'date')")

    shop = sub.add_parser("shop")
    common(shop)
    shop.add_argument("--full", action="store_true", help="dump the whole product record")

    args = parser.parse_args()

    if args.site == "wiki":
        run_articles(load_wiki(), args)
    elif args.site == "news":
        index = load_news()
        # The stored 'year' field is unreliable (most records carry the dump year
        # 2024); 'date' holds the real publication date the site displays.
        if args.year:
            index = {k: v for k, v in index.items() if str(v.get("date"))[:4] == str(args.year)}
            print(f"restricted to publication year {args.year}: {len(index)} articles")
        run_articles(
            index, args, extra=lambda r: f"{str(r.get('date'))[:10]} {r.get('categories', '')[:60]}"
        )
    else:
        run_shop(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
