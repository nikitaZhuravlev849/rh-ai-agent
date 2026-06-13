from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.company import Company
from app.models.communication import Communication, CommunicationStatus, ReplyType
from app.models.project import Project, ProjectStatus
from app.models.competency import Vacancy, Competency
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/dashboard", tags=["Дашборд"])


@router.get("/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Общая сводка прогресса по всем фазам."""
    company_count = (await db.execute(select(func.count(Company.id)))).scalar()
    shortlisted_count = (await db.execute(
        select(func.count(Company.id)).where(Company.is_shortlisted == True)
    )).scalar()
    partner_count = (await db.execute(
        select(func.count(Company.id)).where(Company.is_partner == True)
    )).scalar()

    comm_count = (await db.execute(select(func.count(Communication.id)))).scalar()
    sent_count = (await db.execute(
        select(func.count(Communication.id)).where(Communication.status == CommunicationStatus.SENT)
    )).scalar()
    replied_count = (await db.execute(
        select(func.count(Communication.id)).where(Communication.status == CommunicationStatus.REPLIED)
    )).scalar()
    interested_count = (await db.execute(
        select(func.count(Communication.id)).where(
            Communication.reply_type.in_([ReplyType.INTERESTED, ReplyType.MEETING_REQUEST])
        )
    )).scalar()

    project_count = (await db.execute(select(func.count(Project.id)))).scalar()
    active_projects = (await db.execute(
        select(func.count(Project.id)).where(Project.status == ProjectStatus.ACTIVE)
    )).scalar()

    vacancy_count = (await db.execute(select(func.count(Vacancy.id)))).scalar()
    comp_count = (await db.execute(select(func.count(Competency.id)))).scalar()

    memory = MemoryService(db)
    phase_stats = await memory.get_phase_stats()

    phases = [
        {
            "phase": 1,
            "name": "Анализ индустрии",
            "status": "active" if vacancy_count > 0 else "pending",
            "metrics": {
                "vacancies_parsed": vacancy_count,
                "competencies_found": comp_count,
            },
        },
        {
            "phase": 2,
            "name": "Поиск и скоринг",
            "status": "active" if company_count > 0 else "pending",
            "metrics": {
                "companies_found": company_count,
                "shortlisted": shortlisted_count,
            },
        },
        {
            "phase": 3,
            "name": "Коммуникации",
            "status": "active" if comm_count > 0 else "pending",
            "metrics": {
                "letters_generated": comm_count,
            },
        },
        {
            "phase": 4,
            "name": "Outreach",
            "status": "active" if sent_count > 0 else "pending",
            "metrics": {
                "sent": sent_count,
                "replied": replied_count,
                "interested": interested_count,
                "response_rate": round(replied_count / sent_count, 2) if sent_count else 0,
            },
        },
        {
            "phase": 5,
            "name": "Сбор проектов",
            "status": "active" if project_count > 0 else "pending",
            "metrics": {
                "total_projects": project_count,
                "active_projects": active_projects,
            },
        },
    ]

    kpis = {
        "KPI-1": {"name": "Пул партнёров 100+", "current": company_count, "target": 100, "done": company_count >= 100},
        "KPI-2": {
            "name": "Отклик > 15%",
            "current": round(replied_count / sent_count * 100, 1) if sent_count else 0,
            "target": 15,
            "done": (replied_count / sent_count * 100 >= 15) if sent_count else False,
        },
        "KPI-3": {"name": "Соглашений 10+", "current": partner_count, "target": 10, "done": partner_count >= 10},
        "KPI-4": {"name": "Каталог 20+ проектов", "current": project_count, "target": 20, "done": project_count >= 20},
    }

    return {"phases": phases, "kpis": kpis, "phase_stats": phase_stats}
