#!/usr/bin/env bash
# Corre el radar completo en tu máquina, escribiendo directo en tu vault de Obsidian.
# Uso: scripts/run_local.sh [--weekly] [--no-telegram]
set -euo pipefail
cd "$(dirname "$0")/.."

[ -f .env ] || { echo "Falta .env (copiá .env.example)"; exit 1; }
set -a; source .env; set +a

WEEKLY=false; TELEGRAM=true
for arg in "$@"; do
  case "$arg" in
    --weekly) WEEKLY=true ;;
    --no-telegram) TELEGRAM=false ;;
  esac
done

export DATE="$(date +%F)"
export NOTES_DIR="${OBSIDIAN_VAULT:?definí OBSIDIAN_VAULT en .env}/Radar"
mkdir -p "$NOTES_DIR/Semanal" "$NOTES_DIR/NexoSalud" work
rm -f work/guion*.txt work/headlines*.json work/nexosalud_sin_novedades.txt

python -m radar.collect
bash scripts/run_claude.sh prompts/daily.md
bash scripts/run_claude.sh prompts/nexosalud.md || echo "⚠️  Falló el radar NexoSalud, sigo igual"
[ "$WEEKLY" = true ] && bash scripts/run_claude.sh prompts/weekly.md

python -m radar.tts work/guion.txt "work/radar-$DATE.mp3" || echo "⚠️  Falló el audio, sigo igual"
[ -s work/guion_semanal.txt ] && python -m radar.tts work/guion_semanal.txt "work/radar-semanal-$DATE.mp3"

NOTE_URL="obsidian://open?path=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$OBSIDIAN_VAULT/Radar/$DATE.md")"
if [ "$TELEGRAM" = true ]; then
  python -m radar.telegram --date "$DATE" --audio "work/radar-$DATE.mp3" "work/radar-semanal-$DATE.mp3"
  if [ -s work/headlines_nexosalud.json ]; then
    [ -s work/guion_nexosalud.txt ] && python -m radar.tts work/guion_nexosalud.txt "work/nexosalud-$DATE.mp3"
    python -m radar.telegram --date "$DATE" --name "Radar NexoSalud" --icon "🩺" \
      --headlines work/headlines_nexosalud.json --audio "work/nexosalud-$DATE.mp3"
  fi
fi
echo "Listo. Nota: $NOTE_URL"
