from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ------------------------------------------------------------------
    # LLM — Option A: Anthropic Claude (claude-sonnet-4-6)
    # ------------------------------------------------------------------
    ANTHROPIC_API_KEY: str = ""

    # ------------------------------------------------------------------
    # LLM — Option B: OpenAI-compatible endpoint (Qwen3-32B via vLLM,
    #                  GPT-4o-mini, etc.)
    # Priority: OPENAI_API_KEY wins over ANTHROPIC_API_KEY when both set
    # ------------------------------------------------------------------
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "http://localhost:8000/v1"   # vLLM default
    OPENAI_MODEL: str = "Qwen/Qwen3-32B"

    # ------------------------------------------------------------------
    # RAG corpus
    # ------------------------------------------------------------------
    # Absolute or relative path to the repo-root data/ directory
    DATA_DIR: str = str(Path(__file__).resolve().parents[3] / "data")

    # Sentence-Transformers model for semantic embeddings
    # all-MiniLM-L6-v2 is a good CPU-friendly default
    EMBED_MODEL: str = "all-MiniLM-L6-v2"

    # Number of top documents to retrieve per query
    TOP_K: int = 10

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
