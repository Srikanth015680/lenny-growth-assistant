# 03 — Transcript Ingestion

## Goal

Build an ingestion pipeline that can load transcript files, extract their
metadata, split them into searchable chunks, generate embeddings, and store
the results in PostgreSQL.

## Work Completed

Implemented:

- `scripts/download_transcripts.py`
- `scripts/ingest.py`

The ingestion pipeline supports:

- JSON transcripts with timestamped segments
- Simple text files containing transcript metadata and content

For each transcript, the pipeline extracts available metadata such as:

- episode title
- guest name
- publication date
- timestamp references

Transcript text is split into smaller chunks before embeddings are generated.

## Development Data

Synthetic transcript files were used during development:

- `sample_01_activation.json`
- `sample_02_pricing.json`

These files are clearly marked as sample data and are not presented as
actual Lenny's Podcast transcripts.

The samples were useful for testing the ingestion pipeline without depending
on the external transcript source during development.

## Verification

Tested ingestion against the development PostgreSQL database.

The initial test produced:

- 2 transcript files
- 2 stored chunks

Timestamp extraction was also verified. The stored chunks contained the
expected timestamp references from the sample transcript segments.

## Idempotency

Ran the ingestion process twice using the same input files.

The second run did not create duplicate chunks. The existing records were
updated through the ingestion upsert logic.

This makes the ingestion process safe to run again when the transcript
dataset is refreshed.

## Next Step

Connect the ingestion pipeline to the intended transcript dataset and verify
retrieval using the resulting embedding

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
  the same files, row count stayed at 2 — the `ON CONFLICT (source_id, chunk_index) DO UPDATE` upsert worked as intended, not a duplicate
  insert.
