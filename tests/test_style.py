import unittest

from vector.style import StyleStream, rockify, style_sentence


class StyleSentenceTests(unittest.TestCase):
    def check(self, text, expected):
        self.assertEqual(style_sentence(text), expected)

    def test_drops_articles(self):
        self.check("The clock near a star runs slow.", "Clock near star runs slow.")

    def test_drops_copulas(self):
        self.check("This is not good.", "This not good.")
        self.check("I am happy.", "I happy.")

    def test_expands_contractions(self):
        self.check("I'm tired and it's late.", "I tired and it late.")
        self.check("You can't stop, don't worry.", "You cannot stop, do not worry.")

    def test_question_tag(self):
        self.check("What is your name?", "What your name, question?")
        self.check("You sleep today, question?", "You sleep today, question?")
        self.check("Is it working?", "It working, question?")

    def test_english_tag_question_becomes_plain_question(self):
        self.check("The clock is slow, isn't it?", "Clock slow, question?")

    def test_keeps_capitalisation(self):
        self.check("the answer is yes.", "Answer yes.")

    def test_curly_apostrophes(self):
        self.check("I’m here.", "I here.")


class RockifyTests(unittest.TestCase):
    def test_caps_sentence_count(self):
        self.assertEqual(rockify("One. Two. Three. Four.", max_sentences=2), "One. Two.")


class StyleStreamTests(unittest.TestCase):
    def test_streams_sentences_and_stops_at_cap(self):
        s = StyleStream(max_sentences=2, enabled=True)
        out = []
        for piece in ["The test is ", "hard. Are you", " ready? Third one."]:
            out += s.feed(piece)
        out += s.flush()
        self.assertEqual(out, ["Test hard.", "You ready, question?"])
        self.assertTrue(s.done)

    def test_disabled_passes_text_through(self):
        s = StyleStream(max_sentences=3, enabled=False)
        self.assertEqual(s.feed("The cat is here. ") + s.flush(), ["The cat is here."])


if __name__ == "__main__":
    unittest.main()
