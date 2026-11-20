import tempfile
import unittest
from pathlib import Path

from vector.memory import Memory
from vector.prompt import build_messages, build_user_turn, static_prefix


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


class CrewmateSummaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.memory = Memory(Path(self.tmp.name) / "m.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_condenses_profile_fields(self):
        self.memory.data["core_identity"] = {"fields_of_interest": ["A", "B", "C", "D", "E"]}
        self.memory.data["current_state"] = {"sleep_pattern": "fragmented"}
        self.assertEqual(self.memory.crewmate_summary(), "interests: A, B, C, D; sleep: fragmented")

    def test_handwritten_summary_wins(self):
        self.memory.data["summary"] = "  Night owl.  "
        self.memory.data["core_identity"] = {"fields_of_interest": ["A"]}
        self.assertEqual(self.memory.crewmate_summary(), "Night owl.")


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.memory = Memory(Path(self.tmp.name) / "m.json")
        self.memory.data["core_identity"] = {"goals": ["ship it"]}
        self.memory.history.append({"user": "hi", "vector": "Greeting received."})
        self.behaviour = [{"situation": "s", "user": "u1", "vector": "v1"}, {"situation": "no pair"}]

    def tearDown(self):
        self.tmp.cleanup()

    def test_static_prefix_is_system_then_examples(self):
        prefix = static_prefix("PERSONA", self.memory, self.behaviour, as_first_turn=False)
        self.assertEqual([m["role"] for m in prefix], ["system", "user", "assistant"])
        self.assertIn("PERSONA", prefix[0]["content"])
        self.assertIn("goals: ship it", prefix[0]["content"])

    def test_persona_as_first_turn_for_mistral_style_templates(self):
        prefix = static_prefix("PERSONA", self.memory, self.behaviour, as_first_turn=True)
        self.assertEqual([m["role"] for m in prefix], ["user", "assistant", "user", "assistant"])
        self.assertIn("PERSONA", prefix[0]["content"])

    def test_flags_go_in_static_summary(self):
        self.memory.flags.append("high_stress")
        prefix = static_prefix("P", self.memory, self.behaviour, as_first_turn=False)
        self.assertIn("recently observed: high_stress", prefix[0]["content"])

    def test_user_turn_carries_context(self):
        turn = build_user_turn("q?", knowledge="facts")
        self.assertTrue(turn.startswith("ARCHIVE"))
        self.assertIn("facts", turn)
        self.assertTrue(turn.endswith("q?"))
        self.assertEqual(build_user_turn("q?"), "q?")

    def test_messages_order(self):
        prefix = static_prefix("P", self.memory, self.behaviour, as_first_turn=False)
        msgs = build_messages(prefix, self.memory, "next")
        self.assertEqual([m["role"] for m in msgs],
                         ["system", "user", "assistant", "user", "assistant", "user"])
        self.assertEqual(msgs[-1]["content"], "next")


if __name__ == "__main__":
    unittest.main()
