.PHONY: up down build logs backend-shell test ingest download-transcripts

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

backend-shell:
	docker compose exec backend /bin/bash

test:
	docker compose exec backend pytest -v

download-transcripts:
	docker compose exec backend python scripts/download_transcripts.py

ingest:
	docker compose exec backend python scripts/ingest.py