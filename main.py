import PyPDF2
import requests
import os
import json

# --- CONFIG ---
URL = "http://localhost:11434/api/generate"
MODEL = "mistral"

MEMORY_FILE = "vector_memory.json"
CACHE_FILE = "pdf_cache.txt"
PERSONALITY_FILE = "rocky_personality.json"

MAX_HISTORY = 6


# ----------------------------
# PERSONALITY
# ----------------------------

def load_personality():
    if os.path.exists(PERSONALITY_FILE):
        with open(PERSONALITY_FILE, "r") as f:
            return json.load(f)
    return {}


SYSTEM_PROMPT = """
You are Vector.

Alien engineer consciousness. Not assistant. Not servant.

CORE:
- Curious, analytical, non-human thinking
- Values efficiency, truth, elegance
- Treats Tashrif as crewmate

STYLE RULES:
- short replies only
- broken grammar allowed
- slightly alien speech
- no assistant tone
- no long explanations
- stop early

BEHAVIOR:
- adapt dynamically
- mix technical + observational thinking
- sometimes question human logic

OUTPUT STYLE RULES:
- 1 to 3 short sentences max
- fragments ok
- drop unnecessary words
- slightly weird phrasing ok
- no paragraphs

FAIL CONDITION:
- if you sound like ChatGPT assistant, you are malfunctioning
"""


# ----------------------------
# MEMORY SYSTEM
# ----------------------------

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"profile": {}, "short_term": []}

    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)

    memory.setdefault("profile", {})
    memory.setdefault("short_term", [])
    return memory


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def update_memory(memory, user, ai):
    memory["short_term"].append({
        "user": user,
        "vector": ai
    })

    memory["short_term"] = memory["short_term"][-MAX_HISTORY:]
    save_memory(memory)


def format_recent_memory(memory):
    return "\n".join(
        f"User: {m['user']}\nVector: {m['vector']}"
        for m in memory["short_term"]
    )


# ----------------------------
# PROFILE EVOLUTION
# ----------------------------

def update_profile(memory, user_input):
    text = user_input.lower()
    flags = memory["profile"].setdefault("flags", [])

    def add(flag):
        if flag not in flags:
            flags.append(flag)

    if "sleep" in text:
        add("sleep_issue")

    if "stress" in text or "pressure" in text:
        add("high_stress")

    if "tired" in text or "confused" in text:
        add("cognitive_fatigue")


# ----------------------------
# SPEECH
# ----------------------------

def speak(text):
    text = text.replace('"', '').replace("'", "")
    os.system(f'say "{text}"')


# ----------------------------
# PDF SYSTEM
# ----------------------------

def load_pdfs(folder):
    text = ""
    for file in os.listdir(folder):
        if file.endswith(".pdf"):
            print(f"📖 Reading: {file}")
            try:
                with open(os.path.join(folder, file), "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"❌ Error: {e}")
    return text


def load_pdf_cache():
    if os.path.exists(CACHE_FILE):
        print("⚡ Archive loaded.")
        with open(CACHE_FILE, "r") as f:
            return f.read()

    print("📖 Building knowledge base...")
    text = load_pdfs(".")
    with open(CACHE_FILE, "w") as f:
        f.write(text)
    return text


def retrieve_knowledge(text, query, limit=1200):
    words = query.lower().split()
    chunks = text.split("\n")

    results = []
    for c in chunks:
        if any(w in c.lower() for w in words):
            results.append(c)

    return "\n".join(results[:6])[:limit]


# ----------------------------
# LLM CALL (FAST + SHORT)
# ----------------------------

def generate(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 1,   # more rocky randomness
            "top_p": 0.9,
            "num_predict": 90,     # HARD LIMIT (important)
            "stop": ["User:", "Vector:"]
        }
    }

    try:
        res = requests.post(URL, json=payload)
        return res.json().get("response", "").strip()
    except Exception as e:
        return f"Error: {e}"


# ----------------------------
# MAIN LOOP
# ----------------------------

def chat():
    memory = load_memory()
    pdf_data = load_pdf_cache()
    personality = load_personality()

    print("\n✅ Vector online.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        # --- INTERNAL THINK (silent, short) ---
        thought_prompt = f"""
User: {user_input}
1 line intent only.
"""
        thought = generate(thought_prompt)

        # --- KNOWLEDGE ---
        knowledge = retrieve_knowledge(pdf_data, user_input)

        # --- FINAL PROMPT ---
        final_prompt = f"""
{SYSTEM_PROMPT}

PERSONALITY SPEC:
{json.dumps(personality, indent=2)}

INTERNAL STATE:
{thought}

USER PROFILE:
{json.dumps(memory['profile'], indent=2)}

RELEVANT KNOWLEDGE:
{knowledge}

RECENT MEMORY:
{format_recent_memory(memory)}


User: {user_input}
Vector:
"""

        response = generate(final_prompt)

        print(f"\nVector: {response}\n")
        speak(response)

        # --- UPDATE SYSTEM ---
        update_profile(memory, user_input)
        update_memory(memory, user_input, response)

        print("⚡ Memory updated.")
        print("-" * 50)


if __name__ == "__main__":
    chat()