from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from app.models import ApplicationStatus


# ---------- Users & auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Applications ----------
class ApplicationBase(BaseModel):
    company: str = Field(min_length=1, max_length=120, examples=["Takealot"])
    position: str = Field(min_length=1, max_length=120, examples=["Junior Python Developer"])
    location: str | None = Field(default=None, max_length=120, examples=["Cape Town"])
    job_url: HttpUrl | None = None
    salary_range: str | None = Field(default=None, max_length=60, examples=["R25k - R30k"])
    status: ApplicationStatus = ApplicationStatus.applied
    applied_on: date | None = None
    notes: str | None = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    """Every field is optional so clients can send only what changed (PATCH)."""

    company: str | None = Field(default=None, min_length=1, max_length=120)
    position: str | None = Field(default=None, min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    job_url: HttpUrl | None = None
    salary_range: str | None = Field(default=None, max_length=60)
    status: ApplicationStatus | None = None
    applied_on: date | None = None
    notes: str | None = None


class ApplicationOut(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_url: str | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ApplicationOut]


class Stats(BaseModel):
    total: int
    by_status: dict[ApplicationStatus, int]
    response_rate: float = Field(
        description="Share of submitted applications that got a reply "
        "(interviewing, offer or rejected), from 0 to 1."
    )
