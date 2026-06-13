from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class EventType(str, enum.Enum):
    VACANCY_PARSED = "vacancy_parsed"
    COMPANY_FOUND = "company_found"
    COMPANY_SCORED = "company_scored"
    COMPANY_SHORTLISTED = "company_shortlisted"
    LETTER_GENERATED = "letter_generated"
    LETTER_APPROVED = "letter_approved"
    LETTER_SENT = "letter_sent"
    REPLY_RECEIVED = "reply_received"
    MEETING_SCHEDULED = "meeting_scheduled"
    AGREEMENT_SIGNED = "agreement_signed"
    PROJECT_CREATED = "project_created"
    ESCALATION_TRIGGERED = "escalation_triggered"
    HUMAN_DECISION = "human_decision"


class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(EventType), nullable=False, index=True)
    entity_type = Column(String(100))
    entity_id = Column(Integer)
    description = Column(Text)
    outcome = Column(String(50))
    data = Column(JSON, default=dict)
    feedback_score = Column(Float)
    feedback_text = Column(Text)
    phase = Column(Integer)
    is_successful = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommunicationPattern(Base):
    __tablename__ = "communication_patterns"

    id = Column(Integer, primary_key=True, index=True)
    industry = Column(String(200))
    company_size = Column(String(50))
    tone = Column(String(50))
    subject_template = Column(Text)
    body_template = Column(Text)
    success_rate = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    positive_responses = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AgentStrategy(Base):
    __tablename__ = "agent_strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    parameters = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    performance_score = Column(Float, default=0.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
