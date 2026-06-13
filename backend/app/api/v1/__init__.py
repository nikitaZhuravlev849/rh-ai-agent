from fastapi import APIRouter
from app.api.v1.industry import router as industry_router
from app.api.v1.companies import router as companies_router
from app.api.v1.communications import router as communications_router
from app.api.v1.projects import router as projects_router
from app.api.v1.dashboard import router as dashboard_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(industry_router)
api_router.include_router(companies_router)
api_router.include_router(communications_router)
api_router.include_router(projects_router)
api_router.include_router(dashboard_router)
