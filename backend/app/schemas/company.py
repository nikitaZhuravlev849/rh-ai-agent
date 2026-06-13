from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ContactBase(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    is_decision_maker: bool = False
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass  # company_id comes from URL path, not request body


class ContactOut(ContactBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyBase(BaseModel):
    name: str
    inn: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    region: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    tech_stack: List[str] = []
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None


class CompanyCreate(CompanyBase):
    source: Optional[str] = None
    external_id: Optional[str] = None


class CompanyUpdate(BaseModel):
    is_verified: Optional[bool] = None
    is_shortlisted: Optional[bool] = None
    score: Optional[float] = None
    notes: Optional[str] = None


class ScoreBreakdown(BaseModel):
    tech_stack_score: float = 0.0
    competency_match_score: float = 0.0
    size_score: float = 0.0
    reputation_score: float = 0.0
    education_experience_score: float = 0.0
    total: float = 0.0


class CompanyOut(CompanyBase):
    id: int
    score: float
    score_breakdown: Dict[str, Any] = {}
    is_verified: bool
    is_shortlisted: bool
    is_partner: bool
    source: Optional[str] = None
    contacts: List[ContactOut] = []
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyShortlist(BaseModel):
    companies: List[CompanyOut]
    total: int
    page: int
    per_page: int


class CompanyVerifyRequest(BaseModel):
    company_ids: List[int]
    action: str = Field(..., pattern="^(approve|reject|shortlist)$")
