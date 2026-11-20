"""PDF knowledge base: extract, cache, chunk, keyword-rank."""

import re
from pathlib import Path

from pypdf import PdfReader

from vector import config

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "to", "of", "in", "on",
    "and", "or", "for", "it", "this", "that", "with", "as", "at", "by", "do",
    "does", "what", "how", "why", "who", "you", "your", "me", "my", "i", "we",
    "can", "about", "tell", "explain", "vector", "please", "so", "if", "any",
    "like", "just", "know", "think", "want", "get", "make", "really", "now",
    "then", "also", "there", "have", "has", "had", "not", "but", "from", "they",
    "them", "when", "where", "which", "will", "would", "could", "should", "been",
    "more", "some", "very", "did", "its", "talk", "say", "said", "thing", "things",
}


def pdf_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() == ".pdf")


def extract_pdfs(paths: list[Path]) -> str:
    parts = []
    for path in paths:
        print(f"📖 Reading: {path.name}")
        try:
            for page in PdfReader(path).pages:
                page_text = page.extract_text()
                if page_text:
                    parts.append(page_text)
        except Exception as e:
            print(f"❌ Error reading {path.name}: {e}")
    return "\n".join(parts)


def cache_is_stale(cache: Path, paths: list[Path]) -> bool:
    if not cache.exists() or cache.stat().st_size == 0:
        return True
    cache_mtime = cache.stat().st_mtime
    return any(p.stat().st_mtime > cache_mtime for p in paths)


def load_text(folder: Path = config.KNOWLEDGE_DIR, cache: Path = config.CACHE_FILE) -> str:
    paths = pdf_files(folder)
    if not paths:
        return ""
    if not cache_is_stale(cache, paths):
        print("⚡ Archive loaded.")
        return cache.read_text()

    print("📖 Building knowledge base...")
    text = extract_pdfs(paths)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text)
    return text


def chunk_text(text: str, size: int = config.CHUNK_SIZE) -> list[str]:
    """Group lines into ~size-char chunks so retrieval returns real context."""
    chunks, current = [], ""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if current and len(current) + len(line) > size:
            chunks.append(current.strip())
            current = ""
        current += line + " "
    if current:
        chunks.append(current.strip())
    return chunks


def query_terms(query: str) -> set[str]:
    return {
        w for w in re.findall(r"[a-z0-9']+", query.lower())
        if len(w) > 2 and w not in STOPWORDS
    }


class KnowledgeBase:
    def __init__(self, text: str):
        self.chunks = [(c, c.lower()) for c in chunk_text(text)]

    @classmethod
    def load(cls) -> "KnowledgeBase":
        return cls(load_text())

    def search(self, query: str, top_k: int = config.TOP_K,
               limit: int = config.KNOWLEDGE_CHAR_LIMIT,
               min_coverage: float = config.MIN_TERM_COVERAGE) -> str:
        """Return the best-matching chunks, or "" when nothing is clearly relevant.

        A chunk qualifies only if it contains at least `min_coverage` of the
        query's key terms (and at least two of them for multi-term queries), so
        casual chat doesn't drag archive text into the prompt.
        """
        terms = query_terms(query)
        if not terms or not self.chunks:
            return ""
        # At least half the key terms, and at least two when the query has two or more.
        needed = max(min(2, len(terms)), round(len(terms) * min_coverage))
        scored = []
        for chunk, lower in self.chunks:
            hits = [t for t in terms if t in lower]
            if len(hits) >= needed:
                scored.append((len(hits), sum(lower.count(t) for t in hits), chunk))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return "\n---\n".join(c for *_, c in scored[:top_k])[:limit]
