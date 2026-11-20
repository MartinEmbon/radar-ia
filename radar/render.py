"""Completa las variables de un prompt ($DATE, $NOTES_DIR, …) y lo imprime.

Uso: python -m radar.render prompts/daily.md
"""

from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path
from string import Template
from zoneinfo import ZoneInfo

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def today() -> dt.date:
    if os.getenv("RADAR_DATE"):
        return dt.date.fromisoformat(os.environ["RADAR_DATE"])
    return dt.datetime.now(ZoneInfo(os.getenv("RADAR_TZ", "America/Argentina/Cordoba"))).date()


def variables(day: dt.date | None = None) -> dict[str, str]:
    day = day or today()
    iso_year, iso_week, _ = day.isocalendar()
    return {
        "DATE": day.isoformat(),
        "DATE_LONG": f"{DIAS[day.weekday()]} {day.day} de {MESES[day.month - 1]} de {day.year}",
        "WEEK": f"{iso_year}-W{iso_week:02d}",
        "WEEK_START": (day - dt.timedelta(days=6)).isoformat(),
        "NOTES_DIR": os.getenv("NOTES_DIR", "notes/Radar").rstrip("/"),
    }


def render(path: str | Path, day: dt.date | None = None) -> str:
    return Template(Path(path).read_text()).safe_substitute(variables(day))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("uso: python -m radar.render <prompt.md>")
    if sys.argv[1] == "--var":
        sys.exit("uso: python -m radar.render <prompt.md>")
    print(render(sys.argv[1]))
