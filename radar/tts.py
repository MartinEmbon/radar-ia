"""Convierte un guion de texto en un MP3.

Uso: python -m radar.tts work/guion.txt work/radar.mp3
Proveedor (env TTS_PROVIDER): openai (default) | elevenlabs | none
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

OPENAI_INSTRUCTIONS = (
    "Hablá en español rioplatense de Argentina, con voseo y tono de podcast tranquilo, "
    "cercano y claro. Ritmo natural, ni apurado ni lento. Pausas breves entre temas."
)


def chunk_text(text: str, limit: int) -> list[str]:
    """Parte el texto en bloques <= limit, respetando párrafos y después oraciones."""
    pieces: list[str] = []
    for para in [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]:
        if len(para) <= limit:
            pieces.append(para)
            continue
        current = ""
        for sentence in re.split(r"(?<=[.!?…])\s+", para):
            while len(sentence) > limit:  # oración absurdamente larga
                pieces.append(sentence[:limit])
                sentence = sentence[limit:]
            if current and len(current) + 1 + len(sentence) > limit:
                pieces.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            pieces.append(current)

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if current and len(current) + 2 + len(piece) > limit:
            chunks.append(current)
            current = piece
        else:
            current = f"{current}\n\n{piece}".strip()
    if current:
        chunks.append(current)
    return chunks


def post_with_retry(url: str, **kwargs) -> requests.Response:
    for attempt in range(4):
        resp = requests.post(url, timeout=120, **kwargs)
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < 3:
            time.sleep(2 ** (attempt + 1))
            continue
        if not resp.ok:
            raise RuntimeError(f"TTS {resp.status_code}: {resp.text[:300]}")
        return resp
    raise RuntimeError("TTS: demasiados reintentos")


def openai_tts(text: str) -> bytes:
    resp = post_with_retry(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY'].strip()}"},
        json={
            "model": os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
            "voice": os.getenv("OPENAI_TTS_VOICE", "ash"),
            "input": text,
            "instructions": os.getenv("OPENAI_TTS_INSTRUCTIONS", OPENAI_INSTRUCTIONS),
            "response_format": "mp3",
        },
    )
    return resp.content


def elevenlabs_tts(text: str) -> bytes:
    voice = os.environ["ELEVENLABS_VOICE_ID"].strip()
    resp = post_with_retry(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"].strip()},
        json={
            "text": text,
            "model_id": os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
        },
    )
    return resp.content


PROVIDERS = {
    "openai": (openai_tts, 3500),
    "elevenlabs": (elevenlabs_tts, 2500),
}


def join_mp3(parts: list[Path], out: Path) -> None:
    if len(parts) == 1:
        shutil.copy(parts[0], out)
        return
    if shutil.which("ffmpeg"):
        listing = out.with_suffix(".txt")
        listing.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(listing), "-c", "copy", str(out)],
            check=True,
        )
        listing.unlink()
    else:  # MP3 tolera concatenación cruda; ffmpeg solo deja los headers prolijos
        out.write_bytes(b"".join(p.read_bytes() for p in parts))


def synthesize(script: Path, out: Path, provider: str) -> Path | None:
    if provider == "none":
        print("TTS desactivado (TTS_PROVIDER=none).")
        return None
    if provider not in PROVIDERS:
        raise SystemExit(f"TTS_PROVIDER desconocido: {provider}")
    fn, limit = PROVIDERS[provider]
    chunks = chunk_text(script.read_text(), limit)
    print(f"TTS {provider}: {len(chunks)} bloques, {sum(map(len, chunks))} caracteres")
    with tempfile.TemporaryDirectory() as tmp:
        parts = []
        for i, chunk in enumerate(chunks):
            part = Path(tmp) / f"part-{i:03d}.mp3"
            part.write_bytes(fn(chunk))
            parts.append(part)
        out.parent.mkdir(parents=True, exist_ok=True)
        join_mp3(parts, out)
    print(f"Audio listo: {out} ({out.stat().st_size // 1024} KB)")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: python -m radar.tts <guion.txt> <salida.mp3>")
    synthesize(Path(sys.argv[1]), Path(sys.argv[2]), os.getenv("TTS_PROVIDER", "openai"))
