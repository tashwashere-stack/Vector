"""Paths and tunables. Paths resolve from the project root, not the cwd."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
KNOWLEDGE_DIR = ROOT / "knowledge"
CACHE_DIR = ROOT / ".cache"

PERSONALITY_FILE = DATA_DIR / "personality.json"
BEHAVIOUR_FILE = DATA_DIR / "behaviour.json"
MEMORY_FILE = DATA_DIR / "memory.json"            # private, git-ignored
MEMORY_TEMPLATE = DATA_DIR / "memory.example.json"
CACHE_FILE = CACHE_DIR / "knowledge.txt"

# --- Model ---
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "mistral"
REQUEST_TIMEOUT = 120  # seconds; first call can be slow while the model loads
TEMPERATURE = 1.0
TOP_P = 0.9
MAX_REPLY_TOKENS = 90

# --- Behaviour ---
MAX_HISTORY = 6
USE_INTENT_STEP = False  # extra model call per message; slower, rarely helps
SPEAK = True

# --- Retrieval ---
CHUNK_SIZE = 600
TOP_K = 3
KNOWLEDGE_CHAR_LIMIT = 1500
