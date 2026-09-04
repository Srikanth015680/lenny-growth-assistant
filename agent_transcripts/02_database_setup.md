# 02 — Database setup

This build sandbox has no Docker daemon, so rather than leave the DB layer
unverified, installed Postgres 16 + the `postgresql-16-pgvector` apt
package directly (both available via the sandbox's `archive.ubuntu.com`
mirror) and ran a real instance throughout the build.

Verified for real, against that live instance:
- `CREATE EXTENSION vector` succeeds, version 0.6.0, HNSW access method
  present (`\dx` output confirmed).
- `init_db()` (called from FastAPI's lifespan) creates all 4 tables and
  the `ix_transcript_chunks_embedding_hnsw` index automatically on backend
  startup — confirmed via `\dt` and `\di+` showing `access method: hnsw`
  — no manual `psql` step involved, satisfying section 6's requirement.
- A second `lenny_growth_assistant_test` database was created for the
  pytest suite, schema created/dropped per test session
  (`backend/tests/conftest.py`).

Bug found and fixed here: `TranscriptRetriever`'s cosine search and the
sessions API were both written against this real DB, which is what
surfaced two real bugs during API testing (see `09_testing_and_debugging.md`)
— the schema/index itself had no issues.
