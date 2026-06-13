from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

company_competency = Table(
    "company_competency",
    Base.metadata,
    Column("company_id", Integer, ForeignKey("companies.id"), primary_key=True),
    Column("competency_id", Integer, ForeignKey("competencies.id"), primary_key=True),
    Column("score", Float, default=0.0),
)

project_competency = Table(
    "project_competency",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("competency_id", Integer, ForeignKey("competencies.id"), primary_key=True),
)


class Competency(Base):
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    category = Column(String(100))
    description = Column(Text)
    industry_demand = Column(Float, default=0.0)
    program_coverage = Column(Float, default=0.0)
    gap_score = Column(Float, default=0.0)
    source = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    vacancies = relationship("Vacancy", back_populates="competencies", secondary="vacancy_competency")
    companies = relationship("Company", back_populates="competencies", secondary=company_competency)
    projects = relationship("Project", back_populates="competencies", secondary=project_competency)


vacancy_competency = Table(
    "vacancy_competency",
    Base.metadata,
    Column("vacancy_id", Integer, ForeignKey("vacancies.id"), primary_key=True),
    Column("competency_id", Integer, ForeignKey("competencies.id"), primary_key=True),
)


class Vacancy(Base):
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), unique=True, index=True)
    title = Column(String(500), nullable=False)
    company_name = Column(String(500))
    description = Column(Text)
    requirements = Column(Text)
    salary_from = Column(Integer)
    salary_to = Column(Integer)
    region = Column(String(200))
    source = Column(String(50))
    url = Column(String(1000))
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    competencies = relationship("Competency", back_populates="vacancies", secondary=vacancy_competency)
