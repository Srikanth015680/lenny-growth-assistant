"""
TranscriptRetriever (section 8).

query -> embedding -> pgvector cosine similarity -> top-k above threshold
-> chunk text + citation metadata. This is the ONLY module that knows the
similarity search is backed by pgvector/HNSW — callers get plain Python
objects, per the "don't expose vector/DB internals" rule.
"""
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
    score: float  # cosine similarity, 1.0 = identical, higher is better


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
        except Exception as exc:  # noqa: BLE001 — embeddings.py already logs specifics
            raise RetrievalError("Could not embed the query for retrieval.") from exc

        # pgvector's cosine_distance is `1 - cosine_similarity`; we ask
        # Postgres to do the ANN search (using the HNSW index from
        # db_models.py) and convert back to similarity in Python so callers
        # never see a "distance" number, only a similarity score.
        distance_col = TranscriptChunk.embedding.cosine_distance(query_embedding)
        stmt = (
            select(TranscriptChunk, distance_col.label("distance"))
            .order_by(distance_col)
            .limit(top_k)
        )
        try:
            result = await self.db.execute(stmt)
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError("The similarity search against pgvector failed.") from exc

        chunks: list[RetrievedChunk] = []
        for row, distance in result.all():
            score = 1.0 - float(distance)
            if score < similarity_threshold:
                continue
            chunks.append(
                RetrievedChunk(
                    episode=row.episode_title,
                    guest=row.guest_name,
                    timestamp=row.timestamp_ref,
                    text=row.chunk_text,
                    score=round(score, 4),
                )
            )

        logger.info(
            "retrieval_complete",
            extra={"query_len": len(query), "returned": len(chunks), "top_k": top_k},
        )
        return chunks
