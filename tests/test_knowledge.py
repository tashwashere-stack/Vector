import os
import tempfile
import time
import unittest
from pathlib import Path

from vector.knowledge import KnowledgeBase, cache_is_stale, chunk_text, query_terms, word_counts


class ChunkTextTests(unittest.TestCase):
    def test_groups_lines_up_to_size(self):
        chunks = chunk_text("aaaa\nbbbb\ncccc\n", size=10)
        self.assertEqual(chunks, ["aaaa bbbb", "cccc"])

    def test_skips_blank_lines(self):
        self.assertEqual(chunk_text("\n\n  \nhello\n"), ["hello"])


class QueryTermsTests(unittest.TestCase):
    def test_drops_stopwords_and_short_words(self):
        self.assertEqual(query_terms("What is the time dilation of GPS?"),
                         {"time", "dilation", "gps"})


class SearchTests(unittest.TestCase):
    def setUp(self):
        text = "\n".join([
            "Gravity bends light around massive objects.",
            "",
            "Time dilation makes moving clocks run slow. Time is relative.",
        ])
        self.kb = KnowledgeBase(text)
        self.kb.chunks = [(c, word_counts(c)) for c in chunk_text(text, size=50)]

    def test_ranks_best_match_first(self):
        result = self.kb.search("time dilation")
        self.assertTrue(result.startswith("Time dilation"))

    def test_stopword_only_query_returns_nothing(self):
        self.assertEqual(self.kb.search("what is the"), "")

    def test_irrelevant_query_returns_nothing(self):
        # "time" matches, but "focus" and "problems" don't: below 50% coverage.
        self.assertEqual(self.kb.search("can't focus on time problems"), "")

    def test_single_shared_word_is_not_enough(self):
        self.assertEqual(self.kb.search("relative gravity of my mood"), "")

    def test_matches_whole_words_only(self):
        # "lative" appears inside "relative" but is not a word in the text.
        self.assertEqual(self.kb.search("lative clocks"), "")

    def test_respects_char_limit(self):
        self.assertLessEqual(len(self.kb.search("time dilation", limit=20)), 20)


class CacheStalenessTests(unittest.TestCase):
    def test_missing_or_empty_cache_is_stale(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d) / "cache.txt"
            self.assertTrue(cache_is_stale(cache, []))
            cache.write_text("")
            self.assertTrue(cache_is_stale(cache, []))

    def test_newer_pdf_makes_cache_stale(self):
        with tempfile.TemporaryDirectory() as d:
            cache, pdf = Path(d) / "cache.txt", Path(d) / "a.pdf"
            cache.write_text("x")
            pdf.write_bytes(b"%PDF")
            old = time.time() - 100
            os.utime(cache, (old, old))
            self.assertTrue(cache_is_stale(cache, [pdf]))
            os.utime(pdf, (old - 100, old - 100))
            self.assertFalse(cache_is_stale(cache, [pdf]))


if __name__ == "__main__":
    unittest.main()
