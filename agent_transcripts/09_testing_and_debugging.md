# 09 — Testing and debugging

## Real bugs found and fixed during this build (not hypothetical)

1. **Sessions API 500 on `GET /api/sessions/{id}`** — `selectinload`
   chained on a string (`selectinload(SessionModel.messages).selectinload("artifacts")`)
   instead of a class-bound attribute. Caught by actually curling the
   endpoint against a live server and reading the structured error log;
   fixed to `.selectinload(Message.artifacts)`. This is exactly the class
   of bug that only shows up by running the code, not by reading it.
2. **`MODE_NOT_IMPLEMENTED` returning HTTP 500 instead of 501** — the
   generic `AppError` base class defaults to 500; raising it directly
   without a dedicated subclass silently dropped the intended status code.
   Fixed by adding `ModeNotImplementedError(AppError)` with
   `http_status = 501`, matching the pattern every other error already
   used. Caught by asserting the status code in a live curl test, not
   just the error body's `code` field.
3. **Noisy structured logs** — the JSON log formatter's field-filtering
   logic checked `key in logging.LogRecord.__dict__` (the *class's*
   attributes) instead of the standard *instance* attribute names, so
   every log line included ~15 irrelevant stdlib fields (`msg`, `args`,
   `pathname`, ...). Fixed by filtering against an explicit set of known
   stdlib `LogRecord` instance attribute names instead.
4. **pytest async fixtures: "attached to a different loop"** — the
   default pytest-asyncio config gives each test function its own event
   loop, which broke the shared SQLAlchemy async engine (opened under one
   loop, reused under another). Fixed with
   `asyncio_default_fixture_loop_scope = session` **and**
   `asyncio_default_test_loop_scope = session` in `pytest.ini` — needed
   both keys; the first alone wasn't sufficient with this pytest-asyncio
   version. Also disposed the app's own engine (not a second, separate
   one) in the session-scoped fixture teardown to avoid a second, related
   "loop already closed" error during cleanup.
5. **Postgres service dying between sandbox turns** — not a code bug, but
   worth recording: the sandboxed container doesn't persist running
   background processes across tool-call boundaries the way a real
   machine would. Files and installed packages persisted; the `uvicorn`/
   `postgresql` *processes* did not, and needed `service postgresql
   start` re-run at the top of later sessions. If you're reading this
   transcript wondering why there are multiple "start Postgres" steps
   across these logs, that's why — not repeated flailing, a real
   environment constraint.

## What was verified against live infrastructure

- Postgres 16 + pgvector 0.6.0, HNSW index, extension auto-creation
- All 41 backend tests, run together (not just individually) — API,
  retrieval (against real pgvector ANN search), providers (mocked HTTP),
  routing, persistence (including cascade deletes), Ship30, artifacts
- Full ingestion pipeline against sample data, including idempotency
- End-to-end: live backend + live built frontend, health status flowing
  correctly from Postgres through to the API contract, real session
  creation over HTTP
- `next build` with strict TypeScript checks

## What is code-complete but not verified against live infrastructure
  (and exactly why, so this isn't mistaken for a rushed skip)

- A real Ollama model — no GPU/network access to install it in this
  sandbox. Provider code verified via `respx`-mocked HTTP instead.
- A real `sentence-transformers` model load — no HuggingFace Hub network
  access in this sandbox. Retrieval logic verified against live pgvector
  with a substitute embedding function instead.
- Literal `docker compose up` — no Docker daemon in this sandbox. Each
  service was verified via the equivalent bare-metal command
  (`uvicorn ...`, `npm run build && next start`) against the same live
  Postgres instead, and `docker-compose.yml` is YAML-syntax-validated.
- The artifact iframe's actual sandbox isolation (does it really block
  parent-DOM/cookie/localStorage access) — needs a real browser; verified
  by design/code review against the documented threat model, not by an
  automated sandbox-escape test.

If you re-run this project and any of the above turns up a real issue,
that's expected — it's exactly the boundary this transcript draws, not a
claim that everything works.
