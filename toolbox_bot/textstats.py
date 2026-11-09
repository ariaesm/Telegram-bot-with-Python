"""Pure text statistics used by the ``/wordcount`` command."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

# \w is Unicode-aware, so Persian/Arabic words are counted too.
_WORD_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
_SENTENCE_RE = re.compile(r"[^.!?؟]+[.!?؟]*")

WORDS_PER_MINUTE = 200


@dataclass(frozen=True)
class TextStats:
    characters: int
    characters_no_spaces: int
    words: int
    unique_words: int
    sentences: int
    lines: int
    reading_seconds: int
    top_words: tuple[tuple[str, int], ...]


def words(text: str) -> list[str]:
    return _WORD_RE.findall(text)


def analyze(text: str, top: int = 3) -> TextStats:
    found = words(text)
    lowered = [w.lower() for w in found]
    sentences = [s for s in _SENTENCE_RE.findall(text) if s.strip(" \n\t.!?؟")]
    counts = Counter(lowered)
    # Sort by count desc, then alphabetically, so output is deterministic.
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return TextStats(
        characters=len(text),
        characters_no_spaces=sum(1 for c in text if not c.isspace()),
        words=len(found),
        unique_words=len(counts),
        sentences=len(sentences),
        lines=len(text.splitlines()) if text else 0,
        reading_seconds=round(len(found) * 60 / WORDS_PER_MINUTE),
        top_words=tuple(ranked),
    )


def format_stats(stats: TextStats) -> str:
    lines = [
        f"Words: {stats.words} ({stats.unique_words} unique)",
        f"Characters: {stats.characters} ({stats.characters_no_spaces} without spaces)",
        f"Sentences: {stats.sentences}",
        f"Lines: {stats.lines}",
        f"Reading time: ~{stats.reading_seconds}s at {WORDS_PER_MINUTE} wpm",
    ]
    if stats.top_words:
        top = ", ".join(f"{w} ×{n}" for w, n in stats.top_words)
        lines.append(f"Top words: {top}")
    return "\n".join(lines)
