FROM python:3.11-slim

WORKDIR /app

# System deps needed to build asyncpg / sentence-transformers deps.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# In production, run without --reload. docker-compose overrides this
# command for local dev if hot-reload is desired.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
