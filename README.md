# 🛰️ Radar IA

Tu brief diario de novedades de IA: recolecta noticias, Claude Code las filtra según tus
intereses, escribe una nota en Obsidian, la convierte en un audio en español rioplatense
y te la manda por Telegram todas las mañanas. Los viernes suma un resumen semanal.

```
 07:27 GitHub Actions
   │
   ├─ 1. radar.collect   RSS (labs, newsletters, arXiv) + Hacker News + GitHub  → work/items.json
   ├─ 2. Claude Code     lee intereses + items, verifica fuentes con WebFetch
   │      (headless)     → nota Obsidian  ·  guion de audio  ·  titulares
   ├─ 3. viernes         resumen semanal a partir de las notas de la semana
   ├─ 4. radar.tts       guion → MP3 (OpenAI o ElevenLabs)
   ├─ 5. git push        nota al repo del vault (Obsidian Git la baja a tu Mac)
   └─ 6. radar.telegram  titulares + audio a tu celular
```

## Estructura

| Archivo | Para qué |
|---|---|
| `config/sources.yaml` | Fuentes, palabras clave, ventana de tiempo |
| `config/interests.md` | Quién sos y qué te importa; Claude lo usa para filtrar. **Editalo a gusto.** |
| `prompts/daily.md`, `prompts/weekly.md` | Instrucciones y formato de la nota y del guion |
| `radar/collect.py` | Recolector con deduplicación (`state/seen.json`) |
| `radar/tts.py` | Texto → MP3, partido en bloques |
| `radar/telegram.py` | Envío y helper `--whoami` para obtener tu chat id |
| `scripts/run_claude.sh` | Claude Code en modo headless, sin Bash y con tope de gasto |
| `scripts/run_local.sh` | Todo el pipeline en tu Mac, escribiendo directo en tu vault |

## Setup (unos 20 minutos)

### 1. Repo
Creá un repo **privado** `radar-ia` y subí esto.

### 2. Claude
Elegí una opción y guardala como *secret* del repo (Settings → Secrets and variables → Actions):
- `CLAUDE_CODE_OAUTH_TOKEN`: corré `claude setup-token` en tu Mac. Usa tu suscripción de Claude.
- `ANTHROPIC_API_KEY`: pago por uso desde console.anthropic.com.

Cada corrida tiene un tope de gasto de USD 1,50 (variable `CLAUDE_MAX_BUDGET_USD`), y el costo real queda en el log del paso 2.

### 3. Audio
- Por defecto, OpenAI (`gpt-4o-mini-tts` con instrucciones de acento rioplatense): secret `OPENAI_API_KEY`.
- Para mejor voz, ElevenLabs: secret `ELEVENLABS_API_KEY` y variables `TTS_PROVIDER=elevenlabs` y `ELEVENLABS_VOICE_ID` (elegí una voz argentina en su Voice Library).
- Sin audio: variable `TTS_PROVIDER=none`.

### 4. Telegram
1. En Telegram, hablale a `@BotFather`, mandá `/newbot` y copiá el token → secret `TELEGRAM_BOT_TOKEN`.
2. Mandale cualquier mensaje a tu bot nuevo.
3. En tu Mac: `TELEGRAM_BOT_TOKEN=xxx python -m radar.telegram --whoami` → secret `TELEGRAM_CHAT_ID`.

### 5. Obsidian (elegí una)
**A. Vault sincronizado con GitHub (recomendado)**
1. Si tu vault no está en git: creá un repo privado (por ejemplo `obsidian-vault`) e instalá el plugin
   **Obsidian Git** en Obsidian, con *auto pull* cada 10 minutos.
2. Creá un *fine-grained token* con acceso solo a ese repo y permiso `Contents: Read and write`
   → secret `VAULT_TOKEN`.
3. Variable `VAULT_REPO=MartinEmbon/obsidian-vault` (y opcionalmente `VAULT_SUBDIR`, por defecto `Radar`).

**B. Sin vault en git**: las notas quedan en `notes/Radar/` de este mismo repo. Podés abrir esa carpeta como vault
o correr el radar en local con `scripts/run_local.sh`, que escribe directo en tu vault.

### 6. Probar
Actions → **Radar IA** → *Run workflow*. Para probar sin molestar el celular, tildá `skip_telegram`.
Si algo falla, los archivos intermedios quedan como *artifact* de la corrida (`work/`).

## Correr en local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install -g @anthropic-ai/claude-code
cp .env.example .env   # completalo
bash scripts/run_local.sh --no-telegram
```

## Personalizar
- **Horario**: el `cron` en `.github/workflows/radar.yml` está en UTC (07:27 en Argentina = `27 10`).
- **Fuentes**: agregá RSS en `config/sources.yaml`. Si una URL deja de andar, se saltea y queda en `errors` de `items.json`.
- **Qué te importa**: `config/interests.md`. Es lo que más cambia la calidad del radar.
- **Formato de la nota y del audio**: `prompts/daily.md`.
- **Modelo**: variable `CLAUDE_MODEL` (`sonnet` por defecto; `opus` da mejor criterio a mayor costo).

## Seguridad
- Claude corre con `--permission-mode dontAsk` y solo puede leer y escribir archivos del proyecto y navegar la web. No tiene Bash, así que no puede ejecutar comandos.
- El token del vault solo tiene acceso a ese repo.
- Las páginas web que lee Claude son contenido no confiable. Por eso no tiene herramientas peligrosas habilitadas.
