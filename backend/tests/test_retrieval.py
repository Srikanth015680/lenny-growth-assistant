from app.models.db_models import TranscriptChunk
from app.rag.retriever import TranscriptRetriever
from tests.conftest import random_embedding


async def insert_chunk(
    db_session,
    *,
    episode,
    guest,
    text,
    embedding,
    source_id,
    chunk_index=0,
):
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


async def test_retrieval_returns_closest_chunk_first(
    db_session,
    monkeypatch,
):
    query_vector = random_embedding(seed=1)

    await insert_chunk(
        db_session,
        episode="Ep A",
        guest="Guest A",
        text="close match",
        embedding=query_vector,
        source_id="src-a",
    )

    await insert_chunk(
        db_session,
        episode="Ep B",
        guest="Guest B",
        text="far match",
        embedding=random_embedding(seed=999),
        source_id="src-b",
    )

    monkeypatch.setattr(
        "app.rag.retriever.embed_text",
        lambda query: query_vector,
    )

    retriever = TranscriptRetriever(db_session)

    results = await retriever.retrieve_relevant_chunks(
        "activation ideas",
        top_k=5,
        similarity_threshold=-1.0,
    )

    assert len(results) == 2
    assert results[0].episode == "Ep A"
    assert results[0].score > results[1].score


async def test_similarity_threshold_filters_weak_matches(
    db_session,
    monkeypatch,
):
    query_vector = random_embedding(seed=2)

    await insert_chunk(
        db_session,
        episode="Ep C",
        guest="Guest C",
        text="unrelated",
        embedding=random_embedding(seed=888),
        source_id="src-c",
    )

    monkeypatch.setattr(
        "app.rag.retriever.embed_text",
        lambda query: query_vector,
    )

    retriever = TranscriptRetriever(db_session)

    results = await retriever.retrieve_relevant_chunks(
        "query",
        top_k=5,
        similarity_threshold=0.99,
    )

    assert results == []


async def test_retrieval_returns_empty_list_when_database_is_empty(
    db_session,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.rag.retriever.embed_text",
        lambda query: random_embedding(seed=3),
    )

    retriever = TranscriptRetriever(db_session)

    results = await retriever.retrieve_relevant_chunks(
        "anything",
        top_k=5,
        similarity_threshold=0.35,
    )

    assert results == []


async def test_retrieval_respects_top_k(
    db_session,
    monkeypatch,
):
    query_vector = random_embedding(seed=4)

    for index in range(8):
        await insert_chunk(
            db_session,
            episode=f"Ep {index}",
            guest=f"Guest {index}",
            text=f"chunk {index}",
            embedding=random_embedding(seed=4 + index),
            source_id=f"src-{index}",
        )

    monkeypatch.setattr(
        "app.rag.retriever.embed_text",
        lambda query: query_vector,
    )

    retriever = TranscriptRetriever(db_session)

    results = await retriever.retrieve_relevant_chunks(
        "query",
        top_k=3,
        similarity_threshold=-1.0,
    )

    assert len(results) == 3