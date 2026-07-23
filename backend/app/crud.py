"""
crud.py
-------
Database access layer (Create, Read, Update, Delete) for the Feedback model.
Keeping this logic separate from routes.py keeps route handlers thin and
makes the data-access logic easy to unit test in isolation.
"""

from datetime import date
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import Feedback
from app.schemas import FeedbackCreate, FeedbackUpdate


def create_feedback(db: Session, feedback_in: FeedbackCreate, image_path: Optional[str] = None) -> Feedback:
    """Insert a new feedback record and return the persisted row."""
    db_feedback = Feedback(
        customer_name=feedback_in.customer_name,
        email=feedback_in.email,
        phone=feedback_in.phone,
        visit_date=feedback_in.visit_date,
        flavour=feedback_in.flavour,
        taste_rating=feedback_in.taste_rating,
        quality_rating=feedback_in.quality_rating,
        staff_rating=feedback_in.staff_rating,
        cleanliness_rating=feedback_in.cleanliness_rating,
        overall_rating=feedback_in.overall_rating,
        visit_again=feedback_in.visit_again.value,
        recommend_shop=feedback_in.recommend_shop.value,
        comments=feedback_in.comments,
        image_path=image_path,
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def get_feedback_by_id(db: Session, feedback_id: int) -> Optional[Feedback]:
    """Fetch a single feedback record by primary key."""
    return db.query(Feedback).filter(Feedback.id == feedback_id).first()


def get_all_feedback(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """
    Fetch feedback records with optional search, rating filter, date filter,
    sorting, and pagination. Returns a tuple of (total_count, list_of_rows).

    - search: matches against customer_name, email, or flavour
    - min_rating/max_rating: filters on overall_rating
    - start_date/end_date: filters on visit_date
    """
    query = db.query(Feedback)

    if search:
        like_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Feedback.customer_name.ilike(like_pattern),
                Feedback.email.ilike(like_pattern),
                Feedback.flavour.ilike(like_pattern),
            )
        )

    if min_rating is not None:
        query = query.filter(Feedback.overall_rating >= min_rating)

    if max_rating is not None:
        query = query.filter(Feedback.overall_rating <= max_rating)

    if start_date is not None:
        query = query.filter(Feedback.visit_date >= start_date)

    if end_date is not None:
        query = query.filter(Feedback.visit_date <= end_date)

    total = query.count()

    # Whitelist sortable columns to avoid arbitrary attribute injection
    sortable_columns = {
        "created_at": Feedback.created_at,
        "visit_date": Feedback.visit_date,
        "overall_rating": Feedback.overall_rating,
        "customer_name": Feedback.customer_name,
    }
    sort_column = sortable_columns.get(sort_by, Feedback.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()

    return total, results


def update_feedback(db: Session, feedback_id: int, feedback_in: FeedbackUpdate) -> Optional[Feedback]:
    """Apply a partial update to an existing feedback record."""
    db_feedback = get_feedback_by_id(db, feedback_id)
    if db_feedback is None:
        return None

    update_data = feedback_in.model_dump(exclude_unset=True)

    # Convert Enum values (visit_again / recommend_shop) to plain strings
    for enum_field in ("visit_again", "recommend_shop"):
        if enum_field in update_data and update_data[enum_field] is not None:
            value = update_data[enum_field]
            update_data[enum_field] = value.value if hasattr(value, "value") else value

    for field_name, field_value in update_data.items():
        setattr(db_feedback, field_name, field_value)

    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def delete_feedback(db: Session, feedback_id: int) -> bool:
    """Delete a feedback record by ID. Returns True if a row was deleted."""
    db_feedback = get_feedback_by_id(db, feedback_id)
    if db_feedback is None:
        return False
    db.delete(db_feedback)
    db.commit()
    return True


def get_feedback_stats(db: Session) -> dict:
    """Compute aggregate statistics for the admin dashboard."""
    total = db.query(func.count(Feedback.id)).scalar() or 0

    if total == 0:
        return {
            "total_feedback": 0,
            "average_taste_rating": 0.0,
            "average_quality_rating": 0.0,
            "average_staff_rating": 0.0,
            "average_cleanliness_rating": 0.0,
            "average_overall_rating": 0.0,
            "recommend_percentage": 0.0,
            "visit_again_percentage": 0.0,
        }

    averages = db.query(
        func.avg(Feedback.taste_rating),
        func.avg(Feedback.quality_rating),
        func.avg(Feedback.staff_rating),
        func.avg(Feedback.cleanliness_rating),
        func.avg(Feedback.overall_rating),
    ).first()

    recommend_yes = db.query(func.count(Feedback.id)).filter(Feedback.recommend_shop == "Yes").scalar() or 0
    visit_again_yes = db.query(func.count(Feedback.id)).filter(Feedback.visit_again == "Yes").scalar() or 0

    return {
        "total_feedback": total,
        "average_taste_rating": round(float(averages[0] or 0), 2),
        "average_quality_rating": round(float(averages[1] or 0), 2),
        "average_staff_rating": round(float(averages[2] or 0), 2),
        "average_cleanliness_rating": round(float(averages[3] or 0), 2),
        "average_overall_rating": round(float(averages[4] or 0), 2),
        "recommend_percentage": round((recommend_yes / total) * 100, 2),
        "visit_again_percentage": round((visit_again_yes / total) * 100, 2),
    }
