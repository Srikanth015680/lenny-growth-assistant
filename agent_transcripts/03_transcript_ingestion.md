# 03 — Transcript ingestion

Wrote `download_transcripts.py` and `ingest.py` per section 7, supporting
two input formats (JSON with per-segment timestamps, and a simpler
header+body `.txt` format) — documented in `ingest.py`'s module docstring
and `docs/troubleshooting.md`.

Explicit decision: did **not** attempt to fetch or bundle real Lenny's
Podcast transcripts. That's copyrighted content this project has no
license to redistribute, regardless of the legitimate engineering purpose
— fetching/storing it would be a copyright violation independent of
intent. Instead wrote two clearly-labeled synthetic sample files
(`data/transcripts/sample_01_activation.json`, `sample_02_pricing.json`),
each carrying a `_notice` field stating they're placeholder content, not
real podcast transcripts.

Verified for real (against the live dev database from `02`):
- Ran ingestion against both sample files with a deterministic fake
  embedding function (real `sentence-transformers` wasn't installed — see
  `09_testing_and_debugging.md`) — 2 files in, 2 chunks out, both short
  enough to stay as a single chunk each.
- Confirmed per-segment timestamp extraction: the ingested rows carry
  `timestamp_ref` values (`00:01:00`, `00:02:10`) matching each sample
  file's first segment.
- Confirmed idempotency (section 7.9): ran ingestion a second time against
  the same files, row count stayed at 2 — the `ON CONFLICT (source_id,
  chunk_index) DO UPDATE` upsert worked as intended, not a duplicate
  insert.
