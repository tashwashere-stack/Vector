"""Prompt assembly.

Layout is ordered for Ollama's prompt cache: everything that never changes in a
session (persona, crewmate summary, few-shot examples) comes first, so only the
recent history and the new message get re-processed each turn. Per-message
context (archive excerpts) rides inside the new user message.
"""

from vector import config
from vector.memory import Memory


def build_system_message(persona: str, crewmate_summary: str) -> str:
    parts = [persona.strip()]
    if crewmate_summary:
        parts.append(f"About Tashrif: {crewmate_summary}")
    return "\n\n".join(parts)


def few_shot_messages(behaviour: list[dict]) -> list[dict]:
    """Example exchanges. An optional "archive" field shows the model how to
    turn a textbook excerpt into Vector's own words."""
    messages = []
    for ex in behaviour:
        if ex.get("user") and ex.get("vector"):
            user = build_user_turn(ex["user"], ex.get("archive", ""))
            messages.append({"role": "user", "content": user})
            messages.append({"role": "assistant", "content": ex["vector"]})
    return messages


def static_prefix(persona: str, memory: Memory, behaviour: list[dict],
                  as_first_turn: bool = config.PERSONA_AS_FIRST_TURN) -> list[dict]:
    summary = memory.crewmate_summary()
    if memory.flags:
        summary = f"{summary}; recently observed: {', '.join(memory.flags)}".lstrip("; ")
    system = build_system_message(persona, summary)
    if as_first_turn:
        head = [{"role": "user", "content": system},
                {"role": "assistant", "content": "Understand. Vector ready."}]
    else:
        head = [{"role": "system", "content": system}]
    return [*head, *few_shot_messages(behaviour)]


def build_user_turn(user_input: str, knowledge: str = "", intent: str = "") -> str:
    context = []
    if knowledge:
        context.append(f"ARCHIVE (use facts, say them in your own short words):\n{knowledge}")
    if intent:
        context.append(f"(Intent: {intent})")
    return "\n\n".join([*context, user_input]) if context else user_input


def build_messages(prefix: list[dict], memory: Memory, user_turn: str) -> list[dict]:
    messages = list(prefix)
    for m in memory.history:
        messages.append({"role": "user", "content": m["user"]})
        messages.append({"role": "assistant", "content": m["vector"]})
    messages.append({"role": "user", "content": user_turn})
    return messages
