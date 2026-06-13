from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base
from app.models.competency import project_competency


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    MATCHING = "matching"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectRole(Base):
    __tablename__ = "project_roles"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    role_name = Column(String(255), nullable=False)
    description = Column(Text)
    required_skills = Column(JSON, default=list)
    slots = Column(Integer, default=1)
    filled_slots = Column(Integer, default=0)
    difficulty = Column(String(50))
    effort_hours = Column(Integer)

    project = relationship("Project", back_populates="roles")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    title = Column(String(500), nullable=False)
    description = Column(Text)
    technical_spec = Column(Text)
    goals = Column(Text)
    expected_results = Column(Text)

    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    difficulty = Column(String(50))
    duration_weeks = Column(Integer)
    max_students = Column(Integer)
    enrolled_students = Column(Integer, default=0)

    modules = Column(JSON, default=list)
    evaluation_criteria = Column(JSON, default=list)
    timeline = Column(JSON, default=dict)

    agreement_date = Column(DateTime(timezone=True))
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", back_populates="projects")
    roles = relationship("ProjectRole", back_populates="project", cascade="all, delete-orphan")
    competencies = relationship("Competency", back_populates="projects", secondary=project_competency)
