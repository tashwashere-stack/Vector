import tempfile
import unittest
from pathlib import Path

from vector.memory import Memory
from vector.prompt import build_messages, build_system_message


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "memory.json"
        self.memory = Memory(self.path, max_history=2)

    def tearDown(self):
        self.tmp.cleanup()

    def test_history_is_trimmed_and_persisted(self):
        for i in range(3):
            self.memory.remember(f"q{i}", f"a{i}")
        self.assertEqual([m["user"] for m in self.memory.history], ["q1", "q2"])
        self.assertEqual(Memory(self.path).history, self.memory.history)

    def test_observe_sets_flags_once(self):
        self.memory.observe("so tired and stressed")
        self.memory.observe("still tired")
        self.assertEqual(sorted(self.memory.flags), ["cognitive_fatigue", "high_stress"])

    def test_static_profile_excludes_runtime_keys(self):
        self.memory.data["core_identity"] = {"name": "X"}
        self.assertEqual(self.memory.static_profile(), {"core_identity": {"name": "X"}})


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.memory = Memory(Path(self.tmp.name) / "m.json")
        self.memory.data["core_identity"] = {"name": "X"}
        self.memory.history.append({"user": "hi", "vector": "Greeting received."})

    def tearDown(self):
        self.tmp.cleanup()

    def test_system_message_includes_sections(self):
        msg = build_system_message({"identity": {}}, [{"situation": "s"}], self.memory, "facts")
        for section in ("PERSONALITY SPEC", "RESPONSE EXAMPLES", "CREWMATE PROFILE", "RELEVANT KNOWLEDGE"):
            self.assertIn(section, msg)

    def test_messages_have_roles_in_order(self):
        msgs = build_messages("sys", self.memory, "next")
        self.assertEqual([m["role"] for m in msgs], ["system", "user", "assistant", "user"])
        self.assertEqual(msgs[-1]["content"], "next")


if __name__ == "__main__":
    unittest.main()
