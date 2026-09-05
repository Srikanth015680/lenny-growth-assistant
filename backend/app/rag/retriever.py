from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import RetrievalError
from app.logging_config import get_logger
from app.models.db_models import TranscriptChunk
from app.rag.embeddings import embed_text


logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    episode: str
    guest: str | None
    timestamp: str | None
    text: str
    score: float


class TranscriptRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int = settings.retrieval_top_k,
        similarity_threshold: float = settings.retrieval_threshold,
    ) -> list[RetrievedChunk]:

        try:
            query_embedding = embed_text(query)
        except Exception as exc:
            logger.error(
                "Failed to create query embedding",
                extra={"exception_type": type(exc).__name__},
            )
            raise RetrievalError(
                "Could not embed the query for retrieval."
            ) from exc

        distance = TranscriptChunk.embedding.cosine_distance(
            query_embedding
        )

        query_stmt = (
            select(TranscriptChunk, distance.label("distance"))
            .order_by(distance)
            .limit(top_k)
        )

        try:
            result = await self.db.execute(query_stmt)
        except Exception as exc:
            logger.error(
                "Vector search failed",
                extra={"exception_type": type(exc).__name__},
            )
            raise RetrievalError(
                "The similarity search failed."
            ) from exc

        retrieved: list[RetrievedChunk] = []

        for row, distance_value in result.all():
            similarity = 1.0 - float(distance_value)

            if similarity < similarity_threshold:
                continue

            retrieved.append(
                RetrievedChunk(
                    episode=row.episode_title,
                    guest=row.guest_name,
                    timestamp=row.timestamp_ref,
                    text=row.chunk_text,
                    score=round(similarity, 4),
                )
            )

        logger.info(
            "Retrieval completed",
            extra={
                "query_length": len(query),
                "top_k": top_k,
                "returned": len(retrieved),
            },
        )

        return retrieved