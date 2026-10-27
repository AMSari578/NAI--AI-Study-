from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    database_url: str = f"sqlite:///{BASE_DIR / 'najm.db'}"
    jwt_secret: str = "development-only-change-me"
    jwt_expire_minutes: int = 60 * 24 * 7
    ai_provider: str = "local"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma3:4b"
    frontend_origin: str = "http://localhost:3000"
    max_upload_mb: int = 15
    model_config = SettingsConfigDict(env_file=(BASE_DIR.parent / ".env", BASE_DIR / ".env"), extra="ignore")

settings = Settings()
