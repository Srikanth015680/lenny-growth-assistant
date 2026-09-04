"""
Retrieval tests (section 26): embedding call, similarity ranking, threshold
behavior, empty retrieval.

`embed_text` is monkeypatched to a deterministic fake so these tests don't
need the real sentence-transformers model (not installed in CI/sandbox —
see docs/troubleshooting.md) — but the similarity search itself runs for
real against Postgres + pgvector's HNSW index, which is the part actually
worth verifying.
"""
import uuid

import pytest

from app.models.db_models import TranscriptChunk
from app.rag.retriever import TranscriptRetriever
from tests.conftest import random_embedding


async def _insert_chunk(db_session, *, episode, guest, text, embedding, source_id, chunk_index=0):
    chunk = TranscriptChunk(
        episode_title=episode,
        guest_name=guest,
        publication_date="2024-01-01",
        timestamp_ref="12:34",
        chunk_text=text,
        source_id=source_id,
        chunk_index=chunk_index,
        embedding=embedding,
    )
    db_session.add(chunk)
    await db_session.commit()
    return chunk


async def test_retrieve_returns_nearest_neighbor_first(db_session, monkeypatch):
    query_vec = random_embedding(seed=1)
    # A chunk embedded identically to the query should rank above an
    # unrelated, randomly-seeded one.
    close_vec = query_vec
    far_vec = random_embedding(seed=999)

    await _insert_chunk(
        db_session, episode="Ep A", guest="Guest A", text="close match",
        embedding=close_vec, source_id="src-a",
    )
    await _insert_chunk(
        db_session, episode="Ep B", guest="Guest B", text="far match",
        embedding=far_vec, source_id="src-b",
    )

    monkeypatch.setattr("app.rag.retriever.embed_text", lambda q: query_vec)

    retriever = TranscriptRetriever(db_session)
    results = await retriever.retrieve_relevant_chunks("irrelevant query text", top_k=5, similarity_threshold=-1.0)

    assert len(results) == 2
    assert results[0].episode == "Ep A"
    assert results[0].score > results[1].score


async def test_similarity_threshold_filters_out_weak_matches(db_session, monkeypatch):
    query_vec = random_embedding(seed=2)
    far_vec = random_embedding(seed=888)

    await _insert_chunk(
        db_session, episode="Ep C", guest="Guest C", text="unrelated",
        embedding=far_vec, source_id="src-c",
    )

    monkeypatch.setattr("app.rag.retriever.embed_text", lambda q: query_vec)

    retriever = TranscriptRetriever(db_session)
    # Threshold of 0.99 should exclude a near-orthogonal random vector.
    results = await retriever.retrieve_relevant_chunks("query", top_k=5, similarity_threshold=0.99)

    assert results == []


async def test_retrieve_on_empty_table_returns_empty_list(db_session, monkeypatch):
    monkeypatch.setattr("app.rag.retriever.embed_text", lambda q: random_embedding(seed=3))

    retriever = TranscriptRetriever(db_session)
    results = await retriever.retrieve_relevant_chunks("anything", top_k=5, similarity_threshold=0.35)

    assert results == []


async def test_retrieve_respects_top_k(db_session, monkeypatch):
    query_vec = random_embedding(seed=4)
    for i in range(8):
        await _insert_chunk(
            db_session, episode=f"Ep {i}", guest=f"Guest {i}", text=f"chunk {i}",
            embedding=random_embedding(seed=4 + i), source_id=f"src-{i}",
        )

    monkeypatch.setattr("app.rag.retriever.embed_text", lambda q: query_vec)

    retriever = TranscriptRetriever(db_session)
    results = await retriever.retrieve_relevant_chunks("query", top_k=3, similarity_threshold=-1.0)

    assert len(results) == 3
