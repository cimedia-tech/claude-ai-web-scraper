from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Claude
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    claude_model: str = Field("claude-haiku-4-5", env="CLAUDE_MODEL")
    max_tokens: int = Field(4096, env="MAX_TOKENS")

    # Crawling
    max_pages_per_run: int = Field(50, env="MAX_PAGES_PER_RUN")
    page_timeout_ms: int = Field(30000, env="PAGE_TIMEOUT_MS")
    request_delay_min: float = Field(1.5, env="REQUEST_DELAY_MIN")
    request_delay_max: float = Field(4.5, env="REQUEST_DELAY_MAX")
    max_token_input: int = Field(8000, env="MAX_TOKEN_INPUT")

    # Cache
    cache_ttl_hours: int = Field(24, env="CACHE_TTL_HOURS")
    db_path: str = Field("data/scraper_cache.db", env="DB_PATH")

    # Output
    output_dir: str = Field("output", env="OUTPUT_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
