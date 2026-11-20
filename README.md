# Vector

A local AI crewmate: a terminal chat agent with an alien-engineer persona, running on a local model through [Ollama](https://ollama.com) and speaking replies aloud with macOS `say`.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
ollama pull mistral
ollama serve   # if not already running
```

## Run

```bash
.venv/bin/python main.py
```

Type `exit` (or Ctrl-D) to quit.

## Files

| File | Purpose |
|---|---|
| `main.py` | Chat loop, memory, PDF retrieval, Ollama calls, speech |
| `rocky_personality.json` | Persona spec injected into the system prompt |
| `behaviour_dataset.json` | Example response styles per situation |
| `vector_memory.json` | Your profile + recent conversation (**private, git-ignored**) |
| `*.pdf` | Knowledge base; text is cached in `pdf_cache.txt` (git-ignored, rebuilt automatically when PDFs change) |

Settings (model, history length, intent step, speech) are constants at the top of `main.py`.
