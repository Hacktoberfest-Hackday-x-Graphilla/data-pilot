from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate repository root where .env is stored
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"

class Settings(BaseSettings):
    APP_NAME: str = "DataPilot API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Model Provider Selection: "gemini" (default) or "gemma"
    AI_PROVIDER: str = "gemini"

    # Gemini configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3-flash-preview"
    
    # Gemma configuration (OpenAI-compatible)
    GEMMA_MODEL: str = "gemma2-9b-it"
    GEMMA_API_KEY: str = ""
    GEMMA_API_BASE: str = "https://api.groq.com/openai/v1"
    
    # DataPilot storage & limits
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] = [".csv"]
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def has_gemini_key(self) -> bool:
        """Safely verify key availability without exposing its value."""
        return bool(self.GEMINI_API_KEY and len(self.GEMINI_API_KEY.strip()) > 0)

    @property
    def has_gemma_key(self) -> bool:
        """Safely verify Gemma key availability without exposing its value."""
        return bool(self.GEMMA_API_KEY and len(self.GEMMA_API_KEY.strip()) > 0)

settings = Settings()
