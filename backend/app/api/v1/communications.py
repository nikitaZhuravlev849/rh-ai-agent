from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.communication import Communication, CommunicationStatus, ReplyType
from app.models.company import Company, Contact
from app.schemas.communication import (
    CommunicationOut, CommunicationGenerateRequest,
    CommunicationApproveRequest, ReplyHandleRequest, OutreachStats,
)
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.models.memory import EventType

router = APIRouter(prefix="/communications", tags=["Фаза 3-4: Коммуникации"])
llm = LLMService()


@router.post("/generate", response_model=CommunicationOut)
async def generate_letter(data: CommunicationGenerateRequest, db: AsyncSession = Depends(get_db)):
    """Сгенерировать персонализированное письмо для компании через LLM."""
    company_result = await db.execute(select(Company).where(Company.id == data.company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    contact = None
    if data.contact_id:
        contact_result = await db.execute(select(Contact).where(Contact.id == data.contact_id))
        contact = contact_result.scalar_one_or_none()

    memory = MemoryService(db)
    program_info = memory.get_program_info()

    company_dict = {
        "name": company.name,
        "industry": company.industry,
        "region": company.region,
        "description": company.description,
        "tech_stack": company.tech_stack or [],
    }
    contact_dict = {"name": contact.name, "position": contact.position} if contact else None

    letter = await llm.generate_outreach_letter(
        company=company_dict,
        contact=contact_dict,
        program_info=program_info,
        tone=data.tone,
    )

    comm = Communication(
        company_id=data.company_id,
        contact_id=data.contact_id,
        channel=data.channel,
        status=CommunicationStatus.DRAFT,
        subject=letter.get("subject"),
        body_formal=letter.get("body") if data.tone == "formal" else None,
        body_informal=letter.get("body") if data.tone != "formal" else None,
        value_proposition=letter.get("value_proposition"),
    )
    db.add(comm)
    await db.commit()
    await db.refresh(comm)

    await memory.log_event(
        event_type=EventType.LETTER_GENERATED,
        entity_type="communication",
        entity_id=comm.id,
        description=f"Generated letter for {company.name}",
        phase=3,
    )
    return comm


@router.post("/generate-batch")
async def generate_batch_letters(
    company_ids: List[int],
    tone: str = "formal",
    db: AsyncSession = Depends(get_db),
):
    """Генерация писем для всего шорт-листа."""
    generated = []
    for company_id in company_ids:
        req = CommunicationGenerateRequest(company_id=company_id, tone=tone)
        try:
            comm = await generate_letter(req, db)
            generated.append({"company_id": company_id, "communication_id": comm.id})
        except Exception as e:
            generated.append({"company_id": company_id, "error": str(e)})
    return {"generated": len([g for g in generated if "communication_id" in g]), "results": generated}


@router.post("/approve", response_model=CommunicationOut)
async def approve_letter(data: CommunicationApproveRequest, db: AsyncSession = Depends(get_db)):
    """Точка эскалации №3 — человек утверждает письмо."""
    result = await db.execute(select(Communication).where(Communication.id == data.communication_id))
    comm = result.scalar_one_or_none()
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")

    comm.status = CommunicationStatus.APPROVED
    comm.body_used = data.approved_body or comm.body_formal or comm.body_informal
    comm.approved_by = data.approved_by
    comm.approved_at = datetime.utcnow()
    if data.scheduled_at:
        comm.scheduled_at = data.scheduled_at

    memory = MemoryService(db)
    await memory.log_event(
        event_type=EventType.LETTER_APPROVED,
        entity_type="communication",
        entity_id=comm.id,
        description=f"Letter approved by {data.approved_by}",
        data={"approved_by": data.approved_by},
        phase=3,
        is_successful=True,
    )
    await db.commit()
    await db.refresh(comm)
    return comm


@router.post("/{communication_id}/send")
async def send_letter(communication_id: int, db: AsyncSession = Depends(get_db)):
    """Отправить утверждённое письмо."""
    result = await db.execute(select(Communication).where(Communication.id == communication_id))
    comm = result.scalar_one_or_none()
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    if comm.status != CommunicationStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Communication must be approved before sending")

    from app.tasks.outreach_tasks import send_communication
    task = send_communication.delay(communication_id)
    return {"task_id": task.id, "message": "Письмо поставлено в очередь на отправку"}


@router.post("/reply", response_model=CommunicationOut)
async def handle_reply(data: ReplyHandleRequest, db: AsyncSession = Depends(get_db)):
    """Обработать входящий ответ компании."""
    result = await db.execute(select(Communication).where(Communication.id == data.communication_id))
    comm = result.scalar_one_or_none()
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")

    comm.reply_type = data.reply_type
    comm.reply_content = data.reply_content
    comm.replied_at = datetime.utcnow()
    comm.status = CommunicationStatus.REPLIED

    memory = MemoryService(db)
    is_positive = data.reply_type in (ReplyType.INTERESTED, ReplyType.MEETING_REQUEST)
    await memory.log_event(
        event_type=EventType.REPLY_RECEIVED,
        entity_type="communication",
        entity_id=comm.id,
        description=f"Reply received: {data.reply_type}",
        data={"reply_type": data.reply_type, "content_preview": data.reply_content[:100]},
        phase=4,
        is_successful=is_positive,
    )

    if is_positive:
        await memory.log_event(
            event_type=EventType.ESCALATION_TRIGGERED,
            entity_type="communication",
            entity_id=comm.id,
            description=f"Escalation #4: positive reply from company {comm.company_id}",
            phase=4,
        )

    await db.commit()
    await db.refresh(comm)
    return comm


@router.post("/{communication_id}/auto-classify-reply")
async def auto_classify_reply(
    communication_id: int,
    reply_text: str,
    db: AsyncSession = Depends(get_db),
):
    """Автоматически классифицировать ответ через LLM."""
    reply_type_str = await llm.classify_reply(reply_text)
    mapping = {
        "interested": ReplyType.INTERESTED,
        "meeting_request": ReplyType.MEETING_REQUEST,
        "question": ReplyType.QUESTION,
        "rejected": ReplyType.REJECTED,
        "no_reply": ReplyType.NO_REPLY,
    }
    reply_type = mapping.get(reply_type_str, ReplyType.NO_REPLY)
    req = ReplyHandleRequest(
        communication_id=communication_id,
        reply_content=reply_text,
        reply_type=reply_type,
    )
    return await handle_reply(req, db)


@router.get("/", response_model=List[CommunicationOut])
async def list_communications(
    company_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    q = select(Communication).order_by(Communication.created_at.desc()).limit(limit)
    if company_id:
        q = q.where(Communication.company_id == company_id)
    if status:
        q = q.where(Communication.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/stats", response_model=OutreachStats)
async def get_outreach_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Communication))
    all_comms = result.scalars().all()
    total_sent = len([c for c in all_comms if c.status in (CommunicationStatus.SENT, CommunicationStatus.DELIVERED,
                                                            CommunicationStatus.READ, CommunicationStatus.REPLIED)])
    replied = len([c for c in all_comms if c.status == CommunicationStatus.REPLIED])
    interested = len([c for c in all_comms if c.reply_type in (ReplyType.INTERESTED, ReplyType.MEETING_REQUEST)])

    return OutreachStats(
        total_sent=total_sent,
        delivered=len([c for c in all_comms if c.status in (CommunicationStatus.DELIVERED,
                                                              CommunicationStatus.READ, CommunicationStatus.REPLIED)]),
        read=len([c for c in all_comms if c.status in (CommunicationStatus.READ, CommunicationStatus.REPLIED)]),
        replied=replied,
        interested=interested,
        rejected=len([c for c in all_comms if c.reply_type == ReplyType.REJECTED]),
        pending_followup=len([c for c in all_comms if c.status == CommunicationStatus.SENT and not c.is_followup]),
        response_rate=round(replied / total_sent, 3) if total_sent else 0,
        interest_rate=round(interested / total_sent, 3) if total_sent else 0,
    )
