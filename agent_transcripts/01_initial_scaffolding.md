# 01 — Initial scaffolding

Built the full repository tree from the spec's section 3 in one pass:
backend (`app/{models,api,providers,rag,agent,skills}`, `scripts`,
`tests`), frontend (`src/{app,components,hooks,lib}`), `docs/`,
`agent_transcripts/`, `data/{transcripts,processed}`.

Wrote `.env.example` and `.gitignore` first, then backend foundations in
this order: `config.py` (pydantic-settings, one typed source of truth),
`logging_config.py` (structured JSON logs), `exceptions.py` (one
`AppError` base class + a subclass per failure mode, each with a fixed
`code` + HTTP status — this shape is what section 23's structured error
responses turned into).

Decision: scoped "Phase 1" wider than a literal empty skeleton — included
the SQLAlchemy models and async DB engine too, since they're foundational
and don't depend on anything else being built first. This diverged from a
minimal-scaffold-only interpretation on purpose; flagged to the user
before continuing past it.
