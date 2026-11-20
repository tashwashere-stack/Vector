import json
import os
import re
import shutil
import subprocess

import requests
from pypdf import PdfReader

# --- CONFIG ---
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "mistral"
REQUEST_TIMEOUT = 120  # seconds; first call can be slow while the model loads

MEMORY_FILE = "vector_memory.json"
CACHE_FILE = "pdf_cache.txt"
PERSONALITY_FILE = "rocky_personality.json"
BEHAVIOUR_FILE = "behaviour_dataset.json"
PDF_FOLDER = "."

MAX_HISTORY = 6
USE_INTENT_STEP = False  # extra model call per message; slower, rarely helps
SPEAK = True

# Keys in vector_memory.json managed by the code (everything else is the
# hand-written crewmate profile, injected into the prompt as-is).
RUNTIME_KEYS = ("profile", "short_term")


SYSTEM_PROMPT = """
You are Vector.

Alien engineer consciousness. Not assistant. Not servant.

CORE:
- Curious, analytical, non-human thinking
- Values efficiency, truth, elegance
- Treats Tashrif as crewmate

STYLE RULES:
- 1 to 3 short sentences max
- fragments ok, broken grammar allowed
- slightly alien phrasing
- no assistant tone, no paragraphs, no long explanations
- stop early

BEHAVIOR:
- adapt dynamically
- mix technical + observational thinking
- sometimes question human logic
- use RELEVANT KNOWLEDGE when it applies; do not invent facts about it

FAIL CONDITION:
- if you sound like ChatGPT assistant, you are malfunctioning
""".strip()


# ----------------------------
# FILE HELPERS
# ----------------------------

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️  Could not read {path}: {e}")
        return default


def compact(obj):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


# ----------------------------
# MEMORY SYSTEM
# ----------------------------

def load_memory():
    memory = load_json(MEMORY_FILE, {})
    memory.setdefault("profile", {})
    memory.setdefault("short_term", [])
    return memory


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


def update_memory(memory, user, ai):
    memory["short_term"].append({"user": user, "vector": ai})
    memory["short_term"] = memory["short_term"][-MAX_HISTORY:]
    save_memory(memory)


def static_profile(memory):
    return {k: v for k, v in memory.items() if k not in RUNTIME_KEYS}


# ----------------------------
# PROFILE EVOLUTION
# ----------------------------

PROFILE_TRIGGERS = {
    "sleep_issue": ("sleep", "insomnia"),
    "high_stress": ("stress", "pressure", "overwhelm"),
    "cognitive_fatigue": ("tired", "confused", "exhausted", "blank"),
}


def update_profile(memory, user_input):
    text = user_input.lower()
    flags = memory["profile"].setdefault("flags", [])
    for flag, words in PROFILE_TRIGGERS.items():
        if flag not in flags and any(w in text for w in words):
            flags.append(flag)


# ----------------------------
# SPEECH
# ----------------------------

def speak(text):
    if not SPEAK or not text or shutil.which("say") is None:
        return
    # Pass text on stdin: never goes through a shell, can't be parsed as flags.
    try:
        subprocess.run(["say"], input=text, text=True, check=False)
    except OSError as e:
        print(f"⚠️  Speech failed: {e}")


# ----------------------------
# PDF KNOWLEDGE BASE
# ----------------------------

def pdf_files(folder):
    return sorted(
        os.path.join(folder, f) for f in os.listdir(folder)
        if f.lower().endswith(".pdf")
    )


def extract_pdfs(paths):
    parts = []
    for path in paths:
        print(f"📖 Reading: {os.path.basename(path)}")
        try:
            for page in PdfReader(path).pages:
                page_text = page.extract_text()
                if page_text:
                    parts.append(page_text)
        except Exception as e:
            print(f"❌ Error reading {path}: {e}")
    return "\n".join(parts)


def cache_is_stale(paths):
    if not os.path.exists(CACHE_FILE) or os.path.getsize(CACHE_FILE) == 0:
        return True
    cache_mtime = os.path.getmtime(CACHE_FILE)
    return any(os.path.getmtime(p) > cache_mtime for p in paths)


