"""Envía el radar por Telegram: titulares + audio(s).

Uso:
  python -m radar.telegram --date 2026-11-20 --note-url URL [--audio a.mp3 ...] [--dry-run]
  python -m radar.telegram --whoami   # muestra el chat_id después de escribirle al bot
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
from pathlib import Path

import requests

API = "https://api.telegram.org/bot{token}/{method}"


def call(method: str, *, data: dict, files: dict | None = None) -> dict:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    resp = requests.post(API.format(token=token, method=method), data=data, files=files, timeout=120)
    body = resp.json()
    if not body.get("ok"):
        raise RuntimeError(f"Telegram {method}: {body.get('description')}")
    return body["result"]


def build_message(date: str, headlines: dict, note_url: str | None, weekly: bool = False) -> str:
    title = "Radar IA · resumen semanal" if weekly else f"Radar IA · {date}"
    lines = [f"<b>🛰️ {html.escape(title)}</b>"]
    if headlines.get("resumen"):
        lines += ["", html.escape(headlines["resumen"])]
    items = headlines.get("titulares", [])
    if items:
        lines.append("")
        for i, h in enumerate(items, 1):
            text = html.escape(h.get("titulo", "").strip())
            url = h.get("url", "").strip()
            lines.append(f'{i}. <a href="{html.escape(url, quote=True)}">{text}</a>' if url else f"{i}. {text}")
    if note_url:
        lines += ["", f'📝 <a href="{html.escape(note_url, quote=True)}">Nota completa</a>']
    return "\n".join(lines)[:4000]


def send(date: str, headlines: dict, note_url: str | None, audios: list[Path], dry_run: bool) -> None:
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    message = build_message(date, headlines, note_url)
    if dry_run:
        print("— mensaje —\n" + message)
        for a in audios:
            print(f"— audio — {a}")
        return
    call("sendMessage", data={
        "chat_id": chat_id, "text": message, "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    })
    for audio in audios:
        weekly = "semanal" in audio.name
        with audio.open("rb") as fh:
            call("sendAudio", data={
                "chat_id": chat_id,
                "title": f"Radar IA {'semanal' if weekly else date}",
                "performer": "Radar IA",
            }, files={"audio": (audio.name, fh, "audio/mpeg")})
    print(f"Enviado a Telegram: mensaje + {len(audios)} audio(s)")


def whoami() -> None:
    updates = call("getUpdates", data={})
    chats = {u["message"]["chat"]["id"]: u["message"]["chat"] for u in updates if "message" in u}
    if not chats:
        print("No hay mensajes. Escribile cualquier cosa a tu bot y volvé a correr esto.")
    for chat_id, chat in chats.items():
        name = chat.get("username") or chat.get("title") or chat.get("first_name")
        print(f"TELEGRAM_CHAT_ID={chat_id}   ({name})")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--date")
    p.add_argument("--headlines", default="work/headlines.json")
    p.add_argument("--note-url")
    p.add_argument("--audio", nargs="*", default=[])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--whoami", action="store_true")
    args = p.parse_args()

    if args.whoami:
        whoami()
        return 0
    if not args.date:
        p.error("--date es obligatorio")
    path = Path(args.headlines)
    headlines = json.loads(path.read_text()) if path.exists() else {}
    audios = [Path(a) for a in args.audio if Path(a).exists()]
    send(args.date, headlines, args.note_url, audios, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
