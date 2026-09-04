# The Lenny Growth Assistant

A grounded RAG chat assistant over Lenny's Podcast transcript archive, for
product managers and growth leads. Every answer cites the episode it came
from; the assistant refuses rather than guesses when the archive doesn't
cover a question. Built with Next.js, FastAPI, PostgreSQL + pgvector, and
a swappable Ollama/Anthropic provider layer.

## 1. Product overview

Ask a product/growth question → the assistant retrieves the most relevant
transcript passages (cosine similarity over embeddings, pgvector + HNSW),
answers strictly from that retrieved context with inline citations, and
can turn the same grounded context into a Ship 30-style essay or a
Markdown/HTML artifact rendered in a Claude-style side-by-side viewer.
Sessions persist; follow-up questions keep conversation context.

## 2. Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full breakdown
(component boundaries, schema, API contracts, RAG/embedding pipeline,
security model) with Mermaid diagrams. One-paragraph version: Next.js
frontend ↔ FastAPI backend (REST + SSE) ↔ Postgres/pgvector, with an
Ollama-or-Anthropic provider abstraction and a small agent-routing layer
dispatching to plain chat, a Ship30 essay skill, or an artifact-generation
skill.

## 3. Prerequisites

- Docker + Docker Compose
- [Ollama](https://ollama.com) — either run it inside Compose (included,
  commented setup below) or natively on your host for GPU access
- (Optional) an Anthropic API key, if you want the cloud fallback provider

## 4. Installation

```bash
git clone <this-repo>
cd lenny-growth-assistant
cp .env.example .env
# edit .env if needed — the defaults work for an all-in-Docker setup
```

## 5. Environment variables

See [`.env.example`](.env.example) for the full list with inline
documentation. The important ones:

| Variable | Default | Notes |
|---|---|---|
| `DEFAULT_LLM_PROVIDER` | `ollama` | App must work with this alone, no key needed |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Point at `http://host.docker.internal:11434` if running Ollama natively |
| `OLLAMA_MODEL` | `llama3.2:3b` | Alternatives: `llama3.1:8b`, `mistral:7b` |
| `ANTHROPIC_API_KEY` | *(empty)* | Optional — leave empty to run Ollama-only |
| `RETRIEVAL_TOP_K` / `RETRIEVAL_THRESHOLD` | `5` / `0.35` | Tune retrieval strictness |
| `TRANSCRIPT_SOURCE_URL` | *(empty)* | See §8 |

## 6. Ollama setup

**Option A — inside Docker Compose (default):**
```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.2:3b
```

**Option B — natively on your host** (recommended if you have a GPU):
```bash
ollama serve
ollama pull llama3.2:3b
```
Then in `.env`: `OLLAMA_BASE_URL=http://host.docker.internal:11434`, and
comment out the `ollama` service in `docker-compose.yml`.

## 7. Cloud provider setup (optional)

Set `ANTHROPIC_API_KEY` in `.env`. Never commit this file — it's already
gitignored. With no key set, the `anthropic` provider is simply
unavailable (`/api/health` reports `not_configured`) and the app runs on
Ollama alone.

## 8. Transcript ingestion

**This repository does not include real Lenny's Podcast transcripts** —
that's copyrighted content with no redistribution rights here. Two
clearly-labeled *synthetic* sample files ship in `data/transcripts/` so
you can exercise the pipeline immediately:

```bash
docker compose exec backend python scripts/ingest.py
# or: make ingest
```

For real data: obtain rights-cleared transcripts, format them per
[`docs/troubleshooting.md`](docs/troubleshooting.md#transcript-file-format-for-ingestion),
place them in `data/transcripts/` (or host a `.zip` and set
`TRANSCRIPT_SOURCE_URL`, then `make download-transcripts`), and re-run
ingestion — it's idempotent, safe to re-run on the same files.

## 9. Running the application

```bash
docker compose up --build
```
Frontend: http://localhost:3000 · Backend: http://localhost:8000 ·
Health: http://localhost:8000/api/health

## 10. Testing

```bash
docker compose exec backend pytest -v
# or: make test
```
41 tests across API, retrieval, providers, routing, persistence, and the
Ship30/artifact skills — run against a real Postgres+pgvector schema
(created/dropped per test session) with external LLM calls mocked (no live
Ollama or paid API calls required). See §"Known limitations" for what
wasn't (and couldn't be) exercised in the original build sandbox.

