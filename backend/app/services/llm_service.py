import logging
from typing import Dict, Any, Optional
import anthropic
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self._client: Optional[anthropic.AsyncAnthropic] = None

    @property
    def client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    async def generate_outreach_letter(
        self,
        company: Dict[str, Any],
        contact: Optional[Dict[str, Any]],
        program_info: str,
        tone: str = "formal",
        target_competencies: Optional[list] = None,
    ) -> Dict[str, str]:
        contact_name = (contact or {}).get("name", "")
        contact_position = (contact or {}).get("position", "")
        tech_stack = ", ".join(company.get("tech_stack") or []) or "не указан"
        competencies = ", ".join(target_competencies or []) or "различные IT-компетенции"

        system = (
            "Ты — специалист по B2B коммуникациям и партнёрству с университетами. "
            "Пишешь письма на русском языке от имени программы ПроКомпетенции (УрФУ). "
            "Цель: пригласить компанию стать партнёром для проектного обучения студентов."
        )

        prompt = f"""Напиши персонализированное письмо компании для приглашения к партнёрству.

Данные компании:
- Название: {company.get('name', '')}
- Отрасль: {company.get('industry', 'IT')}
- Регион: {company.get('region', '')}
- Технологический стек: {tech_stack}
- Описание: {company.get('description', '')[:300]}

Контактное лицо: {contact_name} ({contact_position})

О программе ПроКомпетенции:
{program_info}

Ключевые компетенции, которые могут быть интересны: {competencies}

Требования к письму:
- Тон: {"формальный, деловой" if tone == "formal" else "дружелюбный, неформальный"}
- Длина: 200-350 слов
- Структура: приветствие → ценностное предложение → конкретные выгоды → призыв к действию
- Подчеркни конкретную пользу ДЛЯ КОМПАНИИ (готовые кадры, R&D, PR)
- Не используй шаблонные фразы типа "надеемся на сотрудничество"

Верни JSON с полями:
- subject: тема письма (до 80 символов)
- body: тело письма
- value_proposition: одно предложение — главная ценность для компании"""

        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            import json
            import re
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"subject": "Партнёрство в проектном обучении", "body": text, "value_proposition": ""}
        except Exception as e:
            logger.error(f"LLM letter generation error: {e}")
            return self._fallback_letter(company, contact, tone)

    async def generate_project_spec(
        self,
        company: Dict[str, Any],
        agreement_details: str,
        competencies: list,
    ) -> Dict[str, Any]:
        competencies_str = ", ".join(competencies) if competencies else "IT-разработка"
        prompt = f"""Создай техническое задание для проектного обучения студентов.

Компания-партнёр: {company.get('name', '')}
Отрасль: {company.get('industry', '')}
Технологический стек: {', '.join(company.get('tech_stack') or [])}

Детали соглашения:
{agreement_details}

Целевые компетенции студентов: {competencies_str}

Верни JSON со структурой:
{{
  "title": "название проекта",
  "description": "описание проекта (2-3 абзаца)",
  "goals": "цели проекта (список)",
  "expected_results": "ожидаемые результаты",
  "technical_spec": "техническое задание (детально)",
  "difficulty": "beginner/intermediate/advanced",
  "duration_weeks": число,
  "max_students": число,
  "modules": ["модуль 1", "модуль 2", ...],
  "evaluation_criteria": ["критерий 1", "критерий 2", ...],
  "roles": [
    {{"role_name": "Backend разработчик", "required_skills": ["Python", "FastAPI"], "slots": 2, "effort_hours": 80}},
    {{"role_name": "Frontend разработчик", "required_skills": ["React"], "slots": 1, "effort_hours": 60}}
  ]
}}"""

        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            import json
            import re
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"LLM project spec error: {e}")
        return self._fallback_project_spec(company)

    async def classify_reply(self, reply_text: str) -> str:
        prompt = f"""Классифицируй ответ компании на письмо о партнёрстве.

Ответ: {reply_text[:500]}

Варианты:
- "interested" — компания заинтересована, готова к диалогу
- "meeting_request" — просит встречу/звонок
- "question" — задаёт уточняющие вопросы
- "rejected" — вежливый или прямой отказ
- "no_reply" — автоответ, нечитаемо

Верни ТОЛЬКО одно из слов выше, без объяснений."""

        try:
            response = await self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=20,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.content[0].text.strip().lower()
            valid = {"interested", "meeting_request", "question", "rejected", "no_reply"}
            return result if result in valid else "question"
        except Exception as e:
            logger.error(f"LLM reply classification error: {e}")
            from app.services.nlp_service import NLPService
            return NLPService().classify_reply(reply_text)

    async def generate_followup(
        self,
        original_letter: str,
        company_name: str,
        followup_number: int,
    ) -> Dict[str, str]:
        prompt = f"""Напиши фоллоу-ап письмо (напоминание №{followup_number}).

Компания: {company_name}
Исходное письмо:
{original_letter[:400]}

Требования:
- Короткое (100-150 слов)
- Не давить, но напомнить
- Добавить новую ценность или факт
- Предложить удобный формат ответа

Верни JSON: {{"subject": "...", "body": "..."}}"""

        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            import json, re
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"LLM followup error: {e}")
        return {
            "subject": f"Re: Партнёрство ПроКомпетенции — напоминание",
            "body": f"Добрый день!\n\nХотели бы уточнить, рассматриваете ли вы нашу инициативу.\n\nБудем рады любому ответу.",
        }

    def _fallback_letter(self, company, contact, tone) -> Dict[str, str]:
        name = company.get("name", "компания")
        return {
            "subject": f"Приглашение к партнёрству — программа ПроКомпетенции, УрФУ",
            "body": (
                f"Добрый день{',' + contact.get('name', '') if contact and contact.get('name') else ''}!\n\n"
                f"Меня зовут представитель программы ПроКомпетенции Уральского федерального университета.\n\n"
                f"Мы приглашаем {name} стать партнёром нашей программы проектного обучения. "
                f"Студенты выполняют реальные задачи компаний под руководством наставников, "
                f"что даёт вам доступ к мотивированным кандидатам и PR-активности.\n\n"
                f"Готовы ли вы обсудить детали? Буду рад назначить короткий звонок в удобное время."
            ),
            "value_proposition": "Готовые к работе кадры + реальный R&D без затрат на найм.",
        }

    def _fallback_project_spec(self, company) -> Dict[str, Any]:
        return {
            "title": f"Проект для {company.get('name', 'компании')}",
            "description": "Разработка программного решения для нужд компании-партнёра.",
            "goals": "Создать работающий прототип продукта.",
            "expected_results": "Задокументированный прототип, готовый к демо.",
            "technical_spec": "Разработать согласно требованиям партнёра.",
            "difficulty": "intermediate",
            "duration_weeks": 12,
            "max_students": 4,
            "modules": ["Анализ требований", "Проектирование", "Разработка", "Тестирование"],
            "evaluation_criteria": ["Качество кода", "Соответствие ТЗ", "Презентация"],
            "roles": [
                {"role_name": "Backend разработчик", "required_skills": ["Python"], "slots": 2, "effort_hours": 80},
                {"role_name": "Frontend разработчик", "required_skills": ["React"], "slots": 1, "effort_hours": 60},
                {"role_name": "Тестировщик", "required_skills": ["QA"], "slots": 1, "effort_hours": 40},
            ],
        }
