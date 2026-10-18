"""Application configuration, loaded from environment variables / .env file."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = f"sqlite:///{BASE_DIR / 'instance' / 'reconciliation.db'}"

    # Auth / JWT
    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 1 day
    cookie_name: str = "recon_session"

    # CORS
    frontend_origin: str = "http://localhost:4200"

    # Upload / matching limits
    max_rows: int = 1000
    max_upload_mb: int = 10
    upload_dir: str = str(BASE_DIR / "instance" / "uploads")

    # Duplicate detection key is (date, description, amount) exact match per Appendix C


settings = Settings()
