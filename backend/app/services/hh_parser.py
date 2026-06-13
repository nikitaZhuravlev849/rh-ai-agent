import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from app.config import settings

logger = logging.getLogger(__name__)

HH_HEADERS = {
    "User-Agent": "RH-AI-Agent/1.0 (educational project; juravlev.johm@gmail.com)",
    "HH-User-Agent": "RH-AI-Agent/1.0 (educational project; juravlev.johm@gmail.com)",
}


class HHParser:
    BASE_URL = settings.HH_API_URL

    async def search_vacancies(
        self,
        text: str,
        area: int = 1,
        per_page: int = 100,
        pages: int = 5,
    ) -> List[Dict[str, Any]]:
        vacancies = []
        async with aiohttp.ClientSession(headers=HH_HEADERS) as session:
            for page in range(pages):
                params = {
                    "text": text,
                    "area": area,
                    "per_page": per_page,
                    "page": page,
                    "only_with_salary": False,
                }
                if settings.HH_API_TOKEN:
                    session.headers.update({"Authorization": f"Bearer {settings.HH_API_TOKEN}"})

                try:
                    async with session.get(f"{self.BASE_URL}/vacancies", params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            items = data.get("items", [])
                            vacancies.extend(items)
                            if page >= data.get("pages", 0) - 1:
                                break
                        else:
                            logger.warning(f"HH API returned {resp.status} on page {page}")
                            break
                except Exception as e:
                    logger.error(f"Error fetching HH vacancies page {page}: {e}")
                    break

                await asyncio.sleep(0.3)

        return vacancies

    async def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict[str, Any]]:
        async with aiohttp.ClientSession(headers=HH_HEADERS) as session:
            if settings.HH_API_TOKEN:
                session.headers.update({"Authorization": f"Bearer {settings.HH_API_TOKEN}"})
            try:
                async with session.get(f"{self.BASE_URL}/vacancies/{vacancy_id}") as resp:
                    if resp.status == 200:
                        return await resp.json()
            except Exception as e:
                logger.error(f"Error fetching vacancy {vacancy_id}: {e}")
        return None

    async def search_employers(
        self,
        text: str,
        area: int = 1,
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        employers = []
        async with aiohttp.ClientSession(headers=HH_HEADERS) as session:
            if settings.HH_API_TOKEN:
                session.headers.update({"Authorization": f"Bearer {settings.HH_API_TOKEN}"})
            params = {"text": text, "area": area, "per_page": per_page}
            try:
                async with session.get(f"{self.BASE_URL}/employers", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        employers = data.get("items", [])
            except Exception as e:
                logger.error(f"Error fetching HH employers: {e}")
        return employers

    async def get_employer_details(self, employer_id: str) -> Optional[Dict[str, Any]]:
        async with aiohttp.ClientSession(headers=HH_HEADERS) as session:
            if settings.HH_API_TOKEN:
                session.headers.update({"Authorization": f"Bearer {settings.HH_API_TOKEN}"})
            try:
                async with session.get(f"{self.BASE_URL}/employers/{employer_id}") as resp:
                    if resp.status == 200:
                        return await resp.json()
            except Exception as e:
                logger.error(f"Error fetching employer {employer_id}: {e}")
        return None

    def normalize_vacancy(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        salary = raw.get("salary") or {}
        return {
            "external_id": str(raw.get("id", "")),
            "title": raw.get("name", ""),
            "company_name": (raw.get("employer") or {}).get("name", ""),
            "description": self._strip_html(raw.get("description", "") or ""),
            "requirements": self._extract_requirements(raw),
            "salary_from": salary.get("from"),
            "salary_to": salary.get("to"),
            "region": (raw.get("area") or {}).get("name", ""),
            "source": "hh",
            "url": raw.get("alternate_url", ""),
            "published_at": raw.get("published_at"),
        }

    def normalize_employer(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "external_id": f"hh_{raw.get('id', '')}",
            "name": raw.get("name", ""),
            "industry": self._get_industry(raw),
            "size": raw.get("size", {}).get("name") if raw.get("size") else None,
            "region": (raw.get("area") or {}).get("name", ""),
            "website": raw.get("site_url", ""),
            "description": self._strip_html(raw.get("description", "") or ""),
            "hh_url": raw.get("alternate_url", ""),
            "source": "hh",
            "raw_data": raw,
        }

    def _strip_html(self, text: str) -> str:
        import re
        return re.sub(r"<[^>]+>", " ", text).strip()

    def _extract_requirements(self, raw: Dict[str, Any]) -> str:
        snippet = raw.get("snippet") or {}
        parts = [
            snippet.get("requirement", ""),
            snippet.get("responsibility", ""),
        ]
        return " ".join(p for p in parts if p)

    def _get_industry(self, raw: Dict[str, Any]) -> str:
        industries = raw.get("industries") or []
        if industries:
            return industries[0].get("name", "")
        return ""


class SuperjobParser:
    BASE_URL = settings.SUPERJOB_API_URL

    async def search_vacancies(self, keyword: str, count: int = 100) -> List[Dict[str, Any]]:
        if not settings.SUPERJOB_API_KEY:
            logger.warning("Superjob API key not set, skipping")
            return []

        headers = {
            "X-Api-App-Id": settings.SUPERJOB_API_KEY,
            "User-Agent": "RH-AI-Agent/1.0",
        }
        vacancies = []
        async with aiohttp.ClientSession(headers=headers) as session:
            params = {"keyword": keyword, "count": count, "page": 0}
            try:
                async with session.get(f"{self.BASE_URL}/vacancies/", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        vacancies = data.get("objects", [])
            except Exception as e:
                logger.error(f"Error fetching Superjob vacancies: {e}")
        return vacancies

    def normalize_vacancy(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "external_id": f"sj_{raw.get('id', '')}",
            "title": raw.get("profession", ""),
            "company_name": (raw.get("client") or {}).get("title", ""),
            "description": raw.get("candidat", ""),
            "requirements": raw.get("candidat", ""),
            "salary_from": raw.get("payment_from"),
            "salary_to": raw.get("payment_to"),
            "region": (raw.get("town") or {}).get("title", ""),
            "source": "superjob",
            "url": raw.get("link", ""),
            "published_at": None,
        }
