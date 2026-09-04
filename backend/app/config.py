"""
Central application configuration.

Everything the app needs from the environment is declared here, once, as a
typed Settings object. No other module should call `os.environ` directly —
import `settings` from here instead. This is what section 11 of the spec
means by "don't scatter provider-specific if/else logic" extended to config
in general: one source of truth, typed, validated at startup.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/lenny_growth_assistant"

    # --- LLM providers ---
    default_llm_provider: Literal["ollama", "anthropic"] = "ollama"

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_seconds: int = 60

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"

    # --- Embeddings / retrieval ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    retrieval_top_k: int = 5
    retrieval_threshold: float = 0.35

    # --- App ---
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    max_message_length: int = 4000

    # --- Transcript source ---
    transcript_source_url: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def anthropic_available(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    """Settings are read once and cached — safe because env vars don't
    change after process start, and this avoids re-parsing on every request."""
    return Settings()


settings = get_settings()
