"""
Embedding model wrapper (sentence-transformers/all-MiniLM-L6-v2, per spec).

Loaded lazily and once per process — model load is the expensive part, not
individual encode() calls, so every caller shares one instance. Wrapped in
EmbeddingError so a broken model load surfaces as a normal structured API
error rather than crashing the process.

NOTE (sandbox limitation, recorded honestly per agent_transcripts): loading
sentence-transformers pulls in torch and downloads the model from
HuggingFace Hub on first use. Neither is reachable from this build
sandbox's network allowlist, so this module is written correctly but was
verified with a fake embedding function in tests, not a live model load —
see backend/tests/test_retrieval.py and docs/troubleshooting.md.
"""
from functools import lru_cache

from app.config import settings
from app.exceptions import EmbeddingError
from app.logging_config import get_logger

logger = get_logger(__name__)


@lru_cache
def _get_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - exercised only without the dep installed
        raise EmbeddingError(
            "sentence-transformers is not installed in this environment."
        ) from exc
    return SentenceTransformer(settings.embedding_model)


def embed_text(text: str) -> list[float]:
    """Embed a single string (a user query, or one transcript chunk)."""
    try:
        model = _get_model()
        vector = model.encode(text, normalize_embeddings=True)
        return vector.tolist()
    except EmbeddingError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("embedding_failed", extra={"exception_type": type(exc).__name__})
        raise EmbeddingError("Failed to generate an embedding for the input text.") from exc


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed many chunks at once (ingestion path) — one model call instead
    of N, which matters once there are thousands of chunks."""
    try:
        model = _get_model()
        vectors = model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [v.tolist() for v in vectors]
    except EmbeddingError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("batch_embedding_failed", extra={"count": len(texts)})
        raise EmbeddingError("Failed to generate embeddings for a batch of chunks.") from exc
