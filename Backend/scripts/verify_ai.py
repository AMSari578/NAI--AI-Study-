"""Run a live, isolated smoke test against the configured AI provider."""
import json
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app

MATERIAL = """Photosynthesis is the process plants use to make glucose, a kind of sugar.
It happens mainly inside chloroplasts in leaf cells. Chlorophyll absorbs light energy.
The plant takes carbon dioxide from the air and water from the soil. Using light energy,
it changes carbon dioxide and water into glucose and oxygen. Glucose stores chemical
energy that helps the plant grow, while oxygen is released into the air."""

def require(response, label: str):
    if response.status_code >= 400:
        raise RuntimeError(f"{label} failed ({response.status_code}): {response.text}")
    return response.json()

def main() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    auth = require(client.post("/auth/register", json={"name":"AI Verification","email":"ai-verification@example.com","password":"verification-pass-123"}), "registration")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    subject = require(client.post("/subjects", headers=headers, json={"name":"Science"}), "subject")
    topic = require(client.post(f"/subjects/{subject['id']}/topics", headers=headers, json={"title":"Photosynthesis"}), "topic")
    require(client.post(f"/topics/{topic['id']}/materials/text", headers=headers, json={"title":"Lesson","content":MATERIAL}), "material")
    topic_id = topic["id"]
    explanation = require(client.post("/ai/chat", headers=headers, json={"topic_id":topic_id,"message":"Explain photosynthesis simply and mention chlorophyll."}), "explanation")["message"]["message"]
    summary = require(client.post("/ai/summarize", headers=headers, json={"topic_id":topic_id,"summary_type":"detailed","language":"english"}), "summary")["content"]
    concept_map = require(client.post("/ai/concept-map", headers=headers, json={"topic_id":topic_id}), "concept map")["data"]
    flashcards = require(client.post("/ai/flashcards", headers=headers, json={"topic_id":topic_id,"count":3}), "flashcards")
    quiz = require(client.post("/ai/quiz", headers=headers, json={"topic_id":topic_id,"count":3,"quiz_type":"mcq"}), "quiz")
    checks = {
        "provider": settings.ai_provider,
        "model": settings.gemini_model if settings.ai_provider == "gemini" else settings.ai_provider,
        "explanation": len(explanation) > 100 and "chlorophyll" in explanation.lower(),
        "summary": len(summary) > 200 and "photosynthesis" in summary.lower(),
        "concept_map": len(concept_map.get("nodes", [])) >= 4 and bool(concept_map.get("edges")),
        "flashcards": len(flashcards) == 3 and all(card.get("question") and card.get("answer") for card in flashcards),
        "quiz": len(quiz.get("questions", [])) == 3 and all(len(item.get("choices") or []) == 4 for item in quiz["questions"]),
    }
    print(json.dumps(checks, indent=2, ensure_ascii=False))
    if not all(value is True for key, value in checks.items() if key not in {"provider", "model"}):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
