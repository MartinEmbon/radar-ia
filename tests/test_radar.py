import datetime as dt
import json
from types import SimpleNamespace

from radar import collect, render, telegram, tts

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>
<item><title>New MCP server for agents</title><link>https://ex.com/a?utm_source=x</link>
<pubDate>{recent}</pubDate><description>&lt;p&gt;Agents &amp; tools&lt;/p&gt;</description></item>
<item><title>Gardening tips</title><link>https://ex.com/b</link><pubDate>{recent}</pubDate></item>
<item><title>Old LLM news</title><link>https://ex.com/c</link><pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate></item>
</channel></rss>"""


def fake_get(content=b"", payload=None):
    return lambda url, **kw: SimpleNamespace(content=content, json=lambda: payload)


def test_normalize_url_strips_tracking():
    assert collect.normalize_url("https://WWW.Ex.com/a/?utm_source=x&id=3") == "https://ex.com/a?id=3"
    assert collect.normalize_url("https://martinfowler.com/articles/x/#Part2").endswith("#Part2")


def test_keyword_regex_word_boundaries():
    kw = collect.keyword_regex(["ai", "mcp", "hugging face"])
    assert kw.search("New AI model")
    assert kw.search("Hugging Face releases")
    assert not kw.search("Said the captain")  # "ai" dentro de una palabra


def test_rss_filters_by_date_and_keywords(monkeypatch):
    recent = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    monkeypatch.setattr(collect, "http_get", fake_get(RSS.replace(b"{recent}", recent.encode())))
    since = collect.now_utc() - dt.timedelta(hours=48)
    kw = collect.keyword_regex(["mcp", "llm"])
    items = collect.from_rss({"name": "T", "url": "u", "filter": True}, since, kw)
    assert [i.title for i in items] == ["New MCP server for agents"]
    assert items[0].summary == "Agents & tools"


def test_hacker_news_keyword_and_fallback_url(monkeypatch):
    hits = [
        {"objectID": "1", "title": "Show HN: Claude Code plugin", "url": None, "points": 300, "num_comments": 40, "created_at": "x"},
        {"objectID": "2", "title": "Rust 2.0 released", "url": "https://r.s", "points": 900, "created_at": "x"},
    ]
    monkeypatch.setattr(collect, "http_get", fake_get(payload={"hits": hits}))
    items = collect.from_hacker_news({}, collect.now_utc(), collect.keyword_regex(["claude"]))
    assert len(items) == 1 and items[0].url == "https://news.ycombinator.com/item?id=1"


def test_collect_dedupes_against_seen(monkeypatch):
    item = collect.Item(title="x", url="https://ex.com/a", source="s", kind="rss")
    monkeypatch.setattr(collect, "from_rss", lambda *a: [item, item])
    cfg = {"rss": [{"name": "s", "url": "u"}]}
    fresh, errors, attempted = collect.collect(cfg, {})
    assert len(fresh) == 1 and attempted == 1
    fresh, _, _ = collect.collect(cfg, {item.key: "2099-01-01"})
    assert fresh == []


def test_collect_survives_failing_source(monkeypatch):
    def boom(*a):
        raise TimeoutError("timeout")
    monkeypatch.setattr(collect, "from_rss", boom)
    fresh, errors, attempted = collect.collect({"rss": [{"name": "s", "url": "u"}]}, {})
    assert fresh == [] and errors == ["s: timeout"] and attempted == 1


def test_main_writes_outputs(tmp_path, monkeypatch):
    item = collect.Item(title="x", url="https://ex.com/a", source="s", kind="rss")
    monkeypatch.setattr(collect, "from_rss", lambda *a: [item])
    cfg = tmp_path / "s.yaml"
    cfg.write_text("rss:\n  - {name: s, url: u}\ncheck_pages: [https://www.anthropic.com/news]\n")
    out, state = tmp_path / "items.json", tmp_path / "seen.json"
    assert collect.main(["--config", str(cfg), "--out", str(out), "--state", str(state)]) == 0
    data = json.loads(out.read_text())
    assert data["items"][0]["url"] == "https://ex.com/a" and data["check_pages"]
    assert item.key in json.loads(state.read_text())


def test_render_spanish_dates(monkeypatch):
    monkeypatch.setenv("NOTES_DIR", "vault/Radar/")
    v = render.variables(dt.date(2026, 11, 20))
    assert v["DATE_LONG"] == "viernes 20 de noviembre de 2026"
    assert v["WEEK"] == "2026-W47" and v["WEEK_START"] == "2026-11-14"
    assert v["NOTES_DIR"] == "vault/Radar"
    text = render.render("prompts/daily.md", dt.date(2026, 11, 20))
    assert "$DATE" not in text and "vault/Radar/2026-11-20.md" in text


def test_chunk_text_respects_limit():
    text = "\n\n".join(["Oración uno. " * 40, "Corto.", "Otra cosa! " * 100])
    chunks = tts.chunk_text(text, 500)
    assert all(len(c) <= 500 for c in chunks)
    assert "".join(chunks).replace(" ", "").replace("\n", "") == text.replace(" ", "").replace("\n", "")


def test_telegram_message_escapes_html():
    msg = telegram.build_message(
        "2026-11-20",
        {"resumen": "Agentes <everywhere>", "titulares": [{"titulo": "A & B", "url": "https://x.com/?a=1&b=2"}]},
        "https://github.com/x/y",
    )
    assert "Agentes &lt;everywhere&gt;" in msg
    assert '<a href="https://x.com/?a=1&amp;b=2">A &amp; B</a>' in msg
    assert "Nota completa" in msg


def test_same_day_rerun_keeps_todays_items(monkeypatch):
    item = collect.Item(title="x", url="https://ex.com/a", source="s", kind="rss")
    monkeypatch.setattr(collect, "from_rss", lambda *a: [item])
    cfg = {"rss": [{"name": "s", "url": "u"}]}
    fresh, _, _ = collect.collect(cfg, {item.key: collect.local_today()})
    assert len(fresh) == 1
    fresh, _, _ = collect.collect(cfg, {item.key: "2000-01-01"})
    assert fresh == []
