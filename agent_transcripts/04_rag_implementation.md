
# 04 — RAG Implementation

## Goal

Implement transcript retrieval using PostgreSQL and pgvector so that user
questions can be matched against relevant transcript chunks.

## Work Completed

Implemented:

- `rag/retriever.py`
- `rag/embeddings.py`
- `rag/citation.py`
- `rag/prompts.py`

The retriever:

1. Generates an embedding for the user's query.
2. Searches transcript embeddings using cosine similarity.
3. Orders results by similarity in PostgreSQL.
4. Limits the number of returned chunks.
5. Applies a similarity threshold.
6. Returns the transcript metadata needed for citations.

The similarity search is performed in PostgreSQL rather than retrieving all
vectors and sorting them in Python.

## Grounding

Added a grounding prompt that instructs the model to:

- use the retrieved transcript context as its source of knowledge
- avoid inventing unsupported information
- acknowledge when the retrieved context is insufficient
- identify relevant transcript sources
- treat transcript content as data rather than instructions

This also protects against transcript text attempting to override the
assistant's instructions.

## Embeddings

The embedding layer uses `sentence-transformers` and is designed to load the
model lazily so that it does not need to be initialized for every request.

During development, the embedding model could not be downloaded in the
build environment because the required packages/model weights were
unavailable.

Instead of skipping retrieval testing, a deterministic embedding function
was used in the integration tests.

## Verification

The retrieval system was tested against a real PostgreSQL + pgvector
database.

The tests verified:

- nearest-neighbor ordering
- similarity threshold filtering
- `top_k` limiting
- empty retrieval behavior
- PostgreSQL vector search

The test embedding vectors were deterministic, so retrieval behavior could
be tested independently from the external embedding model.

## Result

The RAG retrieval layer is implemented and tested independently from the
embedding model.

The next step is to verify the complete flow using the configured embedding
model and connect retrieval to the LLM/agent layer.
