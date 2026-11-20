#!/usr/bin/env bash
# Corre Claude Code en modo headless con un prompt de prompts/.
# Uso: scripts/run_claude.sh prompts/daily.md
# Auth: CLAUDE_CODE_OAUTH_TOKEN (tu suscripción, vía `claude setup-token`) o ANTHROPIC_API_KEY.
set -euo pipefail

PROMPT_FILE="${1:?uso: run_claude.sh <prompt.md>}"

# GitHub Actions pasa los secrets vacíos como "": los saco para que Claude use el que sí existe.
[ -z "${ANTHROPIC_API_KEY:-}" ] && unset ANTHROPIC_API_KEY
[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && unset CLAUDE_CODE_OAUTH_TOKEN
NAME="$(basename "$PROMPT_FILE" .md)"
mkdir -p work "${NOTES_DIR:-notes/Radar}"

PROMPT="$(python -m radar.render "$PROMPT_FILE")"

# dontAsk: rechaza cualquier herramienta fuera de la lista, sin quedarse esperando.
# Sin Bash: el agente solo lee, escribe archivos y navega la web.
claude -p "$PROMPT" \
  --model "${CLAUDE_MODEL:-sonnet}" \
  --allowedTools "Read,Write,Edit,Glob,Grep,WebFetch,WebSearch" \
  --permission-mode dontAsk \
  --add-dir "${NOTES_DIR:-notes/Radar}" \
  --max-budget-usd "${CLAUDE_MAX_BUDGET_USD:-1.50}" \
  --no-session-persistence \
  --output-format json > "work/claude-$NAME.json"

python - "$NAME" <<'PY'
import json, sys
name = sys.argv[1]
data = json.load(open(f"work/claude-{name}.json"))
cost = data.get("total_cost_usd")
print(f"Claude ({name}): {data.get('subtype', '?')}, "
      f"turnos={data.get('num_turns', '?')}, costo≈{'$%.2f' % cost if cost else 'n/d'}")
if data.get("is_error"):
    sys.exit(f"Claude terminó con error: {data.get('result', '')[:500]}")
PY
