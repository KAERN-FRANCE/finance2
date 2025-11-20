"""
Configuration settings for the Meeting Assistant application.
Loads environment variables and provides configuration classes.
"""
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    openai_api_key: str
    anthropic_api_key: str

    # Paths
    vector_db_path: str = "./data/vector_db"
    upload_dir: str = "./data/uploads"
    reports_dir: str = "./reports"
    database_url: str = "sqlite:///./data/meetings.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Limits
    max_upload_size_mb: int = 100
    max_documents: int = 1000
    max_meeting_duration_hours: int = 4

    # Audio
    audio_chunk_duration_seconds: int = 30
    whisper_model: str = "whisper-1"
    whisper_language: str = "auto"

    # Claude
    claude_model: str = "claude-sonnet-4-5-20250929"
    claude_max_tokens: int = 4096
    claude_temperature: float = 0.7

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Languages
    supported_languages: str = "fr,en"
    default_language: str = "fr"

    # Security
    secret_key: str = "change-this-to-a-random-secret-key"
    access_token_expire_minutes: int = 60

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def supported_languages_list(self) -> List[str]:
        """Parse supported languages into a list."""
        return [lang.strip() for lang in self.supported_languages.split(",")]

    def ensure_directories(self):
        """Ensure all required directories exist."""
        for path in [self.vector_db_path, self.upload_dir, self.reports_dir, Path(self.log_file).parent]:
            Path(path).mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_directories()
