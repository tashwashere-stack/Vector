# Vector

A local AI crewmate: a terminal chat agent with an alien-engineer persona (inspired by Rocky from *Project Hail Mary*). It runs fully offline on a local model through [Ollama](https://ollama.com), pulls context from your own PDFs, remembers recent conversation, and speaks replies aloud with macOS `say`.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
ollama pull mistral
ollama serve   # if not already running
.venv/bin/vector
```

You can also run it with `.venv/bin/python -m vector`. Type `exit` (or Ctrl-D) to quit.

On first run, `data/memory.json` is created from `data/memory.example.json`. Edit it to describe yourself; it stays local and is git-ignored.

## Project layout

```
vector/                 Python package
  cli.py                Interactive chat loop (entry point)
  config.py             Paths, model settings, tunables
  llm.py                Ollama /api/chat client
  prompt.py             System prompt and message assembly
  memory.py             Crewmate profile + short-term history
  knowledge.py          PDF extraction, caching, keyword retrieval
  voice.py              Text-to-speech via `say`
  storage.py            JSON helpers
data/
  personality.json      Persona spec
  behaviour.json        Example response styles per situation
  memory.example.json   Template for your private memory.json
knowledge/              Drop PDFs here; they become Vector's knowledge base
tests/                  Unit tests (stdlib unittest)
```

Generated files live in `.cache/` (extracted PDF text, rebuilt automatically when PDFs change).

## Configuration

Edit [`vector/config.py`](vector/config.py):

| Setting | Default | Meaning |
|---|---|---|
| `MODEL` | `mistral` | Any model you've pulled in Ollama |
| `MAX_HISTORY` | `6` | Exchanges kept in short-term memory |
| `MAX_REPLY_TOKENS` | `90` | Hard cap on reply length |
| `USE_INTENT_STEP` | `False` | Extra model call to infer intent before replying |
| `SPEAK` | `True` | Read replies aloud (macOS only) |

## Tests

```bash
.venv/bin/python -m unittest discover -s tests
```
