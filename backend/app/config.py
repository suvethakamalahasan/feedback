"""
config.py
---------
Centralised application configuration.

Loads values from the .env file (via pydantic-settings) so that
sensitive information such as database credentials never lives in
source code. Import `settings` anywhere in the app to access
configuration values.
"""

import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the backend/ directory (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # ---- Database ----
    DB_HOST: str = os.getenv("MYSQLHOST", os.getenv("DB_HOST", "localhost"))
    DB_PORT: int = int(os.getenv("MYSQLPORT", os.getenv("DB_PORT", "3306")))
    DB_USER: str = os.getenv("MYSQLUSER", os.getenv("DB_USER", "root"))
    DB_PASSWORD: str = os.getenv("MYSQLPASSWORD", os.getenv("DB_PASSWORD", ""))
    DB_NAME: str = os.getenv("MYSQL_DATABASE", os.getenv("MYSQLDATABASE", os.getenv("DB_NAME", "icecream_feedback_db")))

    # ---- Application ----
    APP_NAME: str = "Ice Cream Shop Feedback API"
    APP_ENV: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ---- CORS ----
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1:5500,https://chipper-twilight-718163.netlify.app")

    # ---- File uploads ----
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 5

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        """Builds the SQLAlchemy connection string for MySQL (PyMySQL driver)."""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        """Returns CORS_ORIGINS as a clean list of strings."""
        origins = [origin.strip().rstrip('/') for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        netlify_url = "https://chipper-twilight-718163.netlify.app"
        if netlify_url not in origins:
            origins.append(netlify_url)
        return origins

    @property
    def upload_path(self) -> Path:
        """Absolute path to the uploads directory, created if missing."""
        path = BASE_DIR / self.UPLOAD_DIR
        path.mkdir(parents=True, exist_ok=True)
        return path


# Singleton settings instance used across the application
settings = Settings()
