#!/usr/bin/env python3

import io
import sys
import zipfile
from pathlib import Path

import httpx

from app.config import settings


ROOT_DIR = Path(__file__).resolve().parents[2]
TRANSCRIPTS_DIR = ROOT_DIR / "data" / "transcripts"


def extract_zip(content: bytes) -> None:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise ValueError("Downloaded file is not a valid ZIP archive") from exc

    with archive:
        root = TRANSCRIPTS_DIR.resolve()

        for file in archive.infolist():
            path = (TRANSCRIPTS_DIR / file.filename).resolve()

            if not path.is_relative_to(root):
                raise ValueError(f"Unsafe path in archive: {file.filename}")

        archive.extractall(TRANSCRIPTS_DIR)


def main() -> int:
    url = settings.transcript_source_url

    if not url:
        print(
            "TRANSCRIPT_SOURCE_URL is not configured. "
            "Add transcript files to data/transcripts/ manually."
        )
        return 0

    print("Downloading transcripts...")

    try:
        response = httpx.get(
            url,
            timeout=60,
            follow_redirects=True,
        )
        response.raise_for_status()

        extract_zip(response.content)

    except httpx.TimeoutException:
        print("Transcript download timed out.", file=sys.stderr)
        return 1

    except httpx.HTTPError as exc:
        print(f"Failed to download transcripts: {exc}", file=sys.stderr)
        return 1

    except ValueError as exc:
        print(f"Invalid transcript archive: {exc}", file=sys.stderr)
        return 1

    print(f"Transcripts extracted to {TRANSCRIPTS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())