import re
import logging
from typing import List, Dict, Set, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

TECH_KEYWORDS: Dict[str, List[str]] = {
    "Python": ["python", "питон", "пайтон"],
    "JavaScript": ["javascript", "js", "node.js", "nodejs"],
    "TypeScript": ["typescript", "ts"],
    "React": ["react", "react.js", "reactjs"],
    "Vue.js": ["vue", "vue.js", "vuejs"],
    "Java": ["java"],
    "Kotlin": ["kotlin"],
    "Go": ["golang", "go lang", "go-lang"],
    "Rust": ["rust"],
    "C++": ["c++", "cpp", "с++"],
    "C#": ["c#", "csharp", ".net", "dotnet"],
    "SQL": ["sql", "postgresql", "postgres", "mysql", "sqlite", "mssql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Docker": ["docker", "докер"],
    "Kubernetes": ["kubernetes", "k8s", "кубернетес"],
    "CI/CD": ["ci/cd", "github actions", "gitlab ci", "jenkins", "devops"],
    "Machine Learning": ["machine learning", "ml", "машинное обучение"],
    "Deep Learning": ["deep learning", "нейросети", "neural network"],
    "Data Science": ["data science", "data scientist", "анализ данных"],
    "FastAPI": ["fastapi", "fast api"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Spring": ["spring", "spring boot"],
    "Microservices": ["microservices", "микросервис"],
    "REST API": ["rest api", "restful", "api"],
    "Git": ["git", "github", "gitlab", "bitbucket"],
    "Linux": ["linux", "ubuntu", "centos", "debian"],
    "AWS": ["aws", "amazon web services"],
    "GCP": ["gcp", "google cloud"],
    "Azure": ["azure", "microsoft azure"],
    "Agile": ["agile", "scrum", "kanban"],
    "NLP": ["nlp", "natural language processing", "обработка текста"],
    "Computer Vision": ["computer vision", "opencv", "компьютерное зрение"],
    "LLM": ["llm", "gpt", "chatgpt", "langchain", "large language model"],
}

SOFT_SKILL_KEYWORDS: Dict[str, List[str]] = {
    "Командная работа": ["команд", "team", "коллектив", "совместн"],
    "Коммуникация": ["коммуникац", "общени", "переговор", "презентац"],
    "Аналитическое мышление": ["аналитическ", "анализ", "исследован"],
    "Управление проектами": ["управлени", "project manager", "pm", "руководств"],
    "Лидерство": ["лидер", "leadership", "наставник"],
    "Самостоятельность": ["самостоятельн", "автономн", "инициатив"],
    "Критическое мышление": ["критическ", "problem solving", "решение задач"],
    "Обучаемость": ["обучаем", "быстро учится", "развивать"],
}


class NLPService:
    def __init__(self):
        self._spacy_model = None

    def _load_spacy(self):
        if self._spacy_model is None:
            try:
                import spacy
                self._spacy_model = spacy.load("ru_core_news_sm")
            except Exception:
                logger.warning("spaCy ru_core_news_sm not available, using keyword-only extraction")
                self._spacy_model = False
        return self._spacy_model

    def extract_competencies(self, text: str) -> List[Dict[str, str]]:
        text_lower = text.lower()
        found: List[Dict[str, str]] = []

        for skill_name, keywords in TECH_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                found.append({"name": skill_name, "category": "technical", "source": "keyword"})

        for skill_name, keywords in SOFT_SKILL_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                found.append({"name": skill_name, "category": "soft", "source": "keyword"})

        nlp = self._load_spacy()
        if nlp:
            extra = self._extract_with_spacy(text, nlp)
            existing_names = {c["name"] for c in found}
            for item in extra:
                if item["name"] not in existing_names:
                    found.append(item)

        return found

    def _extract_with_spacy(self, text: str, nlp) -> List[Dict[str, str]]:
        doc = nlp(text[:50000])
        result = []
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PRODUCT") and len(ent.text) > 2:
                result.append({"name": ent.text.strip(), "category": "technical", "source": "spacy"})
        return result

    def build_competency_frequency(self, texts: List[str]) -> Dict[str, int]:
        counter: Counter = Counter()
        for text in texts:
            for item in self.extract_competencies(text):
                counter[item["name"]] += 1
        return dict(counter.most_common(200))

    def calculate_gap(
        self,
        industry_freq: Dict[str, int],
        program_competencies: List[str],
    ) -> Dict[str, float]:
        total = max(sum(industry_freq.values()), 1)
        program_set = {c.lower() for c in program_competencies}
        gaps = {}
        for comp, count in industry_freq.items():
            demand = count / total
            covered = 1.0 if comp.lower() in program_set else 0.0
            gaps[comp] = round(demand - covered * demand, 4)
        return gaps

    def extract_tech_stack_from_description(self, description: str) -> List[str]:
        techs = []
        text_lower = description.lower()
        for tech_name, keywords in TECH_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                techs.append(tech_name)
        return techs

    def classify_reply(self, reply_text: str) -> str:
        text_lower = reply_text.lower()
        interest_signals = [
            "интересно", "готов", "расскажите подробнее", "когда можем", "встреч",
            "свяжитесь", "да", "согласен", "рассмотрим", "заинтересован",
            "interested", "meeting", "call", "discuss",
        ]
        rejection_signals = [
            "не интересно", "не готов", "отказ", "нет", "не можем", "не рассматриваем",
            "not interested", "decline", "reject", "unfortunately",
        ]
        question_signals = [
            "вопрос", "уточни", "расскажите", "какой", "что такое", "как",
            "question", "clarify", "what is", "how",
        ]

        if any(s in text_lower for s in interest_signals):
            return "interested"
        if any(s in text_lower for s in rejection_signals):
            return "rejected"
        if any(s in text_lower for s in question_signals):
            return "question"
        return "no_reply"
