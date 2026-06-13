from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.communication import CommunicationStatus, ReplyType, CommunicationChannel


class CommunicationGenerateRequest(BaseModel):
    company_id: int
    contact_id: Optional[int] = None
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    tone: str = "formal"
    include_followup_plan: bool = True


class CommunicationApproveRequest(BaseModel):
    communication_id: int
    approved_body: Optional[str] = None
    approved_by: str
    scheduled_at: Optional[datetime] = None


class CommunicationOut(BaseModel):
    id: int
    company_id: int
    contact_id: Optional[int] = None
    channel: CommunicationChannel
    status: CommunicationStatus
    reply_type: Optional[ReplyType] = None
    subject: Optional[str] = None
    body_formal: Optional[str] = None
    body_informal: Optional[str] = None
    body_used: Optional[str] = None
    value_proposition: Optional[str] = None
    is_followup: bool
    followup_number: int
    sent_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    reply_content: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReplyHandleRequest(BaseModel):
    communication_id: int
    reply_content: str
    reply_type: ReplyType


class OutreachStats(BaseModel):
    total_sent: int
    delivered: int
    read: int
    replied: int
    interested: int
    rejected: int
    pending_followup: int
    response_rate: float
    interest_rate: float
