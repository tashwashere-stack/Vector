"""Paths and tunables. Paths resolve from the project root, not the cwd."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
KNOWLEDGE_DIR = ROOT / "knowledge"
CACHE_DIR = ROOT / ".cache"

PERSONA_FILE = DATA_DIR / "persona.md"            # the live system prompt
BEHAVIOUR_FILE = DATA_DIR / "behaviour.json"      # few-shot example exchanges
MEMORY_FILE = DATA_DIR / "memory.json"            # private, git-ignored
MEMORY_TEMPLATE = DATA_DIR / "memory.example.json"
CACHE_FILE = CACHE_DIR / "knowledge.txt"

# --- Model ---
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "mistral"            # try llama3.2:3b / qwen2.5:3b / gemma3:4b for ~2x speed
REQUEST_TIMEOUT = 120        # seconds; first call can be slow while the model loads
KEEP_ALIVE = "30m"           # keep the model in memory between messages
NUM_CTX = 4096               # context window; prompt is ~300-900 tokens
TEMPERATURE = 0.7
TOP_P = 0.9
MAX_REPLY_TOKENS = 70
MAX_SENTENCES = 3            # reply is cut (and generation stopped) after this many
STYLE_FILTER = True          # enforce speech quirks: no articles/contractions, ", question?"
STOP = ["\n\n"]             # one paragraph per reply
# Mistral's chat template moves the system prompt into the *latest* user message,
# which defeats Ollama's prompt cache. For those models, send the persona as the
# first exchange instead so it stays a fixed, cacheable prefix.
PERSONA_AS_FIRST_TURN = MODEL.startswith(("mistral", "mixtral"))
WARM_UP = True               # pre-load model + cache the static prompt at startup

# --- Behaviour ---
MAX_HISTORY = 4
USE_INTENT_STEP = False      # extra model call per message; slower, rarely helps
SPEAK = True

# --- Retrieval ---
CHUNK_SIZE = 600
TOP_K = 2
KNOWLEDGE_CHAR_LIMIT = 1000
MIN_TERM_COVERAGE = 0.5      # a chunk must contain at least half the query's key terms
