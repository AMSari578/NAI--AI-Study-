import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AI_PROVIDER"] = "local"
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_complete_local_study_flow():
    auth = client.post("/auth/register", json={"name":"Mohammed","email":"m@example.com","password":"strong-pass-123"})
    assert auth.status_code == 201, auth.text
    headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}
    subject = client.post("/subjects", headers=headers, json={"name":"Anatomy","description":"Human structure"}).json()
    topic = client.post(f"/subjects/{subject['id']}/topics", headers=headers, json={"title":"Cardiovascular System","description":"Heart and vessels"}).json()
    material = client.post(f"/topics/{topic['id']}/materials/text", headers=headers, json={"title":"Lecture notes","content":"The left ventricle pumps oxygenated blood through the aorta."})
    assert material.status_code == 201
    chat = client.post("/ai/chat", headers=headers, json={"topic_id":topic["id"],"message":"Explain this lecture simply"})
    assert chat.status_code == 200 and "material" in chat.json()["message"]["message"].lower()
    cards = client.post("/ai/flashcards", headers=headers, json={"topic_id":topic["id"],"count":5})
    assert cards.status_code == 200 and len(cards.json()) == 5
    quiz = client.post("/ai/quiz", headers=headers, json={"topic_id":topic["id"],"count":5,"quiz_type":"mcq"})
    assert quiz.status_code == 200 and len(quiz.json()["questions"]) == 5
    assert "correct_answer" not in quiz.json()["questions"][0]
    bank = client.get("/question-bank", headers={**headers, "Origin": "http://localhost:3000"})
    assert bank.status_code == 200 and len(bank.json()) == 10
    assert bank.headers["access-control-allow-origin"] == "http://localhost:3000"
    due = client.get("/review/due-flashcards", headers={**headers, "Origin": "http://localhost:3000"})
    assert due.status_code == 200 and len(due.json()) == 5
    assert due.headers["access-control-allow-origin"] == "http://localhost:3000"
    task = client.post("/tasks", headers=headers, json={"title":"Review Cardiovascular System","topic_id":topic["id"]})
    assert task.status_code == 201
    dashboard = client.get("/dashboard", headers=headers)
    assert dashboard.status_code == 200 and dashboard.json()["subjects"][0]["name"] == "Anatomy"

def test_user_cannot_access_another_users_subject():
    other = client.post("/auth/register", json={"name":"Other User","email":"other@example.com","password":"strong-pass-123"}).json()
    headers = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.get("/subjects/1", headers=headers).status_code == 404


def test_teach_actions_and_mistake_review_flow():
    auth = client.post("/auth/register", json={"name":"Study User","email":"study@example.com","password":"strong-pass-123"}).json()
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    subject = client.post("/subjects", headers=headers, json={"name":"Biology"}).json()
    topic = client.post(f"/subjects/{subject['id']}/topics", headers=headers, json={"title":"Cells"}).json()
    client.post(f"/topics/{topic['id']}/materials/text", headers=headers, json={"title":"Cells notes","content":"Mitochondria release usable energy from nutrients for the cell."})

    lesson = client.post("/ai/chat", headers=headers, json={"topic_id":topic["id"],"message":"Teach me","mode":"teach"})
    assert lesson.status_code == 200
    assert any(action["id"] == "dont_understand" for action in lesson.json()["actions"])

    quiz = client.post("/ai/quiz", headers=headers, json={"topic_id":topic["id"],"count":1,"quiz_type":"essay"}).json()
    question = quiz["questions"][0]
    evaluation = client.post("/ai/evaluate-answer", headers=headers, json={"question_id":question["id"],"answer":"I do not know"})
    assert evaluation.status_code == 200
    assert evaluation.json()["educational_feedback"] is True
    assert "suggested_answer" in evaluation.json()

    mistakes = client.get(f"/review/mistakes?topic_id={topic['id']}", headers=headers)
    assert mistakes.status_code == 200
    assert mistakes.json()[0]["question_id"] == question["id"]


def test_reader_review_planner_search_and_mock_exam():
    auth = client.post("/auth/register", json={"name":"Planner User","email":"planner@example.com","password":"strong-pass-123"}).json()
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    subject = client.post("/subjects", headers=headers, json={"name":"Physiology"}).json()
    topic = client.post(f"/subjects/{subject['id']}/topics", headers=headers, json={"title":"Respiration"}).json()
    material = client.post(f"/topics/{topic['id']}/materials/text", headers=headers, json={"title":"Oxygen notes","content":"Alveoli exchange oxygen and carbon dioxide with nearby capillaries."}).json()
    pages = client.get(f"/materials/{material['id']}/pages", headers=headers)
    assert pages.status_code == 200 and pages.json()["pages"][0]["page_number"] == 1
    continuation = client.get("/dashboard", headers=headers).json()["continue_studying"]
    assert continuation["material_id"] == material["id"]
    note_action = client.post("/study/context-action", headers=headers, json={"topic_id":topic["id"],"material_id":material["id"],"page_number":1,"selected_text":"Alveoli exchange gases with capillaries.","action":"add_to_notes"})
    assert note_action.status_code == 200 and note_action.json()["created_id"]
    card_action = client.post("/study/context-action", headers=headers, json={"topic_id":topic["id"],"material_id":material["id"],"selected_text":"Alveoli exchange gases with capillaries.","action":"create_flashcard"})
    assert card_action.status_code == 200 and card_action.json()["created_id"]
    marked = client.post("/review/items", headers=headers, json={"topic_id":topic["id"],"title":"Review gas exchange"})
    assert marked.status_code == 201 and client.get("/review/items",headers=headers).json()[0]["title"] == "Review gas exchange"

    cards = client.post("/ai/flashcards", headers=headers, json={"topic_id":topic["id"],"count":1}).json()
    reviewed = client.post(f"/flashcards/{cards[0]['id']}/review", headers=headers, json={"rating":"good"})
    assert reviewed.status_code == 200 and reviewed.json()["review_count"] == 1

    exam = client.post("/exams", headers=headers, json={"name":"Respiration exam","subject_id":subject["id"],"exam_datetime":"2030-01-10T09:00:00","topic_ids":[topic["id"]]}).json()
    plan = client.post("/study-plans/ai", headers=headers, json={"exam_id":exam["id"],"daily_minutes":30,"available_days":[0,1,2,3,4,5,6]})
    assert plan.status_code == 201 and plan.json()["items"]
    assert client.get("/calendar", headers=headers).status_code == 200
    found = client.get("/search?q=oxygen", headers=headers)
    assert found.status_code == 200 and any(item["type"] == "material" for item in found.json())

    mock = client.post("/ai/mock-exam", headers=headers, json={"topic_ids":[topic["id"]],"count":5,"question_types":["essay"]})
    assert mock.status_code == 200 and "correct_answer" not in mock.json()["questions"][0]
    submitted = client.post(f"/mock-exams/{mock.json()['id']}/submit", headers=headers, json={"answers":[]})
    assert submitted.status_code == 200 and "results" in submitted.json()

    stranger = client.post("/auth/register", json={"name":"Stranger","email":"stranger@example.com","password":"strong-pass-123"}).json()
    stranger_headers = {"Authorization": f"Bearer {stranger['access_token']}"}
    assert client.get(f"/materials/{material['id']}/pages",headers=stranger_headers).status_code == 404
    assert client.post("/study/context-action",headers=stranger_headers,json={"topic_id":topic["id"],"selected_text":"private","action":"summarize"}).status_code == 404
