from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class CommunicationStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    REPLIED = "replied"
    BOUNCED = "bounced"
    REJECTED = "rejected"


class ReplyType(str, enum.Enum):
    INTERESTED = "interested"
    REJECTED = "rejected"
    QUESTION = "question"
    MEETING_REQUEST = "meeting_request"
    NO_REPLY = "no_reply"


class CommunicationChannel(str, enum.Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"


class Communication(Base):
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"))

    channel = Column(Enum(CommunicationChannel), default=CommunicationChannel.EMAIL)
    status = Column(Enum(CommunicationStatus), default=CommunicationStatus.DRAFT)
    reply_type = Column(Enum(ReplyType))

    subject = Column(String(500))
    body_formal = Column(Text)
    body_informal = Column(Text)
    body_used = Column(Text)
    value_proposition = Column(Text)

    is_followup = Column(Boolean, default=False)
    followup_number = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("communications.id"))

    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    replied_at = Column(DateTime(timezone=True))
    reply_content = Column(Text)

    scheduled_at = Column(DateTime(timezone=True))
    approved_by = Column(String(255))
    approved_at = Column(DateTime(timezone=True))

    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", back_populates="communications")
    contact = relationship("Contact")
    followups = relationship("Communication", foreign_keys=[parent_id])
