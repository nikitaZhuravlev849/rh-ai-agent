from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database import get_db
from app.models.company import Company, Contact
from app.models.competency import Competency
from app.schemas.company import CompanyOut, CompanyCreate, CompanyUpdate, ContactCreate, ContactOut, CompanyShortlist, CompanyVerifyRequest
from app.services.company_scorer import CompanyScorer
from app.services.nlp_service import NLPService

router = APIRouter(prefix="/companies", tags=["Фаза 2: Компании и скоринг"])
nlp = NLPService()


def _company_query():
    """Base query with eager-loaded contacts to avoid async lazy-load errors."""
    return select(Company).options(selectinload(Company.contacts))


@router.get("/", response_model=CompanyShortlist)
async def list_companies(
    page: int = 1,
    per_page: int = 20,
    shortlisted_only: bool = False,
    min_score: float = 0,
    industry: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Company).order_by(desc(Company.score))
    if shortlisted_only:
        q = q.where(Company.is_shortlisted == True)
    if min_score > 0:
        q = q.where(Company.score >= min_score)
    if industry:
        q = q.where(Company.industry.ilike(f"%{industry}%"))

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar()

    q = q.options(selectinload(Company.contacts)).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    companies = result.scalars().all()

    return CompanyShortlist(companies=companies, total=total, page=page, per_page=per_page)


@router.get("/top", response_model=List[CompanyOut])
async def get_top_companies(limit: int = Query(10, le=100), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Company).options(selectinload(Company.contacts)).order_by(desc(Company.score)).limit(limit)
    )
    return result.scalars().all()


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Company).options(selectinload(Company.contacts)).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/", response_model=CompanyOut)
async def create_company(data: CompanyCreate, db: AsyncSession = Depends(get_db)):
    comp_result = await db.execute(
        select(Competency).order_by(Competency.industry_demand.desc()).limit(20)
    )
    top_comps = [c.name for c in comp_result.scalars().all()]
    scorer = CompanyScorer(target_competencies=top_comps)

    company_dict = data.model_dump()
    if not company_dict.get("tech_stack"):
        company_dict["tech_stack"] = nlp.extract_tech_stack_from_description(data.description or "")

    score_data = scorer.score(company_dict)
    company = Company(
        **company_dict,
        score=score_data["total"],
        score_breakdown=score_data,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)

    # Re-fetch with contacts loaded
    result = await db.execute(
        select(Company).options(selectinload(Company.contacts)).where(Company.id == company.id)
    )
    return result.scalar_one()


@router.patch("/{company_id}", response_model=CompanyOut)
async def update_company(company_id: int, data: CompanyUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(company, field, value)
    await db.commit()

    result = await db.execute(
        select(Company).options(selectinload(Company.contacts)).where(Company.id == company_id)
    )
    return result.scalar_one()


@router.post("/verify-batch")
async def verify_companies(data: CompanyVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Точка эскалации №2 — человек верифицирует шорт-лист."""
    from app.services.memory_service import MemoryService
    from app.models.memory import EventType
    memory = MemoryService(db)

    result = await db.execute(select(Company).where(Company.id.in_(data.company_ids)))
    companies = result.scalars().all()

    for company in companies:
        if data.action == "approve":
            company.is_verified = True
        elif data.action == "shortlist":
            company.is_shortlisted = True
            company.is_verified = True
        elif data.action == "reject":
            company.is_shortlisted = False

    await db.commit()
    await memory.log_event(
        event_type=EventType.HUMAN_DECISION,
        entity_type="company",
        entity_id=None,
        description=f"Human {data.action}d {len(companies)} companies",
        data={"company_ids": data.company_ids, "action": data.action},
        phase=2,
        is_successful=True,
    )
    return {"updated": len(companies), "action": data.action}


@router.post("/{company_id}/rescore", response_model=CompanyOut)
async def rescore_company(company_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    comp_result = await db.execute(
        select(Competency).order_by(Competency.industry_demand.desc()).limit(20)
    )
    top_comps = [c.name for c in comp_result.scalars().all()]
    scorer = CompanyScorer(target_competencies=top_comps)

    company_dict = {
        "name": company.name,
        "description": company.description,
        "tech_stack": company.tech_stack,
        "size": company.size,
        "website": company.website,
        "linkedin_url": company.linkedin_url,
        "hh_url": company.hh_url,
    }
    score_data = scorer.score(company_dict)
    company.score = score_data["total"]
    company.score_breakdown = score_data
    await db.commit()

    result = await db.execute(
        select(Company).options(selectinload(Company.contacts)).where(Company.id == company_id)
    )
    return result.scalar_one()


@router.post("/{company_id}/contacts", response_model=ContactOut)
async def add_contact(company_id: int, data: ContactCreate, db: AsyncSession = Depends(get_db)):
    contact = Contact(**data.model_dump(), company_id=company_id)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.get("/{company_id}/contacts", response_model=List[ContactOut])
async def get_contacts(company_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.company_id == company_id))
    return result.scalars().all()
