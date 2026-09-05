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

    target_tokens = (TARGET_TOKENS_MIN + TARGET_TOKENS_MAX) // 2

    chunk_size = _tokens_to_words(target_tokens)
    overlap = _tokens_to_words(OVERLAP_TOKENS)

    chunks: list[Chunk] = []

    start = 0
    index = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))

        chunks.append(
            Chunk(
                index=index,
                text=" ".join(words[start:end]),
            )
        )

        index += 1

        if end >= len(words):
            break

        start = end - overlap

    return chunks