"""
routes.py
---------
All REST API route handlers for the feedback resource, plus the
image-upload static file mount helper. Business logic delegates to
crud.py; this module focuses on request/response handling, validation
errors, and HTTP status codes.
"""

import os
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/feedback", tags=["Feedback"])

# Allowed image types for the optional upload field
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _save_uploaded_image(image: UploadFile) -> str:
    """
    Validates and saves an uploaded image to the uploads directory.
    Returns the relative path stored in the database.
    Raises HTTPException on invalid file type or size.
    """
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type '{image.content_type}'. Allowed: JPEG, PNG, WEBP, GIF.",
        )

    file_extension = os.path.splitext(image.filename or "")[1] or ".jpg"
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    destination = settings.upload_path / unique_filename

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = image.file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    with open(destination, "wb") as buffer:
        buffer.write(contents)

    # Relative path used to build a URL for the frontend, e.g. uploads/<file>
    return f"{settings.UPLOAD_DIR}/{unique_filename}"


@router.post("", response_model=schemas.FeedbackOut, status_code=status.HTTP_201_CREATED)
def create_feedback(
    customer_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    visit_date: date = Form(...),
    flavour: str = Form(...),
    taste_rating: int = Form(...),
    quality_rating: int = Form(...),
    staff_rating: int = Form(...),
    cleanliness_rating: int = Form(...),
    overall_rating: int = Form(...),
    visit_again: schemas.YesNo = Form(...),
    recommend_shop: schemas.YesNo = Form(...),
    comments: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    POST /feedback
    Accepts multipart/form-data so an optional image file can be uploaded
    alongside the feedback fields. Validates all fields via FeedbackCreate.
    """
    try:
        feedback_in = schemas.FeedbackCreate(
            customer_name=customer_name,
            email=email,
            phone=phone,
            visit_date=visit_date,
            flavour=flavour,
            taste_rating=taste_rating,
            quality_rating=quality_rating,
            staff_rating=staff_rating,
            cleanliness_rating=cleanliness_rating,
            overall_rating=overall_rating,
            visit_again=visit_again,
            recommend_shop=recommend_shop,
            comments=comments,
        )
    except Exception as exc:  # Pydantic ValidationError or similar
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    image_path = None
    if image is not None and image.filename:
        image_path = _save_uploaded_image(image)

    try:
        db_feedback = crud.create_feedback(db, feedback_in, image_path=image_path)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save feedback: {exc}",
        )

    return db_feedback


@router.get("", response_model=schemas.FeedbackListResponse)
def read_all_feedback(
    page: int = Query(1, ge=1, description="Page number, starting at 1"),
    page_size: int = Query(20, ge=1, le=100, description="Number of records per page"),
    search: Optional[str] = Query(None, description="Search by customer name, email, or flavour"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Minimum overall rating"),
    max_rating: Optional[int] = Query(None, ge=1, le=5, description="Maximum overall rating"),
    start_date: Optional[date] = Query(None, description="Filter: visit_date >= start_date"),
    end_date: Optional[date] = Query(None, description="Filter: visit_date <= end_date"),
    sort_by: str = Query("created_at", description="created_at | visit_date | overall_rating | customer_name"),
    sort_order: str = Query("desc", description="asc | desc"),
    db: Session = Depends(get_db),
):
    """
    GET /feedback
    Retrieve all feedback records with optional search, filtering,
    sorting, and pagination — primarily used by the admin dashboard.
    """
    total, results = crud.get_all_feedback(
        db,
        page=page,
        page_size=page_size,
        search=search,
        min_rating=min_rating,
        max_rating=max_rating,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return schemas.FeedbackListResponse(total=total, page=page, page_size=page_size, results=results)


@router.get("/stats", response_model=schemas.FeedbackStats)
def read_feedback_stats(db: Session = Depends(get_db)):
    """
    GET /feedback/stats
    Returns aggregate statistics for the admin dashboard: average ratings,
    total feedback count, and recommendation percentage.
    NOTE: declared before /{feedback_id} so 'stats' isn't parsed as an ID.
    """
    stats = crud.get_feedback_stats(db)
    return schemas.FeedbackStats(**stats)


@router.get("/{feedback_id}", response_model=schemas.FeedbackOut)
def read_feedback_by_id(feedback_id: int, db: Session = Depends(get_db)):
    """GET /feedback/{id} - Retrieve a single feedback record by its ID."""
    db_feedback = crud.get_feedback_by_id(db, feedback_id)
    if db_feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Feedback with id {feedback_id} not found")
    return db_feedback


@router.put("/{feedback_id}", response_model=schemas.FeedbackOut)
def update_feedback(feedback_id: int, feedback_in: schemas.FeedbackUpdate, db: Session = Depends(get_db)):
    """PUT /feedback/{id} - Update an existing feedback record (partial update supported)."""
    db_feedback = crud.update_feedback(db, feedback_id, feedback_in)
    if db_feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Feedback with id {feedback_id} not found")
    return db_feedback


@router.delete("/{feedback_id}", response_model=schemas.MessageResponse)
def delete_feedback(feedback_id: int, db: Session = Depends(get_db)):
    """DELETE /feedback/{id} - Permanently delete a feedback record."""
    deleted = crud.delete_feedback(db, feedback_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Feedback with id {feedback_id} not found")
    return schemas.MessageResponse(message=f"Feedback with id {feedback_id} was deleted successfully")
