"""Interactive chat loop."""

from vector import config, llm, voice
from vector.knowledge import KnowledgeBase
from vector.memory import Memory
from vector.prompt import build_messages, build_system_message
from vector.storage import load_json


def main() -> None:
    memory = Memory()
    kb = KnowledgeBase.load()
    personality = load_json(config.PERSONALITY_FILE, {})
    behaviour = load_json(config.BEHAVIOUR_FILE, [])

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

        try:
            intent = llm.infer_intent(user_input) if config.USE_INTENT_STEP else ""
            system_message = build_system_message(
                personality, behaviour, memory, kb.search(user_input), intent
            )
            reply = llm.chat(build_messages(system_message, memory, user_input))
        except llm.LLMError as e:
            print(f"\n❌ {e}\n")
            continue

        print(f"\nVector: {reply}\n")
        voice.speak(reply)
        memory.observe(user_input)
        memory.remember(user_input, reply)

        print("⚡ Memory updated.")
        print("-" * 50)


if __name__ == "__main__":
    main()
