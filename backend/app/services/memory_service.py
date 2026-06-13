import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.memory import AgentMemory, CommunicationPattern, AgentStrategy, EventType

logger = logging.getLogger(__name__)

PROGRAM_INFO = """
Программа ПроКомпетенции — это образовательная инициатива Уральского федерального университета (УрФУ),
в рамках которой студенты выполняют реальные проекты для компаний-партнёров.

Формат: команды студентов 3-5 человек работают над задачами компании в течение семестра (14-16 недель).
Роли: разработчики, аналитики, дизайнеры, менеджеры.
Направления: IT, Data Science, Product Management, UX/UI.
Стоимость для компании: бесплатно или символическая оплата за наставничество.
Выгоды: доступ к молодым кадрам, R&D, брендинг работодателя в университете.
"""


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        event_type: EventType,
        entity_type: str,
        entity_id: Optional[int],
        description: str,
        data: Optional[Dict[str, Any]] = None,
        outcome: Optional[str] = None,
        phase: Optional[int] = None,
        is_successful: Optional[bool] = None,
    ) -> AgentMemory:
        event = AgentMemory(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            data=data or {},
            outcome=outcome,
            phase=phase,
            is_successful=is_successful,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        entity_id: Optional[int] = None,
        phase: Optional[int] = None,
        limit: int = 100,
    ) -> List[AgentMemory]:
        q = select(AgentMemory).order_by(AgentMemory.created_at.desc()).limit(limit)
        if event_type:
            q = q.where(AgentMemory.event_type == event_type)
        if entity_id:
            q = q.where(AgentMemory.entity_id == entity_id)
        if phase:
            q = q.where(AgentMemory.phase == phase)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def update_communication_pattern(
        self,
        industry: str,
        company_size: str,
        tone: str,
        subject_template: str,
        body_template: str,
        was_successful: bool,
    ):
        q = select(CommunicationPattern).where(
            CommunicationPattern.industry == industry,
            CommunicationPattern.company_size == company_size,
            CommunicationPattern.tone == tone,
        )
        result = await self.db.execute(q)
        pattern = result.scalar_one_or_none()

        if pattern:
            pattern.usage_count += 1
            if was_successful:
                pattern.positive_responses += 1
            pattern.success_rate = pattern.positive_responses / pattern.usage_count
        else:
            pattern = CommunicationPattern(
                industry=industry,
                company_size=company_size,
                tone=tone,
                subject_template=subject_template,
                body_template=body_template,
                usage_count=1,
                positive_responses=1 if was_successful else 0,
                success_rate=1.0 if was_successful else 0.0,
            )
            self.db.add(pattern)
        await self.db.commit()

    async def get_best_pattern(self, industry: str, company_size: str) -> Optional[CommunicationPattern]:
        q = (
            select(CommunicationPattern)
            .where(
                CommunicationPattern.industry == industry,
                CommunicationPattern.company_size == company_size,
                CommunicationPattern.usage_count >= 3,
            )
            .order_by(CommunicationPattern.success_rate.desc())
            .limit(1)
        )
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def get_phase_stats(self) -> Dict[str, Any]:
        from sqlalchemy import case
        q = select(
            AgentMemory.phase,
            func.count(AgentMemory.id).label("total"),
            func.sum(case((AgentMemory.is_successful == True, 1), else_=0)).label("successful"),
        ).group_by(AgentMemory.phase)
        result = await self.db.execute(q)
        stats = {}
        for row in result:
            phase = row.phase
            if phase:
                stats[f"phase_{phase}"] = {
                    "total": row.total,
                    "successful": row.successful or 0,
                    "success_rate": round((row.successful or 0) / row.total, 2) if row.total else 0,
                }
        return stats

    def get_program_info(self) -> str:
        return PROGRAM_INFO
