"""
schemas.py
----------
Pydantic schemas used for request validation and response serialization.

- FeedbackBase / FeedbackCreate / FeedbackUpdate: used for incoming data.
- FeedbackOut: used for outgoing (response) data.
- FeedbackStats: used for the admin dashboard statistics endpoint.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class YesNo(str, Enum):
    """Restricts visit_again / recommend_shop fields to Yes/No only."""
    yes = "Yes"
    no = "No"


class FlavourEnum(str, Enum):
    """Allowed ice cream flavours shown in the frontend dropdown."""
    chocolate_fudge = "Chocolate Fudge"
    vanilla_bean = "Vanilla Bean"
    strawberry_swirl = "Strawberry Swirl"
    mango_delight = "Mango Delight"
    butterscotch = "Butterscotch"
    cookies_and_cream = "Cookies and Cream"
    pistachio = "Pistachio"
    black_currant = "Black Currant"
    mint_chocolate_chip = "Mint Chocolate Chip"
    red_velvet = "Red Velvet"
    coffee_mocha = "Coffee Mocha"
    other = "Other"


class FeedbackBase(BaseModel):
    """Shared fields/validation logic for creating and updating feedback."""

    customer_name: str = Field(..., min_length=2, max_length=150, examples=["Aarav Sharma"])
    email: EmailStr = Field(..., examples=["aarav.sharma@example.com"])
    phone: str = Field(..., min_length=7, max_length=20, examples=["9876543210"])
    visit_date: date = Field(..., examples=["2026-07-01"])
    flavour: str = Field(..., min_length=2, max_length=100, examples=["Chocolate Fudge"])

    taste_rating: int = Field(..., ge=1, le=5)
    quality_rating: int = Field(..., ge=1, le=5)
    staff_rating: int = Field(..., ge=1, le=5)
    cleanliness_rating: int = Field(..., ge=1, le=5)
    overall_rating: int = Field(..., ge=1, le=5)

    visit_again: YesNo
    recommend_shop: YesNo

    comments: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """Ensures phone number contains only digits, spaces, +, - and ()."""
        cleaned = value.strip()
        allowed = set("0123456789+-() ")
        if not all(ch in allowed for ch in cleaned):
            raise ValueError("Phone number contains invalid characters")
        digits_only = "".join(ch for ch in cleaned if ch.isdigit())
        if len(digits_only) < 7 or len(digits_only) > 15:
            raise ValueError("Phone number must contain between 7 and 15 digits")
        return cleaned

    @field_validator("customer_name")
    @classmethod
    def validate_customer_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Customer name cannot be empty")
        return cleaned


class FeedbackCreate(FeedbackBase):
    """Schema used when creating new feedback (image handled separately as a file upload)."""
    pass


class FeedbackUpdate(BaseModel):
    """
    Schema used for PUT /feedback/{id}.
    All fields optional so clients can send a partial or full update.
    """

    customer_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, min_length=7, max_length=20)
    visit_date: Optional[date] = None
    flavour: Optional[str] = Field(default=None, min_length=2, max_length=100)

    taste_rating: Optional[int] = Field(default=None, ge=1, le=5)
    quality_rating: Optional[int] = Field(default=None, ge=1, le=5)
    staff_rating: Optional[int] = Field(default=None, ge=1, le=5)
    cleanliness_rating: Optional[int] = Field(default=None, ge=1, le=5)
    overall_rating: Optional[int] = Field(default=None, ge=1, le=5)

    visit_again: Optional[YesNo] = None
    recommend_shop: Optional[YesNo] = None

    comments: Optional[str] = Field(default=None, max_length=2000)
    image_path: Optional[str] = None


class FeedbackOut(BaseModel):
    """Schema returned to clients for a single feedback record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    email: str
    phone: str
    visit_date: date
    flavour: str
    taste_rating: int
    quality_rating: int
    staff_rating: int
    cleanliness_rating: int
    overall_rating: int
    visit_again: str
    recommend_shop: str
    comments: Optional[str] = None
    image_path: Optional[str] = None
    created_at: datetime


class FeedbackListResponse(BaseModel):
    """Wraps a list of feedback records with pagination metadata."""

    total: int
    page: int
    page_size: int
    results: list[FeedbackOut]


class FeedbackStats(BaseModel):
    """Aggregate statistics used by the admin dashboard."""

    total_feedback: int
    average_taste_rating: float
    average_quality_rating: float
    average_staff_rating: float
    average_cleanliness_rating: float
    average_overall_rating: float
    recommend_percentage: float
    visit_again_percentage: float


class MessageResponse(BaseModel):
    """Generic message response, e.g. after a successful delete."""
    message: str
