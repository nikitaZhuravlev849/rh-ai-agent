from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from app.database import get_db
from app.models.competency import Competency, Vacancy
from app.schemas.competency import CompetencyOut, CompetencyGapReport
from app.tasks.parsing_tasks import run_vacancy_parsing

router = APIRouter(prefix="/industry", tags=["Фаза 1: Анализ индустрии"])


@router.post("/parse-vacancies")
async def trigger_vacancy_parsing(
    keywords: Optional[List[str]] = None,
    area: int = 1,
):
    """Запустить парсинг вакансий с HH.ru и Superjob."""
    task = run_vacancy_parsing.delay(keywords, area)
    return {"task_id": task.id, "status": "started", "message": "Парсинг запущен в фоне"}


@router.get("/competencies", response_model=List[CompetencyOut])
async def get_competencies(
    category: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    q = select(Competency).order_by(Competency.industry_demand.desc()).limit(limit)
    if category:
        q = q.where(Competency.category == category)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/gap-report", response_model=CompetencyGapReport)
async def get_gap_report(db: AsyncSession = Depends(get_db)):
    """Отчёт о пробелах между программой и индустрией."""
    result = await db.execute(select(Competency))
    all_comps = result.scalars().all()

    industry_only = [c for c in all_comps if c.program_coverage == 0 and c.industry_demand > 0]
    program_only = [c for c in all_comps if c.industry_demand == 0 and c.program_coverage > 0]
    matched = [c for c in all_comps if c.industry_demand > 0 and c.program_coverage > 0]
    top_gaps = sorted([c for c in all_comps if c.gap_score > 0], key=lambda x: x.gap_score, reverse=True)[:10]
    top_covered = sorted(matched, key=lambda x: x.program_coverage, reverse=True)[:10]

    return CompetencyGapReport(
        total_competencies=len(all_comps),
        industry_only=industry_only[:20],
        program_only=program_only[:20],
        matched=matched[:20],
        top_gaps=top_gaps,
        top_covered=top_covered,
    )


@router.get("/stats")
async def get_industry_stats(db: AsyncSession = Depends(get_db)):
    vac_count = await db.execute(select(func.count(Vacancy.id)))
    comp_count = await db.execute(select(func.count(Competency.id)))
    top_comps = await db.execute(
        select(Competency).order_by(Competency.industry_demand.desc()).limit(10)
    )
    return {
        "total_vacancies": vac_count.scalar(),
        "total_competencies": comp_count.scalar(),
        "top_demanded": [{"name": c.name, "demand": c.industry_demand} for c in top_comps.scalars()],
    }


@router.post("/approve-priority")
async def approve_priority_area(
    industry: str,
    priority_competencies: List[str],
    db: AsyncSession = Depends(get_db),
):
    """Точка эскалации №1 — человек утверждает приоритетную отрасль."""
    from app.services.memory_service import MemoryService
    from app.models.memory import EventType
    memory = MemoryService(db)
    await memory.log_event(
        event_type=EventType.HUMAN_DECISION,
        entity_type="industry",
        entity_id=None,
        description=f"Human approved industry: {industry}",
        data={"industry": industry, "competencies": priority_competencies},
        phase=1,
        is_successful=True,
    )
    from app.tasks.parsing_tasks import run_company_search
    run_company_search.delay(industry)
    return {
        "message": f"Отрасль '{industry}' утверждена. Запущен поиск компаний.",
        "competencies": priority_competencies,
    }
