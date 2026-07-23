"""
models.py
---------
SQLAlchemy ORM model(s) mapping Python classes to MySQL tables.

The Feedback model mirrors the `feedback` table created by
database/feedback.sql. Keep both files in sync if the schema changes.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Text,
    Enum,
    TIMESTAMP,
    SmallInteger,
    func,
)

from app.database import Base


class Feedback(Base):
    """ORM model representing a single customer feedback record."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Customer information
    customer_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    visit_date = Column(Date, nullable=False, index=True)

    # Visit details
    flavour = Column(String(100), nullable=False)

    # Ratings (1-5)
    taste_rating = Column(SmallInteger, nullable=False)
    quality_rating = Column(SmallInteger, nullable=False)
    staff_rating = Column(SmallInteger, nullable=False)
    cleanliness_rating = Column(SmallInteger, nullable=False)
    overall_rating = Column(SmallInteger, nullable=False, index=True)

    # Yes/No feedback
    visit_again = Column(Enum("Yes", "No", name="visit_again_enum"), nullable=False)
    recommend_shop = Column(Enum("Yes", "No", name="recommend_shop_enum"), nullable=False)

    # Free text feedback
    comments = Column(Text, nullable=True)

    # Optional uploaded image path (relative path stored, e.g. "uploads/xyz.jpg")
    image_path = Column(String(255), nullable=True)

    # Audit column
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper only
        return f"<Feedback id={self.id} customer_name={self.customer_name!r}>"
