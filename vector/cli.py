"""Interactive chat loop."""

from vector import config, llm
from vector.knowledge import KnowledgeBase
from vector.memory import Memory
from vector.prompt import build_messages, build_user_turn, static_prefix
from vector.storage import load_json
from vector.style import StyleStream
from vector.voice import Speaker


def load_persona() -> str:
    try:
        return config.PERSONA_FILE.read_text()
    except OSError:
        return "You are Vector, an alien engineer. Reply in 1-3 short sentences."


def main() -> None:
    memory = Memory()
    kb = KnowledgeBase.load()
    prefix = static_prefix(load_persona(), memory, load_json(config.BEHAVIOUR_FILE, []))
    speaker = Speaker()

    if config.WARM_UP:
        print("🔧 Warming up model...")
        try:
            llm.warm_up(prefix + [{"role": "user", "content": "ready?"}])
        except llm.LLMError as e:
            print(f"❌ {e}")

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

        sentences: list[str] = []

        def show(new: list[str]) -> None:
            for sentence in new:
                print(("" if not sentences else " ") + sentence, end="", flush=True)
                speaker.say(sentence)
                sentences.append(sentence)

        try:
            intent = llm.infer_intent(user_input) if config.USE_INTENT_STEP else ""
            user_turn = build_user_turn(user_input, kb.search(user_input), intent)
            style = StyleStream()
            print("\nVector: ", end="", flush=True)
            for piece in llm.stream_chat(build_messages(prefix, memory, user_turn)):
                show(style.feed(piece))
                if style.done:
                    break  # closes the stream; Ollama stops generating
            show(style.flush())
        except llm.LLMError as e:
            print(f"\n❌ {e}\n")
            continue

        print("\n")
        reply = " ".join(sentences)
        if reply:
            memory.observe(user_input)
            memory.remember(user_input, reply)
        print("-" * 50)

    speaker.close()


if __name__ == "__main__":
    main()
