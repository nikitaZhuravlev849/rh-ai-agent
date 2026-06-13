from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.competency import company_competency


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    inn = Column(String(20), unique=True, index=True)
    industry = Column(String(200))
    size = Column(String(50))
    region = Column(String(200))
    website = Column(String(500))
    description = Column(Text)
    tech_stack = Column(JSON, default=list)

    email = Column(String(255))
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    hh_url = Column(String(500))

    score = Column(Float, default=0.0)
    score_breakdown = Column(JSON, default=dict)
    is_verified = Column(Boolean, default=False)
    is_shortlisted = Column(Boolean, default=False)
    is_partner = Column(Boolean, default=False)

    source = Column(String(100))
    external_id = Column(String(200))
    raw_data = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    competencies = relationship("Competency", back_populates="companies", secondary=company_competency)
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="company", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="company")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255))
    position = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    is_decision_maker = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="contacts")
