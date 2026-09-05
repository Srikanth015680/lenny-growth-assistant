
# 02 — Database Setup

## Goal

Set up PostgreSQL with pgvector and verify that the backend can create and use the required database schema.

## Work Completed

The build environment did not have a Docker daemon available, so PostgreSQL 16 and pgvector were installed directly for development and testing.

Verified:

- PostgreSQL 16 is running.
- The `vector` extension is available.
- pgvector supports the HNSW index used for transcript embeddings.
- The FastAPI startup process creates the required database tables automatically.
- The transcript embedding index is created during database initialization.
- A separate test database is used by pytest.

The application does not require manually creating the database tables with `psql`.

## Database Tables

The initial schema contains:

- `sessions`
- `messages`
- `artifacts`
- `transcript_chunks`

## Testing

A separate test database was created so the test suite does not use the development database.

The database layer was tested against a real PostgreSQL instance rather than only mocked objects.

## Issues Found

While testing the database-backed API, issues were found in:

- transcript retrieval
- session API behavior

These were fixed during the later API testing/debugging stage and are documented in `09_testing_and_debugging.md`.

## Result

PostgreSQL, pgvector, the database schema, and the vector index were successfully verified.
