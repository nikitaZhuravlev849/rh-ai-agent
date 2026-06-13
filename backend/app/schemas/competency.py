from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CompetencyBase(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None


class CompetencyCreate(CompetencyBase):
    pass


class CompetencyUpdate(BaseModel):
    industry_demand: Optional[float] = None
    program_coverage: Optional[float] = None
    gap_score: Optional[float] = None


class CompetencyOut(CompetencyBase):
    id: int
    industry_demand: float
    program_coverage: float
    gap_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class CompetencyGapReport(BaseModel):
    total_competencies: int
    industry_only: List[CompetencyOut]
    program_only: List[CompetencyOut]
    matched: List[CompetencyOut]
    top_gaps: List[CompetencyOut]
    top_covered: List[CompetencyOut]


class VacancyBase(BaseModel):
    title: str
    company_name: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_from: Optional[int] = None
    salary_to: Optional[int] = None
    region: Optional[str] = None
    source: str
    url: Optional[str] = None


class VacancyOut(VacancyBase):
    id: int
    external_id: str
    competencies: List[CompetencyOut] = []
    created_at: datetime

    class Config:
        from_attributes = True
