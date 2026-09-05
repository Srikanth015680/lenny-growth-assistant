#!/usr/bin/env python3

import asyncio
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from app.database import AsyncSessionLocal, init_db
from app.logging_config import configure_logging, get_logger
from app.models.db_models import TranscriptChunk
from app.rag.chunker import chunk_transcript
from app.rag.embeddings import embed_batch


logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTS_DIR = PROJECT_ROOT / "data" / "transcripts"


@dataclass
class ParsedTranscript:
    episode_title: str
    guest_name: str | None
    publication_date: str | None
    text: str
    timestamps: dict[int, str]


def parse_json(path: Path) -> ParsedTranscript:
    data = json.loads(path.read_text(encoding="utf-8"))

    words: list[str] = []
    timestamps: dict[int, str] = {}

    for segment in data.get("segments", []):
        text = segment.get("text", "").strip()

        if not text:
            continue

        timestamps[len(words)] = segment.get("timestamp", "")
        words.extend(text.split())

    return ParsedTranscript(
        episode_title=data.get("episode_title", path.stem),
        guest_name=data.get("guest_name"),
        publication_date=data.get("publication_date"),
        text=" ".join(words),
        timestamps=timestamps,
    )


def parse_text(path: Path) -> ParsedTranscript:
    content = path.read_text(encoding="utf-8")
    header, _, body = content.partition("---")

    metadata: dict[str, str] = {}

    for line in header.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        metadata[key.strip().upper()] = value.strip()

    return ParsedTranscript(
        episode_title=metadata.get("EPISODE", path.stem),
        guest_name=metadata.get("GUEST"),
        publication_date=metadata.get("DATE"),
        text=" ".join(body.split()),
        timestamps={},
    )


def parse_transcript(path: Path) -> ParsedTranscript | None:
    if path.suffix.lower() == ".json":
        return parse_json(path)

    if path.suffix.lower() == ".txt":
        return parse_text(path)

    logger.warning(
        "unsupported_transcript_file",
        extra={"file": str(path)},
    )
    return None


def get_timestamp(
    timestamps: dict[int, str],
    word_index: int,
) -> str | None:
    if not timestamps:
        return None

    positions = [position for position in timestamps if position <= word_index]

    if not positions:
        return None

    return timestamps[max(positions)]


async def ingest_file(
    session,
    path: Path,
    embed_fn: Callable[[list[str]], list[list[float]]] = embed_batch,
) -> int:
    transcript = parse_transcript(path)

    if transcript is None:
        return 0

    if not transcript.text.strip():
        logger.warning(
            "empty_transcript",
            extra={"file": str(path)},
        )
        return 0

    chunks = chunk_transcript(transcript.text)

    if not chunks:
        return 0

    embeddings = embed_fn([chunk.text for chunk in chunks])
    source_id = path.stem

    word_index = 0

    for chunk, embedding in zip(chunks, embeddings):
        timestamp = get_timestamp(
            transcript.timestamps,
            word_index,
        )

        word_index += len(chunk.text.split())

        statement = (
            insert(TranscriptChunk)
            .values(
                episode_title=transcript.episode_title,
                guest_name=transcript.guest_name,
                publication_date=transcript.publication_date,
                timestamp_ref=timestamp,
                chunk_text=chunk.text,
                source_id=source_id,
                chunk_index=chunk.index,
                metadata_json={
                    "word_count": len(chunk.text.split()),
                },
                embedding=embedding,
            )
            .on_conflict_do_update(
                index_elements=["source_id", "chunk_index"],
                set_={
                    "episode_title": transcript.episode_title,
                    "guest_name": transcript.guest_name,
                    "publication_date": transcript.publication_date,
                    "timestamp_ref": timestamp,
                    "chunk_text": chunk.text,
                    "metadata_json": {
                        "word_count": len(chunk.text.split()),
                    },
                    "embedding": embedding,
                },
            )
        )

        await session.execute(statement)

    await session.commit()

    logger.info(
        "transcript_ingested",
        extra={
            "file": str(path),
            "source_id": source_id,
            "chunks": len(chunks),
        },
    )

    return len(chunks)


async def ingest_all() -> None:
    configure_logging()
    await init_db()

    if not TRANSCRIPTS_DIR.exists():
        logger.warning(
            "transcript_directory_missing",
            extra={"path": str(TRANSCRIPTS_DIR)},
        )
        return

    files = sorted(
        [
            *TRANSCRIPTS_DIR.glob("*.json"),
            *TRANSCRIPTS_DIR.glob("*.txt"),
        ]
    )

    if not files:
        print(f"No transcript files found in {TRANSCRIPTS_DIR}")
        return

    total_chunks = 0

    async with AsyncSessionLocal() as session:
        for path in files:
            total_chunks += await ingest_file(session, path)

    logger.info(
        "ingestion_complete",
        extra={
            "files": len(files),
            "chunks": total_chunks,
        },
    )

    print(
        f"Ingested {len(files)} file(s) "
        f"and {total_chunks} chunk(s)."
    )


if __name__ == "__main__":
    try:
        asyncio.run(ingest_all())
    except KeyboardInterrupt:
        print("\nIngestion cancelled.")
        sys.exit(130)