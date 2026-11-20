"""System prompt and message assembly."""

from vector.memory import Memory
from vector.storage import compact

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


def format_behaviour(behaviour: list[dict]) -> str:
    return "\n".join(
        f"- {b.get('situation')}: {b.get('response_style')} | e.g. \"{b.get('example')}\""
        for b in behaviour
    )


def build_system_message(personality: dict, behaviour: list[dict], memory: Memory,
                         knowledge: str = "", intent: str = "") -> str:
    sections = [SYSTEM_PROMPT]
    if personality:
        sections.append(f"PERSONALITY SPEC:\n{compact(personality)}")
    if behaviour:
        sections.append(f"RESPONSE EXAMPLES BY SITUATION:\n{format_behaviour(behaviour)}")
    if profile := memory.static_profile():
        sections.append(f"CREWMATE PROFILE:\n{compact(profile)}")
    if memory.flags:
        sections.append(f"OBSERVED SIGNALS: {', '.join(memory.flags)}")
    if intent:
        sections.append(f"INTERNAL STATE (inferred intent): {intent}")
    if knowledge:
        sections.append(f"RELEVANT KNOWLEDGE (from archive):\n{knowledge}")
    return "\n\n".join(sections)


def build_messages(system_message: str, memory: Memory, user_input: str) -> list[dict]:
    messages = [{"role": "system", "content": system_message}]
    for m in memory.history:
        messages.append({"role": "user", "content": m["user"]})
        messages.append({"role": "assistant", "content": m["vector"]})
    messages.append({"role": "user", "content": user_input})
    return messages
