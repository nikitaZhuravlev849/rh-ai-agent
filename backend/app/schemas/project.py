from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.project import ProjectStatus


class ProjectRoleBase(BaseModel):
    role_name: str
    description: Optional[str] = None
    required_skills: List[str] = []
    slots: int = 1
    difficulty: Optional[str] = None
    effort_hours: Optional[int] = None


class ProjectRoleOut(ProjectRoleBase):
    id: int
    filled_slots: int

    class Config:
        from_attributes = True


class ProjectGenerateRequest(BaseModel):
    company_id: int
    agreement_details: str
    competency_ids: Optional[List[int]] = None


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    technical_spec: Optional[str] = None
    goals: Optional[str] = None
    expected_results: Optional[str] = None
    difficulty: Optional[str] = None
    duration_weeks: Optional[int] = None
    max_students: Optional[int] = None
    modules: List[str] = []
    evaluation_criteria: List[str] = []


class ProjectCreate(ProjectBase):
    company_id: int


class ProjectOut(ProjectBase):
    id: int
    company_id: int
    status: ProjectStatus
    enrolled_students: int
    roles: List[ProjectRoleOut] = []
    agreement_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectCatalogItem(BaseModel):
    id: int
    title: str
    company_name: str
    difficulty: Optional[str]
    duration_weeks: Optional[int]
    max_students: Optional[int]
    enrolled_students: int
    status: ProjectStatus
    roles_count: int
    competencies: List[str] = []
