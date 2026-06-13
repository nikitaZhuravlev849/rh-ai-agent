from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.project import Project, ProjectRole, ProjectStatus
from app.models.company import Company
from app.models.competency import Competency
from app.schemas.project import ProjectOut, ProjectCreate, ProjectGenerateRequest, ProjectCatalogItem, ProjectRoleOut
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.models.memory import EventType

router = APIRouter(prefix="/projects", tags=["Фаза 5: Проекты и ТЗ"])
llm = LLMService()


def _project_query():
    return select(Project).options(
        selectinload(Project.roles),
        selectinload(Project.competencies),
    )


@router.post("/generate", response_model=ProjectOut)
async def generate_project(data: ProjectGenerateRequest, db: AsyncSession = Depends(get_db)):
    """Сгенерировать ТЗ проекта на основе соглашения с партнёром."""
    company_result = await db.execute(select(Company).where(Company.id == data.company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    competencies = []
    if data.competency_ids:
        comp_result = await db.execute(
            select(Competency).where(Competency.id.in_(data.competency_ids))
        )
        competencies = comp_result.scalars().all()

    company_dict = {
        "name": company.name,
        "industry": company.industry,
        "tech_stack": company.tech_stack or [],
    }
    comp_names = [c.name for c in competencies]

    spec = await llm.generate_project_spec(
        company=company_dict,
        agreement_details=data.agreement_details,
        competencies=comp_names,
    )

    project = Project(
        company_id=data.company_id,
        title=spec.get("title", f"Проект {company.name}"),
        description=spec.get("description"),
        technical_spec=spec.get("technical_spec"),
        goals=spec.get("goals"),
        expected_results=spec.get("expected_results"),
        difficulty=spec.get("difficulty", "intermediate"),
        duration_weeks=spec.get("duration_weeks", 12),
        max_students=spec.get("max_students", 4),
        modules=spec.get("modules", []),
        evaluation_criteria=spec.get("evaluation_criteria", []),
        status=ProjectStatus.DRAFT,
        agreement_date=datetime.utcnow(),
    )
    db.add(project)
    await db.flush()

    for role_data in spec.get("roles", []):
        role = ProjectRole(
            project_id=project.id,
            role_name=role_data.get("role_name", "Разработчик"),
            required_skills=role_data.get("required_skills", []),
            slots=role_data.get("slots", 1),
            effort_hours=role_data.get("effort_hours"),
        )
        db.add(role)

    for comp in competencies:
        project.competencies.append(comp)

    await db.commit()

    # Re-fetch with relationships loaded
    result = await db.execute(_project_query().where(Project.id == project.id))
    project = result.scalar_one()

    memory = MemoryService(db)
    await memory.log_event(
        event_type=EventType.PROJECT_CREATED,
        entity_type="project",
        entity_id=project.id,
        description=f"Project '{project.title}' created for {company.name}",
        phase=5,
        is_successful=True,
    )
    return project


@router.get("/catalog", response_model=List[ProjectCatalogItem])
async def get_project_catalog(
    status: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Project, Company.name.label("company_name")).join(Company).options(
        selectinload(Project.competencies)
    )
    if status:
        q = q.where(Project.status == status)
    if difficulty:
        q = q.where(Project.difficulty == difficulty)

    result = await db.execute(q)
    items = []
    for row in result:
        project, company_name = row
        roles_result = await db.execute(
            select(func.count(ProjectRole.id)).where(ProjectRole.project_id == project.id)
        )
        roles_count = roles_result.scalar()
        comp_names = [c.name for c in project.competencies] if project.competencies else []
        items.append(ProjectCatalogItem(
            id=project.id,
            title=project.title,
            company_name=company_name,
            difficulty=project.difficulty,
            duration_weeks=project.duration_weeks,
            max_students=project.max_students,
            enrolled_students=project.enrolled_students,
            status=project.status,
            roles_count=roles_count or 0,
            competencies=comp_names,
        ))
    return items


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(_project_query().where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}/status")
async def update_project_status(
    project_id: int,
    status: ProjectStatus,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.status = status
    if status == ProjectStatus.ACTIVE:
        project.start_date = datetime.utcnow()
    await db.commit()
    return {"project_id": project_id, "status": status}


@router.get("/{project_id}/roles", response_model=List[ProjectRoleOut])
async def get_project_roles(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProjectRole).where(ProjectRole.project_id == project_id))
    return result.scalars().all()
