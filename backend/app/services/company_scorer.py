from typing import List, Dict, Any, Optional
from app.services.nlp_service import NLPService

nlp = NLPService()

SIZE_SCORES = {
    "крупная": 1.0,
    "large": 1.0,
    "средняя": 0.8,
    "medium": 0.8,
    "малая": 0.6,
    "small": 0.6,
    "микро": 0.4,
    "micro": 0.4,
}

EDUCATION_KEYWORDS = [
    "университет", "вуз", "образовани", "студент", "практик", "стажир",
    "university", "education", "student", "internship", "trainee",
]


class CompanyScorer:
    def __init__(self, target_competencies: Optional[List[str]] = None):
        self.target_competencies = [c.lower() for c in (target_competencies or [])]

    def score(self, company: Dict[str, Any]) -> Dict[str, float]:
        tech_score = self._tech_stack_score(company)
        comp_score = self._competency_match_score(company)
        size_score = self._size_score(company)
        rep_score = self._reputation_score(company)
        edu_score = self._education_experience_score(company)

        weights = {
            "tech_stack_score": 0.30,
            "competency_match_score": 0.35,
            "size_score": 0.10,
            "reputation_score": 0.15,
            "education_experience_score": 0.10,
        }
        breakdown = {
            "tech_stack_score": round(tech_score * 100, 1),
            "competency_match_score": round(comp_score * 100, 1),
            "size_score": round(size_score * 100, 1),
            "reputation_score": round(rep_score * 100, 1),
            "education_experience_score": round(edu_score * 100, 1),
        }
        total = sum(
            breakdown[k] * weights[k]
            for k in weights
        )
        breakdown["total"] = round(total, 1)
        return breakdown

    def _tech_stack_score(self, company: Dict[str, Any]) -> float:
        tech_stack = company.get("tech_stack") or []
        description = company.get("description") or ""
        all_techs = set(t.lower() for t in tech_stack)
        all_techs |= set(t.lower() for t in nlp.extract_tech_stack_from_description(description))

        if not self.target_competencies:
            return min(len(all_techs) / 10, 1.0)

        matched = sum(1 for t in self.target_competencies if any(t in tech for tech in all_techs))
        return min(matched / max(len(self.target_competencies), 1), 1.0)

    def _competency_match_score(self, company: Dict[str, Any]) -> float:
        if not self.target_competencies:
            return 0.5

        description = (company.get("description") or "").lower()
        matched = sum(1 for c in self.target_competencies if c in description)
        return min(matched / max(len(self.target_competencies), 1), 1.0)

    def _size_score(self, company: Dict[str, Any]) -> float:
        size = (company.get("size") or "").lower()
        for key, val in SIZE_SCORES.items():
            if key in size:
                return val
        return 0.5

    def _reputation_score(self, company: Dict[str, Any]) -> float:
        score = 0.5
        if company.get("website"):
            score += 0.1
        if company.get("linkedin_url"):
            score += 0.1
        if company.get("hh_url"):
            score += 0.1
        description = company.get("description") or ""
        if len(description) > 200:
            score += 0.1
        return min(score, 1.0)

    def _education_experience_score(self, company: Dict[str, Any]) -> float:
        text = " ".join([
            company.get("description") or "",
            company.get("name") or "",
        ]).lower()
        matches = sum(1 for kw in EDUCATION_KEYWORDS if kw in text)
        return min(matches / 3, 1.0)

    def rank_companies(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        scored = []
        for company in companies:
            breakdown = self.score(company)
            company["score"] = breakdown["total"]
            company["score_breakdown"] = breakdown
            scored.append(company)
        return sorted(scored, key=lambda c: c["score"], reverse=True)