## 11. API documentation

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/sessions` | Create a session |
| `GET` | `/api/sessions` | List sessions |
| `GET` | `/api/sessions/{id}` | Session + full history |
| `POST` | `/api/chat` | Grounded chat (SSE) — `mode`: `default` \| `ship30` \| `artifact` |
| `GET` | `/api/artifacts/{id}` | Read a persisted artifact |
| `GET` | `/api/health` | Structured dependency diagnostics |

Full request/response shapes: `backend/app/models/schemas.py`. SSE event
sequence: `docs/architecture.md`.

## 12. Troubleshooting

See [`docs/troubleshooting.md`](docs/troubleshooting.md) — Ollama
connectivity, transcript format, and (importantly) exactly which parts of
this build were verified against live infrastructure vs. mocked, and why.

## 13. Security model

See [`docs/architecture.md`](docs/architecture.md#artifact-security) for
the full artifact sandboxing threat model. Summary: generated HTML runs in
an iframe with `sandbox="allow-scripts"` and **no** `allow-same-origin` —
it cannot read this app's DOM, cookies, or localStorage. Transcript
content retrieved into a prompt is explicitly marked as data, not
instructions, in every grounding prompt (guards against prompt injection
via transcript text — section 37 of the original spec). Secrets are never
logged (`app/logging_config.py` redacts by key name) and never leak into
error responses (`app/exceptions.py` returns a generic message for
unhandled exceptions, full detail only in server-side logs).

## 14. Project structure

See the tree in §"Final output" below, or browse `backend/app/` and
`frontend/src/` directly — both are organized by concern (api / agent /
rag / skills / providers on the backend; components / hooks / lib on the
frontend).

## 15. Deployment

`docker-compose.yml` is written for local/single-host deployment
(`db` + `backend` + `frontend` + optional `ollama`, with a named volume
for Postgres data and health-check-gated startup ordering). For a real
production deployment you'd want to additionally: put a real domain +
TLS in front of `frontend`/`backend`, move `ANTHROPIC_API_KEY` to a
secrets manager rather than a `.env` file, and point `DATABASE_URL` at a
managed Postgres with pgvector support instead of the containerized one.

## 16. Known limitations

- No auth/multi-tenancy — single shared session list (see PRD "Out of
  scope")
- `infer_mode_from_text` (free-text "turn that into an essay" intent
  detection) is a documented, currently-inert seam — mode selection today
  is the frontend's explicit Ask/Ship30/Artifact picker, not text
  inference
- Mobile artifact viewer is a full-screen overlay, not a drag-gesture
  bottom sheet (see `docs/design.md`'s trade-offs)
- No dark mode
- `npm audit` reports 5 high-severity findings, all a transitive
  PostCSS dependency bundled inside Next.js 14's own toolchain
  (build-time source-map path traversal — not a runtime vulnerability).
  Fully resolving it means a Next 15/16 major upgrade, not attempted here
  — see `docs/troubleshooting.md`.
- Built in a sandbox without Docker-in-Docker, a GPU, or HuggingFace/Ollama
  network access — `docker compose up` as literal Compose, a live Ollama
  model, and a live sentence-transformers model load are all
  code-complete but **not yet run for real**. Everything else in this
  list (schema + HNSW index creation, all 41 backend tests, the full
  ingestion pipeline against sample data, and `next build`) **was** run
  and verified against live infrastructure. Full transparency in
  `docs/troubleshooting.md`.

## 17. Future improvements

- Real free-text mode inference (the `infer_mode_from_text` seam)
- Streaming token counts / cost tracking per provider
- Editing or regenerating a past message/artifact in place
- A proper mobile bottom-sheet for the artifact viewer
- CI running the pytest suite + `next build` on every push
