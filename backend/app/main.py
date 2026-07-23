"""
main.py
-------
FastAPI application entrypoint for the Ice Cream Shop Customer Feedback
System. Wires together configuration, database, routes, CORS, static
file serving for uploaded images, and global error handling.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
(from inside the backend/ directory)
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import Base, engine
from app.routes import router as feedback_router

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("icecream_feedback_api")

# ---------------------------------------------------------------------
# FastAPI app instance
# ---------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description="REST API for collecting and managing ice cream shop customer feedback.",
    version="1.0.0",
)

# ---------------------------------------------------------------------
# CORS - allow the frontend (served separately) to call this API
# ---------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# Static file serving for uploaded feedback images
# ---------------------------------------------------------------------
app.mount(f"/{settings.UPLOAD_DIR}", StaticFiles(directory=str(settings.upload_path)), name="uploads")

# ---------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------
app.include_router(feedback_router)


# ---------------------------------------------------------------------
# Startup: create database tables if they do not already exist
# ---------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except SQLAlchemyError as exc:
        logger.error("Failed to connect to or initialize the database: %s", exc)
        logger.error(
            "Please verify your MySQL server is running and the credentials "
            "in backend/.env are correct, and that 'icecream_feedback_db' exists "
            "(run database/feedback.sql first)."
        )


# ---------------------------------------------------------------------
# Root / health check endpoints
# ---------------------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    """Simple health check / welcome endpoint."""
    return {
        "message": f"{settings.APP_NAME} is running.",
        "docs": "/docs",
        "status": "ok",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint used by uptime monitors / load balancers."""
    return {"status": "healthy"}


# ---------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a clean, consistent JSON structure for validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Validation failed. Please check the submitted fields.",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Catch-all handler for unexpected database errors."""
    logger.error("Database error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "A database error occurred. Please try again later."},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler so unexpected errors never leak stack traces to clients."""
    logger.error("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred. Please try again later."},
    )
