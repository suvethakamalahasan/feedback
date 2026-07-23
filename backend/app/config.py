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
import logging
from pathlib import Path
from typing import List
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Absolute path to the backend/ directory (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # ---- Database ----
    # Railway provides these env vars automatically when you add a MySQL plugin:
    #   MYSQLHOST, MYSQLPORT, MYSQLUSER, MYSQLPASSWORD, MYSQLDATABASE, MYSQL_URL
    # We check for all of them with sensible fallbacks for local dev.
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "icecream_feedback_db"

    # Railway-specific variable names (populated via Reference Variables)
    MYSQLHOST: str = ""
    MYSQLPORT: str = ""
    MYSQLUSER: str = ""
    MYSQLPASSWORD: str = ""
    MYSQLDATABASE: str = ""
    MYSQL_URL: str = ""
    DATABASE_URL: str = ""

    # ---- Application ----
    APP_NAME: str = "Ice Cream Shop Feedback API"
    APP_ENV: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ---- CORS ----
    CORS_ORIGINS: str = "http://localhost,http://127.0.0.1:5500,https://chipper-twilight-718163.netlify.app"

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
        """
        Builds the SQLAlchemy connection string for MySQL (PyMySQL driver).

        Priority order:
        1. MYSQL_URL / DATABASE_URL (Railway provides this as a full connection string)
        2. MYSQLHOST/MYSQLUSER/MYSQLPASSWORD/MYSQLDATABASE (Railway Reference Variables)
        3. DB_HOST/DB_USER/DB_PASSWORD/DB_NAME (local .env file)
        """
        # Option 1: Use MYSQL_URL or DATABASE_URL if available
        raw_url = self.MYSQL_URL or self.DATABASE_URL
        if raw_url:
            # Railway gives mysql:// but SQLAlchemy needs mysql+pymysql://
            url = raw_url.replace("mysql://", "mysql+pymysql://", 1)
            logger.info("Using MYSQL_URL/DATABASE_URL for database connection.")
            return url

        # Option 2: Use Railway individual variables
        host = self.MYSQLHOST or self.DB_HOST
        port = self.MYSQLPORT or str(self.DB_PORT)
        user = self.MYSQLUSER or self.DB_USER
        password = self.MYSQLPASSWORD or self.DB_PASSWORD
        db_name = self.MYSQLDATABASE or self.DB_NAME

        # URL-encode password to handle special characters
        encoded_password = quote_plus(password) if password else ""

        url = f"mysql+pymysql://{user}:{encoded_password}@{host}:{port}/{db_name}"
        logger.info("Database connection: %s@%s:%s/%s", user, host, port, db_name)
        return url

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
