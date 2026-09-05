from functools import lru_cache

from app.config import settings
from app.exceptions import EmbeddingError
from app.logging_config import get_logger


logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise EmbeddingError(
            "sentence-transformers is not installed."
        ) from exc

    return SentenceTransformer(settings.embedding_model)


def embed_text(text: str) -> list[float]:
    try:
        model = _get_model()

        vector = model.encode(
            text,
            normalize_embeddings=True,
        )

        return vector.tolist()

    except EmbeddingError:
        raise

    except Exception as exc:
        logger.error(
            "Embedding failed",
            extra={
                "exception_type": type(exc).__name__,
            },
        )
        raise EmbeddingError(
            "Failed to generate an embedding."
        ) from exc


def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    try:
        model = _get_model()

        vectors = model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
        )

        return [vector.tolist() for vector in vectors]

    except EmbeddingError:
        raise

    except Exception as exc:
        logger.error(
            "Batch embedding failed",
            extra={"count": len(texts)},
        )
        raise EmbeddingError(
            "Failed to generate embeddings."
        ) from exc