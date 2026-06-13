import logging

logger = logging.getLogger(__name__)


def run_vacancy_parsing(keywords=None, area=1):
    logger.info("[stub] run_vacancy_parsing — запустите Celery для автопарсинга")


run_vacancy_parsing.delay = lambda *a, **kw: type("R", (), {"id": "stub"})()


def run_company_search(industry: str, region: int = 1):
    logger.info(f"[stub] run_company_search({industry}) — запустите Celery")


run_company_search.delay = lambda *a, **kw: type("R", (), {"id": "stub"})()

INDUSTRY_KEYWORDS = [
    "разработчик", "программист", "data scientist", "аналитик данных",
    "DevOps", "ML engineer", "backend", "frontend", "fullstack",
    "product manager", "UX designer",
]
