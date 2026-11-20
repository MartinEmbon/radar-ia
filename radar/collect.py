"""Recolecta novedades de IA desde RSS, Hacker News y GitHub.

Salida: work/items.json (lista de items nuevos, sin repetidos respecto de state/seen.json).
Uso: python -m radar.collect [--config config/sources.yaml] [--out work/items.json]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import requests
import yaml

UA = "radar-ia/1.0 (personal news digest)"
TIMEOUT = 20
SEEN_RETENTION_DAYS = 45
TRACKING_PARAMS = {"ref", "ref_src", "source", "fbclid", "gclid", "mc_cid", "mc_eid"}


@dataclass
class Item:
    title: str
    url: str
    source: str
    kind: str  # rss | hn | github
    published: str | None = None
    summary: str = ""
    signals: dict = field(default_factory=dict)

    @property
    def key(self) -> str:
        return hashlib.sha256(normalize_url(self.url).encode()).hexdigest()[:16]


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower().removeprefix("www."), path, urlencode(query), ""))


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def keyword_regex(keywords: list[str]) -> re.Pattern:
    escaped = [re.escape(k.lower()) for k in keywords]
    return re.compile(r"(?<![a-z0-9])(" + "|".join(escaped) + r")(?![a-z0-9])", re.IGNORECASE)


def http_get(url: str, **kwargs) -> requests.Response:
    headers = {"User-Agent": UA, **kwargs.pop("headers", {})}
    resp = requests.get(url, headers=headers, timeout=TIMEOUT, **kwargs)
    resp.raise_for_status()
    return resp


# ---------------------------------------------------------------- fuentes


def from_rss(src: dict, since: dt.datetime, kw: re.Pattern) -> list[Item]:
    feed = feedparser.parse(http_get(src["url"]).content)
    if feed.bozo and not feed.entries:
        raise ValueError(f"feed inválido: {feed.bozo_exception}")
    out: list[Item] = []
    for entry in feed.entries[: src.get("max", 15)]:
        stamp = entry.get("published_parsed") or entry.get("updated_parsed")
        published = dt.datetime(*stamp[:6], tzinfo=dt.timezone.utc) if stamp else None
        if published and published < since:
            continue
        title = strip_html(entry.get("title", ""))
        summary = strip_html(entry.get("summary", ""))[:700]
        link = entry.get("link")
        if not title or not link:
            continue
        if src.get("filter") and not kw.search(f"{title} {summary}"):
            continue
        out.append(
            Item(
                title=title,
                url=link,
                source=src["name"],
                kind="rss",
                published=published.isoformat() if published else None,
                summary=summary,
            )
        )
    if "keep" in src:
        out = out[: src["keep"]]
    return out


def from_hacker_news(cfg: dict, since: dt.datetime, kw: re.Pattern) -> list[Item]:
    params = {
        "tags": "story",
        "numericFilters": f"created_at_i>{int(since.timestamp())},points>={cfg.get('min_points', 80)}",
        "hitsPerPage": 200,
    }
    hits = http_get("https://hn.algolia.com/api/v1/search_by_date", params=params).json()["hits"]
    hits.sort(key=lambda h: h.get("points") or 0, reverse=True)
    out: list[Item] = []
    for hit in hits:
        title = hit.get("title") or ""
        if not kw.search(title):
            continue
        discussion = f"https://news.ycombinator.com/item?id={hit['objectID']}"
        out.append(
            Item(
                title=title,
                url=hit.get("url") or discussion,
                source="Hacker News",
                kind="hn",
                published=hit.get("created_at"),
                signals={
                    "points": hit.get("points"),
                    "comments": hit.get("num_comments"),
                    "discussion": discussion,
                },
            )
        )
        if len(out) >= cfg.get("max", 15):
            break
    return out


def from_github(cfg: dict, token: str | None) -> list[Item]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    created = (now_utc() - dt.timedelta(days=cfg.get("created_within_days", 10))).date().isoformat()
    seen: set[str] = set()
    out: list[Item] = []
    failures: list[str] = []
    queries = cfg.get("queries", [])
    for query in queries:
        params = {
            "q": f"{query} created:>={created} stars:>={cfg.get('min_stars', 40)}",
            "sort": "stars",
            "order": "desc",
            "per_page": cfg.get("max_per_query", 5),
        }
        try:
            data = http_get("https://api.github.com/search/repositories", params=params, headers=headers).json()
        except Exception as exc:
            failures.append(f"{query}: {exc}")
            continue
        for repo in data.get("items", []):
            if repo["full_name"] in seen:
                continue
            seen.add(repo["full_name"])
            out.append(
                Item(
                    title=f"{repo['full_name']}: {repo.get('description') or 'sin descripción'}",
                    url=repo["html_url"],
                    source="GitHub",
                    kind="github",
                    published=repo.get("created_at"),
                    summary=(repo.get("description") or "")[:400],
                    signals={
                        "stars": repo.get("stargazers_count"),
                        "language": repo.get("language"),
                        "topics": repo.get("topics", [])[:8],
                        "query": query,
                    },
                )
            )
    if queries and len(failures) == len(queries):
        raise RuntimeError("; ".join(failures))
    return out


# ---------------------------------------------------------------- estado


def load_seen(path: Path) -> dict[str, str]:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def prune_seen(seen: dict[str, str]) -> dict[str, str]:
    cutoff = (now_utc() - dt.timedelta(days=SEEN_RETENTION_DAYS)).date().isoformat()
    return {k: v for k, v in seen.items() if v >= cutoff}


# ---------------------------------------------------------------- main


def collect(config: dict, seen: dict[str, str]) -> tuple[list[Item], list[str], int]:
    since = now_utc() - dt.timedelta(hours=config.get("lookback_hours", 48))
    kw = keyword_regex(config.get("keywords", []))
    items: list[Item] = []
    errors: list[str] = []
    attempted = 0

    def run(name: str, fn):
        nonlocal attempted
        attempted += 1
        try:
            got = fn()
            items.extend(got)
            print(f"  ✓ {name}: {len(got)}")
        except Exception as exc:  # una fuente caída no frena el radar
            errors.append(f"{name}: {exc}")
            print(f"  ✗ {name}: {exc}", file=sys.stderr)

    for src in config.get("rss", []):
        run(src["name"], lambda src=src: from_rss(src, since, kw))
    if config.get("hacker_news", {}).get("enabled"):
        run("Hacker News", lambda: from_hacker_news(config["hacker_news"], since, kw))
    if config.get("github", {}).get("enabled"):
        run("GitHub", lambda: from_github(config["github"], os.getenv("GITHUB_TOKEN")))

    unique: dict[str, Item] = {}
    for item in items:
        if item.key in seen or item.key in unique:
            continue
        unique[item.key] = item
    fresh = list(unique.values())[: config.get("max_items_total", 80)]
    return fresh, errors, attempted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/sources.yaml")
    parser.add_argument("--out", default="work/items.json")
    parser.add_argument("--state", default="state/seen.json")
    args = parser.parse_args(argv)

    config = yaml.safe_load(Path(args.config).read_text())
    state_path = Path(args.state)
    seen = prune_seen(load_seen(state_path))

    print("Recolectando fuentes…")
    fresh, errors, attempted = collect(config, seen)

    today = now_utc().date().isoformat()
    for item in fresh:
        seen[item.key] = today

    payload = {
        "generated_at": now_utc().isoformat(),
        "check_pages": config.get("check_pages", []),
        "errors": errors,
        "items": [asdict(i) for i in fresh],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(seen, indent=0, sort_keys=True))

    print(f"Listo: {len(fresh)} items nuevos, {len(errors)} fuentes con error → {out}")
    if attempted and len(errors) == attempted:
        print("Todas las fuentes fallaron; corto acá.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
