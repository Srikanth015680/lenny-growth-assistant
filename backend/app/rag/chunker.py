"""
Transcript chunking for ingestion (section 7.5-7.6).

Approximate token counting: we don't pull in a tokenizer dependency just
for this, so we approximate 1 token ~= 0.75 words (a documented assumption,
see docs/PRD.md "Assumptions") and chunk on word boundaries. This is
"approximately" 500-800 tokens per the spec's own wording, not an exact
tokenizer match — fine for this use case since chunk boundaries don't need
to be precise, just roughly even and not mid-sentence-hostile.
"""
from dataclasses import dataclass

WORDS_PER_TOKEN = 0.75
TARGET_TOKENS_MIN = 500
TARGET_TOKENS_MAX = 800
OVERLAP_TOKENS = 100


@dataclass
class Chunk:
    index: int
    text: str


def _tokens_to_words(tokens: int) -> int:
    return int(tokens / WORDS_PER_TOKEN)


def chunk_transcript(text: str) -> list[Chunk]:
    words = text.split()
    if not words:
        return []

    target_words = _tokens_to_words((TARGET_TOKENS_MIN + TARGET_TOKENS_MAX) // 2)
    overlap_words = _tokens_to_words(OVERLAP_TOKENS)

    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(words):
        end = min(start + target_words, len(words))
        chunk_text = " ".join(words[start:end])
        chunks.append(Chunk(index=index, text=chunk_text))
        index += 1
        if end == len(words):
            break
        start = end - overlap_words
    return chunks
