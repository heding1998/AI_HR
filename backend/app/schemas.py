from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class JobCreate(BaseModel):
    code: str
    name: str
    location: str = ""


class JobUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    is_active: bool | None = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    location: str
    is_active: bool


class ScoringStandardAIn(BaseModel):
    category: str
    subcategory: str
    category_score: float
    subcategory_score: float


class ScoringStandardAOut(ScoringStandardAIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ScoringStandardBIn(BaseModel):
    category: str
    subcategory: str
    level1_indicator: str
    level2_indicator: str
    weight: int


class ScoringStandardBOut(ScoringStandardBIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ScoringStandardOut(BaseModel):
    a: list[ScoringStandardAOut]
    b: list[ScoringStandardBOut]


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    status: str
    total_count: int
    processed_count: int
    error: str | None
    created_at: datetime


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    job_id: int
    original_filename: str
    status: str
    error: str | None
    created_at: datetime
    extracted_content: dict | None = None
    score: float | None = None
    score_error: str | None = None


class ResumeDetailOut(ResumeOut):
    extracted_text: str


class BatchDetailOut(BatchOut):
    resumes: list[ResumeOut]
