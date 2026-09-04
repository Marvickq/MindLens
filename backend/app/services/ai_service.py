import uuid
import httpx
from typing import Dict, Any
from sqlmodel import Session, select

from app.models.case import StudentCase
from app.models.discrepancy import Signal, Discrepancy
from app.config import get_settings

settings = get_settings()

def get_case_insights(case_id: uuid.UUID, db: Session) -> Dict[str, Any]:
    case = db.get(StudentCase, case_id)
    if not case:
        raise ValueError("Case not found")

    signals = db.exec(select(Signal).where(Signal.case_id == case_id)).all()
    discrepancies = db.exec(select(Discrepancy).where(Discrepancy.case_id == case_id)).all()
    
    # Build prompt context
    context = {
        "case_name": case.display_name,
        "signals": [{"title": s.title, "description": s.description} for s in signals],
        "discrepancies": [{"rater_a": d.rater_a, "rater_b": d.rater_b, "divergence": d.divergence} for d in discrepancies]
    }
    
    if settings.grok_api_key:
        return call_grok_api(context)
    else:
        return get_mock_insights(context)

def call_grok_api(context: Dict[str, Any]) -> Dict[str, Any]:
    # Standard OpenAI-compatible API call for Grok
    prompt = f"Analyze the following case data and provide a qualitative synthesis and contextualize the discrepancies: {context}"
    try:
        response = httpx.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.grok_api_key}"},
            json={
                "model": "grok-beta",
                "messages": [
                    {"role": "system", "content": "You are a clinical decision-support assistant. Do not diagnose. Summarize findings based on the provided metrics."},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return {
                "qualitative_synthesis": content,
                "contextualized_discrepancies": "Extracted from Grok response (see synthesis).",
                "note": "Live data from Grok API."
            }
        else:
            return get_mock_insights(context)
    except Exception as e:
        return get_mock_insights(context)

def get_mock_insights(context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "qualitative_synthesis": f"Based on the input for {context.get('case_name')}, common themes indicate challenges in unstructured environments, while retaining focus during direct supervision.",
        "contextualized_discrepancies": "The divergence surfaced is primarily driven by behavioral differences across settings, rather than conflicting rater interpretations.",
        "note": "This is simulated AI output. Add GROK_API_KEY to your .env to enable live Grok analysis."
    }
