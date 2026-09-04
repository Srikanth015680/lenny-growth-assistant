#!/usr/bin/env python3
"""
Transcript ingestion (section 7).

INPUT FORMAT (documented here + docs/troubleshooting.md — files live in
data/transcripts/):

  1) JSON (preferred — carries per-segment timestamps):
     {
       "episode_title": "Episode name",
       "guest_name": "Guest Name",
       "publication_date": "2024-03-01",
       "segments": [
         {"timestamp": "00:01:15", "text": "..."},
         {"timestamp": "00:04:40", "text": "..."}
       ]
     }

  2) Plain text, with a small header:
     EPISODE: Episode name
     GUEST: Guest Name
     DATE: 2024-03-01
     ---
     <full transcript text, no per-chunk timestamps available>

Chunking targets ~500-800 tokens with ~100 token overlap (app/rag/chunker.py).
Each chunk is upserted keyed on (source_id, chunk_index) — the unique index
declared in app/models/db_models.py — so re-running ingestion on the same
file updates existing chunks instead of duplicating them (section 7.9).

Run: python backend/scripts/ingest.py
"""
import asyncio
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import AsyncSessionLocal, init_db
from app.logging_config import configure_logging, get_logger
from app.models.db_models import TranscriptChunk
from app.rag.chunker import chunk_transcript
from app.rag.embeddings import embed_batch

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "transcripts"

logger = get_logger(__name__)


@dataclass
class ParsedTranscript:
    episode_title: str
    guest_name: str | None
    publication_date: str | None
    full_text: str
    # word_index -> timestamp, for files that carry per-segment timestamps.
    timestamp_at_word: dict[int, str]


def _parse_json(path: Path) -> ParsedTranscript:
    data = json.loads(path.read_text())
    segments = data.get("segments", [])
    words: list[str] = []
    timestamp_at_word: dict[int, str] = {}
    for segment in segments:
        timestamp_at_word[len(words)] = segment.get("timestamp", "")
        words.extend(segment.get("text", "").split())
    return ParsedTranscript(
        episode_title=data["episode_title"],
        guest_name=data.get("guest_name"),
        publication_date=data.get("publication_date"),
        full_text=" ".join(words),
        timestamp_at_word=timestamp_at_word,
    )


def _parse_txt(path: Path) -> ParsedTranscript:
    raw = path.read_text()
    header, _, body = raw.partition("---")
    fields = {}
    for line in header.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip().upper()] = value.strip()
    return ParsedTranscript(
        episode_title=fields.get("EPISODE", path.stem),
        guest_name=fields.get("GUEST"),
        publication_date=fields.get("DATE"),
        full_text=" ".join(body.split()),
        timestamp_at_word={},
    )


def _timestamp_for_word_index(parsed: ParsedTranscript, word_index: int) -> str | None:
    if not parsed.timestamp_at_word:
        return None
    applicable = [w for w in parsed.timestamp_at_word if w <= word_index]
    if not applicable:
        return None
    return parsed.timestamp_at_word[max(applicable)]


async def ingest_file(
    session,
    path: Path,
    embed_fn: Callable[[list[str]], list[list[float]]] = embed_batch,
) -> int:
    if path.suffix == ".json":
        parsed = _parse_json(path)
    elif path.suffix == ".txt":
        parsed = _parse_txt(path)
    else:
        logger.warning("ingest_skipped_unsupported_file", extra={"file": str(path)})
        return 0

    if not parsed.full_text.strip():
        logger.warning("ingest_skipped_empty_transcript", extra={"file": str(path)})
        return 0

    chunks = chunk_transcript(parsed.full_text)
    if not chunks:
        return 0

    embeddings = embed_fn([c.text for c in chunks])
    source_id = path.stem

    # Track approximate word offset per chunk to look up a timestamp, since
    # chunk_transcript() only returns chunk text/index, not offsets.
    words_seen = 0
    for chunk, embedding in zip(chunks, embeddings):
        timestamp_ref = _timestamp_for_word_index(parsed, words_seen)
        words_seen += len(chunk.text.split())

        stmt = (
            pg_insert(TranscriptChunk)
            .values(
                episode_title=parsed.episode_title,
                guest_name=parsed.guest_name,
                publication_date=parsed.publication_date,
                timestamp_ref=timestamp_ref,
                chunk_text=chunk.text,
                source_id=source_id,
                chunk_index=chunk.index,
                metadata_json={"word_count": len(chunk.text.split())},
                embedding=embedding,
            )
            .on_conflict_do_update(
                index_elements=["source_id", "chunk_index"],
                set_={
                    "episode_title": parsed.episode_title,
                    "guest_name": parsed.guest_name,
                    "publication_date": parsed.publication_date,
                    "timestamp_ref": timestamp_ref,
                    "chunk_text": chunk.text,
                    "metadata_json": {"word_count": len(chunk.text.split())},
                    "embedding": embedding,
                },
            )
        )
        await session.execute(stmt)

    await session.commit()
    logger.info(
        "ingest_file_complete",
        extra={"file": str(path), "source_id": source_id, "chunks": len(chunks)},
    )
    return len(chunks)


async def ingest_all() -> None:
    configure_logging()
    await init_db()

    if not DATA_DIR.exists():
        logger.warning("ingest_no_data_dir", extra={"path": str(DATA_DIR)})
        return

    files = sorted(list(DATA_DIR.glob("*.json")) + list(DATA_DIR.glob("*.txt")))
    if not files:
        logger.warning("ingest_no_files_found", extra={"path": str(DATA_DIR)})
        print(f"No transcript files found in {DATA_DIR}. See download_transcripts.py.")
        return

    total_chunks = 0
    async with AsyncSessionLocal() as session:
        for path in files:
            total_chunks += await ingest_file(session, path)

    logger.info("ingest_all_complete", extra={"files": len(files), "total_chunks": total_chunks})
    print(f"Ingested {len(files)} file(s), {total_chunks} chunk(s) total.")


if __name__ == "__main__":
    asyncio.run(ingest_all())
    sys.exit(0)
