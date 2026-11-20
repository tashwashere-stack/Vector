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
  persona.md            The live system prompt (keep it short: it's sent every turn)
  behaviour.json        Example exchanges, sent as few-shot conversation turns
  personality.json      Full persona design notes (reference; persona.md is the distilled version)
  memory.example.json   Template for your private memory.json
knowledge/              Drop PDFs here; they become Vector's knowledge base
tests/                  Unit tests (stdlib unittest)
```

Generated files live in `.cache/` (extracted PDF text, rebuilt automatically when PDFs change).

## Configuration

Edit [`vector/config.py`](vector/config.py):

| Setting | Default | Meaning |
|---|---|---|
| `MODEL` | `mistral` | Any model you've pulled in Ollama (`llama3.2:3b`, `qwen2.5:3b`, `gemma3:4b` are faster) |
| `MAX_HISTORY` | `4` | Exchanges kept in short-term memory |
| `MAX_REPLY_TOKENS` | `80` | Hard cap on reply length |
| `TEMPERATURE` | `0.7` | Lower = more focused, higher = more random |
| `KEEP_ALIVE` | `30m` | How long Ollama keeps the model loaded between messages |
| `WARM_UP` | `True` | Load the model and cache the static prompt at startup |
| `USE_INTENT_STEP` | `False` | Extra model call to infer intent before replying |
| `SPEAK` | `True` | Read replies aloud (macOS only) |

## How it stays fast

- **Small, static prompt.** `persona.md`, a condensed crewmate summary and the `behaviour.json` examples form a prefix that never changes during a session, so Ollama caches it and only processes the new message each turn.
- **Per-message context goes in the user turn.** PDF excerpts are added only when a chunk covers at least half of the question's key terms.
- **Streaming.** Words print as they're generated, and speech runs sentence by sentence on a background thread.

To give Vector a hand-written profile instead of the auto-condensed one, add a `"summary": "..."` string to `data/memory.json`.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests
```
