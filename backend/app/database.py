"""
database.py
-----------
SQLAlchemy engine, session factory, and declarative base.

This module is responsible ONLY for the database connection plumbing.
Table definitions live in models.py, and CRUD logic lives in crud.py.
"""

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------
# pool_pre_ping=True avoids "MySQL server has gone away" errors on
# long-lived connections by testing the connection before using it.
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# ---------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------------
# Declarative base used by all ORM models
# ---------------------------------------------------------------------
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session and guarantees
    it is closed after the request finishes, even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