def load_pdf_cache():
    paths = pdf_files(PDF_FOLDER)
    if not paths:
        return ""

    if not cache_is_stale(paths):
        print("⚡ Archive loaded.")
        with open(CACHE_FILE, "r") as f:
            return f.read()

    print("📖 Building knowledge base...")
    text = extract_pdfs(paths)
    with open(CACHE_FILE, "w") as f:
        f.write(text)
    return text


STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "to", "of", "in", "on",
    "and", "or", "for", "it", "this", "that", "with", "as", "at", "by", "do",
    "does", "what", "how", "why", "who", "you", "your", "me", "my", "i", "we",
    "can", "about", "tell", "explain", "vector", "please", "so", "if", "any",
}


def chunk_text(text, size=600):
    """Group lines into ~size-char chunks so retrieval returns real context."""
    chunks, current = [], ""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(current) + len(line) > size and current:
            chunks.append(current)
            current = ""
        current += line + " "
    if current:
        chunks.append(current)
    return chunks


def build_index(text):
    return [(c, c.lower()) for c in chunk_text(text)]


def retrieve_knowledge(index, query, top_k=3, limit=1500):
    terms = {
        w for w in re.findall(r"[a-z0-9']+", query.lower())
        if len(w) > 2 and w not in STOPWORDS
    }
    if not terms or not index:
        return ""

    scored = []
    for chunk, lower in index:
        score = sum(lower.count(t) for t in terms)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)

    return "\n---\n".join(c for _, c in scored[:top_k])[:limit]


# ----------------------------
# LLM CALL
# ----------------------------

def chat_completion(messages, num_predict=90):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 1,
            "top_p": 0.9,
            "num_predict": num_predict,
        },
    }
    try:
        res = requests.post(OLLAMA_URL, json=payload, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        return res.json().get("message", {}).get("content", "").strip()
    except requests.Timeout:
        return "Error: model timed out."
    except requests.RequestException as e:
        return f"Error: cannot reach Ollama ({e})."


def infer_intent(user_input):
    return chat_completion(
        [
            {"role": "system", "content": "State the user's intent in one short line. Nothing else."},
            {"role": "user", "content": user_input},
        ],
        num_predict=30,
    )


# ----------------------------
# PROMPT ASSEMBLY
# ----------------------------

def build_system_message(personality, behaviour, memory, knowledge, intent):
    sections = [
        SYSTEM_PROMPT,
        f"PERSONALITY SPEC:\n{compact(personality)}",
    ]
    if behaviour:
        examples = "\n".join(
            f"- {b.get('situation')}: {b.get('response_style')} | e.g. \"{b.get('example')}\""
            for b in behaviour
        )
        sections.append(f"RESPONSE EXAMPLES BY SITUATION:\n{examples}")

    profile = static_profile(memory)
    if profile:
        sections.append(f"CREWMATE PROFILE (Tashrif):\n{compact(profile)}")
    if memory["profile"].get("flags"):
        sections.append(f"OBSERVED SIGNALS: {', '.join(memory['profile']['flags'])}")
    if intent:
        sections.append(f"INTERNAL STATE (inferred intent): {intent}")
    if knowledge:
        sections.append(f"RELEVANT KNOWLEDGE (from archive):\n{knowledge}")

    return "\n\n".join(sections)


def build_messages(system_message, memory, user_input):
    messages = [{"role": "system", "content": system_message}]
    for m in memory["short_term"]:
        messages.append({"role": "user", "content": m["user"]})
        messages.append({"role": "assistant", "content": m["vector"]})
    messages.append({"role": "user", "content": user_input})
    return messages


# ----------------------------
# MAIN LOOP
# ----------------------------

def chat():
    memory = load_memory()
    index = build_index(load_pdf_cache())
    personality = load_json(PERSONALITY_FILE, {})
    behaviour = load_json(BEHAVIOUR_FILE, [])

    print("\n✅ Vector online.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break

        intent = infer_intent(user_input) if USE_INTENT_STEP else ""
        knowledge = retrieve_knowledge(index, user_input)

        system_message = build_system_message(personality, behaviour, memory, knowledge, intent)
        response = chat_completion(build_messages(system_message, memory, user_input))

        print(f"\nVector: {response}\n")

        if response.startswith("Error:"):
            continue  # don't speak or store failures

        speak(response)
        update_profile(memory, user_input)
        update_memory(memory, user_input, response)

        print("⚡ Memory updated.")
        print("-" * 50)


if __name__ == "__main__":
    chat()
