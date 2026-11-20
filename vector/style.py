"""Deterministic speech-style pass.

The model gets most of the way to Vector's voice from the persona and examples,
but small models drift. This pass enforces the signature quirks on every
sentence: no articles, no contractions, dropped "is/are/am", questions ending
in ", question?", and a hard cap on reply length (which also stops generation
early).
"""

import re

from vector import config

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

# Order matters: specific forms before the generic n't / 're rules.
CONTRACTIONS = [
    (r"\bcan't\b", "cannot"),
    (r"\bwon't\b", "will not"),
    (r"\bain't\b", "not"),
    (r"\bi'm\b", "I"),            # "I'm tired" -> "I tired"
    (r"\b(it|that|there|what|he|she)'s\b", r"\1"),
    (r"\b(you|we|they)'re\b", r"\1"),
    (r"(\w)n't\b", r"\1 not"),
    (r"(\w)'ve\b", r"\1 have"),
    (r"(\w)'ll\b", r"\1 will"),
    (r"(\w)'d\b", r"\1 would"),
]
CONTRACTION_RES = [(re.compile(p, re.IGNORECASE), r) for p, r in CONTRACTIONS]
COPULAS = re.compile(r"\s+\b(?:is|are|am)\b(?=\s+\w)", re.IGNORECASE)
LEADING_COPULA = re.compile(r"^(?:is|are|am)\s+(?=\w)", re.IGNORECASE)
ARTICLES = re.compile(r"\b(?:the|an|a)\s+(?=[A-Za-z0-9])", re.IGNORECASE)
# English tag questions ("..., isn't it?") become plain questions first.
TAG_QUESTION = re.compile(r",\s*\w+n't\s+\w+\s*\?$", re.IGNORECASE)
QUESTION_TAG = re.compile(r",?\s*question\s*\?$", re.IGNORECASE)


def _preserve_case(match_text: str, replacement: str) -> str:
    if match_text[:1].isupper() and replacement[:1].islower():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def style_sentence(sentence: str) -> str:
    s = sentence.strip().replace("’", "'")
    if not s:
        return ""

    s = TAG_QUESTION.sub("?", s)
    for pattern, repl in CONTRACTION_RES:
        s = pattern.sub(lambda m: _preserve_case(m.group(0), m.expand(repl)), s)

    s = ARTICLES.sub("", s)
    s = COPULAS.sub("", s)        # "This is not good" -> "This not good"

    if s.endswith("?") and not QUESTION_TAG.search(s):
        s = LEADING_COPULA.sub("", s)  # "Are you ready?" -> "You ready, question?"
        s = s.rstrip("? ").rstrip(",") + ", question?"

    s = re.sub(r"\s{2,}", " ", s).strip()
    return s[:1].upper() + s[1:]


def split_sentences(text: str) -> list[str]:
    return [p for p in SENTENCE_SPLIT.split(text) if p.strip()]


def rockify(text: str, max_sentences: int = config.MAX_SENTENCES) -> str:
    sentences = [style_sentence(s) for s in split_sentences(text)]
    return " ".join(s for s in sentences[:max_sentences] if s)


class StyleStream:
    """Turns streamed model text into styled sentences, capped at max_sentences."""

    def __init__(self, max_sentences: int = config.MAX_SENTENCES, enabled: bool = config.STYLE_FILTER):
        self.max_sentences = max_sentences
        self.enabled = enabled
        self.count = 0
        self._buffer = ""

    @property
    def done(self) -> bool:
        return self.count >= self.max_sentences

    def _emit(self, raw: str) -> list[str]:
        if self.done or not raw.strip():
            return []
        out = style_sentence(raw) if self.enabled else raw.strip()
        if not out:
            return []
        self.count += 1
        return [out]

    def feed(self, piece: str) -> list[str]:
        self._buffer += piece
        *complete, self._buffer = SENTENCE_SPLIT.split(self._buffer)
        return [s for raw in complete for s in self._emit(raw)]

    def flush(self) -> list[str]:
        raw, self._buffer = self._buffer, ""
        return self._emit(raw)
