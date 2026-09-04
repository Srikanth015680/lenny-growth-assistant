# Troubleshooting

## "Ollama unavailable" / health shows `ollama: down`

`/api/health` calls `GET {OLLAMA_BASE_URL}/api/tags` and checks the
configured model is pulled. Fixes, in order:

1. Is Ollama actually running? `ollama serve` (or check the `ollama`
   Compose service: `docker compose logs ollama`).
2. Is the model pulled? `ollama pull llama3.2:3b` (or whatever
   `OLLAMA_MODEL` is set to) — the health response's `detail` field says
   exactly which model is missing.
3. Running Ollama natively on your host instead of the Compose `ollama`
   service (common — lets it use your host GPU)? Set
   `OLLAMA_BASE_URL=http://host.docker.internal:11434` in `.env` and
   comment out the `ollama` service in `docker-compose.yml`.

The app never crashes when Ollama is down — chat requests against the
`ollama` provider will fail with a structured `OLLAMA_UNAVAILABLE` /
`OLLAMA_TIMEOUT` error; switch the provider selector to Anthropic (if
configured) as a workaround.

## Transcript file format for ingestion

`backend/scripts/ingest.py` reads every `.json`/`.txt` file in
`data/transcripts/`. Full format spec is in that script's module
docstring; summary:

**JSON (preferred — carries per-segment timestamps):**
```json
{
  "episode_title": "Episode name",
  "guest_name": "Guest Name",
  "publication_date": "2024-03-01",
  "segments": [
    {"timestamp": "00:01:15", "text": "..."},
    {"timestamp": "00:04:40", "text": "..."}
  ]
}
```

**Plain text (no per-chunk timestamps):**
```
EPISODE: Episode name
GUEST: Guest Name
DATE: 2024-03-01
---
<full transcript text>
```

This repository does **not** include real Lenny's Podcast transcripts —
that's copyrighted content with no redistribution license. Two clearly
labeled synthetic sample files
(`data/transcripts/sample_01_activation.json`,
`sample_02_pricing.json`) exist purely to exercise the ingestion pipeline
end to end; they are placeholder text, not real episode content, and say
so in a `_notice` field. Supply your own rights-cleared transcripts
(formatted per above) before demoing real answers.

## `TRANSCRIPT_SOURCE_URL`

`download_transcripts.py` expects this to point at a `.zip` of correctly
formatted files if set. If you don't have a hosted archive, skip it and
place files directly in `data/transcripts/` yourself, then run
`python backend/scripts/ingest.py` (or `make ingest`).

## Sandbox / build-environment limitations (read this if numbers here don't match what you see)

This project's initial build happened inside a sandboxed environment
without a Docker daemon and without network access to Ollama's installer
or HuggingFace Hub. Concretely, that means:

- **`sentence-transformers` / embeddings**: the code in
  `app/rag/embeddings.py` is real, but the model weights for
  `all-MiniLM-L6-v2` were never downloaded in that sandbox — retrieval
  logic was verified against a live Postgres+pgvector instance using a
  deterministic fake embedding function instead of a real model load. The
  actual model load path only gets exercised the first time you run this
  for real (in Docker, with real network access) — if it fails, check
  outbound network access to `huggingface.co` from the `backend`
  container.
- **Ollama itself**: never installed/run in that sandbox (no GPU, no
  network access to the Ollama installer). The provider code
  (`app/providers/ollama_provider.py`) was verified with `respx`-mocked
  HTTP responses, not a live model. First real run against a live Ollama
  is on you — if `/api/health` doesn't go green after `ollama serve` +
  `ollama pull <model>`, see the section above.
- **`docker compose up` itself**: never run as literal Compose in that
  sandbox (no Docker daemon available there). `docker-compose.yml` is
  YAML-validated and each service's Dockerfile was written against the
  same dependency versions verified to work via a plain venv/npm install —
  but the full multi-container orchestration is unverified until you run
  it. If something doesn't come up, `docker compose logs <service>` first.
- **Frontend build**: this WAS verified for real — `npm install` +
  `next build` succeeds cleanly (including strict TypeScript checks) — see
  `agent_transcripts/08_frontend.md`.
- **PostCSS security advisory**: `npm audit` reports 5 high-severity
  findings, all a transitive PostCSS dependency bundled *inside* Next.js
  14's own build tooling (source-map path traversal, build-time only —
  not a runtime/production vulnerability). Fully resolving it requires
  upgrading to Next 15/16, a breaking change not attempted here for time
  reasons — see README's "Known limitations."

None of this means the affected code is untested — see each module's own
test file for what *was* verified, and the module docstrings for exactly
what substitute was used in place of the missing dependency.

## Database won't initialize / `pgvector` extension missing

`init_db()` runs `CREATE EXTENSION IF NOT EXISTS vector` automatically on
backend startup — this requires the Postgres image to have the pgvector
extension available, which is why `docker-compose.yml` uses
`pgvector/pgvector:pg16` rather than the plain `postgres:16` image. If
you swap the image, install pgvector into it first.

## Empty / generic answers even with data ingested

Check `RETRIEVAL_THRESHOLD` in `.env` — if it's set too high, legitimate
matches get filtered out and you'll see the grounded-refusal message
instead of an answer. `RETRIEVAL_TOP_K` and the threshold are both request
tunable via `TranscriptRetriever.retrieve_relevant_chunks()`'s defaults in
`app/config.py`.
