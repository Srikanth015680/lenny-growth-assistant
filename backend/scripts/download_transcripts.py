#!/usr/bin/env python3
"""
Downloads transcript source files into data/transcripts/ (section 7).

This repository does not bundle real Lenny's Podcast transcripts — that's
copyrighted content this project has no license to redistribute. Instead:

  - If TRANSCRIPT_SOURCE_URL is set, this script expects it to point at a
    .zip archive of transcript files (in the format documented in
    docs/troubleshooting.md and backend/scripts/ingest.py's module
    docstring) and extracts it into data/transcripts/.
  - If it's unset, this script does nothing but explain how to supply your
    own transcripts — either by pointing TRANSCRIPT_SOURCE_URL at an
    archive you have the rights to use, or by placing files directly in
    data/transcripts/ yourself.

Run: python backend/scripts/download_transcripts.py
"""
import io
import sys
import zipfile
from pathlib import Path

import httpx

from app.config import settings

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "transcripts"

NO_SOURCE_MESSAGE = """\
TRANSCRIPT_SOURCE_URL is not set — nothing to download.

This project intentionally does not bundle real Lenny's Podcast transcripts
(that's copyrighted content). To get real data into the pipeline:

  1. Obtain transcripts you have the rights to use (e.g. your own export,
     or a licensed dataset), formatted per docs/troubleshooting.md, and
     place the files directly in:
         data/transcripts/

  2. OR host a .zip of correctly-formatted files somewhere reachable and
     set TRANSCRIPT_SOURCE_URL to it, then re-run this script.

  3. For a quick end-to-end test of the ingestion pipeline itself (chunking,
     embedding, idempotent upsert) without real data, see the synthetic
     sample files already in data/transcripts/sample_*.json — those are
     clearly-labeled placeholder content, not real podcast transcripts.

Once files are in place, run: python backend/scripts/ingest.py
"""


def main() -> int:
    if not settings.transcript_source_url:
        print(NO_SOURCE_MESSAGE)
        return 0

    print(f"Downloading transcript archive from {settings.transcript_source_url} ...")
    try:
        resp = httpx.get(settings.transcript_source_url, timeout=60, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"ERROR: could not download transcript archive: {exc}", file=sys.stderr)
        return 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            zf.extractall(DATA_DIR)
    except zipfile.BadZipFile:
        print(
            "ERROR: TRANSCRIPT_SOURCE_URL did not point to a valid .zip archive.",
            file=sys.stderr,
        )
        return 1

    print(f"Extracted transcript archive into {DATA_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
