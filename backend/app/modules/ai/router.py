from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app import models as m
from app.modules.ai import schemas as s
from app.integrations.ai_provider import provider, retrieval_context, topic_context
from app.core.config import BASE_DIR, settings
from app.db.session import get_db
from app.shared.dependencies import conversation_for, material_for, note_for, topic_for
from app.core.security import current_user
from app.modules.study.service import response_actions, tutor_prompt
from app.modules.materials.router import ALLOWED_UPLOADS

router = APIRouter(tags=["AI study tools"])


@router.get("/notes/{note_id}", tags=["notes-ai"])
def get_note(note_id: int, db=Depends(get_db), user=Depends(current_user)):
    note = note_for(db, note_id, user.id)
    return {"id": note.id, "topic_id": note.topic_id, "title": note.title, "content": note.content, "updated_at": note.updated_at}


@router.post("/notes/{note_id}/ai", tags=["notes-ai"])
def note_ai(note_id: int, body: s.NoteAIIn, db=Depends(get_db), user=Depends(current_user)):
    note = note_for(db, note_id, user.id)
    prompts = {
        "summarize": "Summarize these study notes accurately.",
        "organize": "Organize these notes into clear headings and useful bullet points without losing facts.",
        "explain": "Explain these notes simply as a patient tutor.",
        "key_points": "Extract the key points and what the student should memorize.",
        "flashcards": "Create useful question-and-answer flashcards from these notes and return readable Markdown.",
        "quiz": "Create a short practice quiz from these notes without revealing answers until the end.",
    }
    context = f"NOTE: {note.title}\n{note.content}"
    if body.action == "flashcards":
        items = provider().structured("Create 10 flashcards from this note. Return JSON array with question and answer.", context)
        cards = [m.Flashcard(topic_id=note.topic_id, question=str(item.get("question", "")).strip(), answer=str(item.get("answer", "")).strip()) for item in items if item.get("question") and item.get("answer")]
        db.add_all(cards)
        db.commit()
        return {"action": body.action, "content": f"Created {len(cards)} flashcards from this note."}
    if body.action == "quiz":
        items = provider().structured("Create 5 multiple-choice questions from this note. Return JSON array with question, exactly four choices, correct_answer, explanation.", context)
        quiz = m.Quiz(topic_id=note.topic_id, quiz_type="mcq")
        db.add(quiz)
        db.flush()
        added = 0
        for item in items:
            choices = list(dict.fromkeys(str(choice).strip() for choice in item.get("choices", []) if str(choice).strip()))
            correct = str(item.get("correct_answer", "")).strip()
            question = str(item.get("question", "")).strip()
            if correct and correct not in choices:
                choices.insert(0, correct)
            if question and correct and len(choices) == 4:
                db.add(m.QuizQuestion(quiz_id=quiz.id, question=question, question_type="mcq", choices=choices, correct_answer=correct, explanation=str(item.get("explanation", "")).strip()))
                added += 1
        db.commit()
        return {"action": body.action, "content": f"Created a {added}-question quiz from this note."}
    return {"action": body.action, "content": provider().text(prompts[body.action], context)}


def generation_context(topic, body: s.GenerateIn, db, user) -> str:
    if not body.material_id:
        return topic_context(topic)
    material = material_for(db, body.material_id, user.id)
    if material.topic_id != topic.id:
        raise HTTPException(400, "Material does not belong to the selected topic")
    return f"SUBJECT: {topic.subject.name}\nTOPIC: {topic.title}\nSELECTED MATERIAL: {material.file_name}\n{material.extracted_text}"


@router.get("/topics/{topic_id}/chat")
def chat_history(topic_id: int, db=Depends(get_db), user=Depends(current_user)):
    topic_for(db, topic_id, user.id)
    conversation = db.query(m.ChatConversation).filter_by(topic_id=topic_id).order_by(m.ChatConversation.id.desc()).first()
    return {"conversation_id": conversation.id if conversation else None, "messages": conversation.messages if conversation else []}


@router.post("/ai/chat")
def chat(body: s.ChatIn, db=Depends(get_db), user=Depends(current_user)):
    topic = topic_for(db, body.topic_id, user.id)
    conversation = conversation_for(db, body.conversation_id, user.id) if body.conversation_id else m.ChatConversation(topic_id=topic.id)
    if not body.conversation_id:
        db.add(conversation)
        db.flush()
    history = [{"role": item.role, "content": item.message} for item in conversation.messages]
    search_query = " ".join([item["content"] for item in history[-4:] if item["role"] == "user"] + [body.message])
    db.add(m.ChatMessage(conversation_id=conversation.id, role="user", message=body.message))
    context = retrieval_context(topic, search_query)
    if body.material_id:
        material = material_for(db, body.material_id, user.id)
        if material.topic_id != topic.id:
            raise HTTPException(400, "Material does not belong to the selected topic")
        if body.page_number:
            page = db.query(m.MaterialPage).filter_by(material_id=material.id, page_number=body.page_number).first()
            if not page:
                raise HTTPException(404, "Page text is not available")
            context = f"CURRENT PDF PAGE {page.page_number} FROM {material.file_name}:\n{page.content}\n\n{context}"
        elif material.extracted_text:
            context = f"SELECTED MATERIAL {material.file_name}:\n{material.extracted_text[:18000]}\n\n{context}"
    if body.selected_text:
        context = f"STUDENT-SELECTED TEXT (prioritize this):\n{body.selected_text}\n\n{context}"
    reply = provider().text(tutor_prompt(body.message, body.mode, body.action), context, history)
    message = m.ChatMessage(conversation_id=conversation.id, role="assistant", message=reply)
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"conversation_id": conversation.id, "message": message, "actions": response_actions(body.mode)}


@router.post("/ai/chat-image")
async def chat_image(topic_id: int = Form(...), message: str = Form(...), conversation_id: int | None = Form(None), file: UploadFile = File(...), db=Depends(get_db), user=Depends(current_user)):
    topic = topic_for(db, topic_id, user.id)
    if file.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(415, "Chat attachment must be a PNG, JPEG, or WEBP image")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "Image is too large")
    conversation = conversation_for(db, conversation_id, user.id) if conversation_id else m.ChatConversation(topic_id=topic.id)
    if not conversation_id:
        db.add(conversation)
        db.flush()
    folder = BASE_DIR / "uploads" / str(user.id) / str(topic_id) / "chat"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid4().hex}.{ALLOWED_UPLOADS[file.content_type]}"
    path.write_bytes(data)
    db.add(m.ChatMessage(conversation_id=conversation.id, role="user", message=message, image_path=str(path)))
    reply = provider().image(message, retrieval_context(topic, message), data, file.content_type)
    response = m.ChatMessage(conversation_id=conversation.id, role="assistant", message=reply)
    db.add(response)
    db.commit()
    db.refresh(response)
    return {"conversation_id": conversation.id, "message": response}


@router.get("/topics/{topic_id}/summaries")
def summaries(topic_id: int, db=Depends(get_db), user=Depends(current_user)):
    topic_for(db, topic_id, user.id)
    return db.query(m.Summary).filter_by(topic_id=topic_id).order_by(m.Summary.id.desc()).all()


@router.delete("/summaries/{summary_id}", status_code=204)
def delete_summary(summary_id: int, db=Depends(get_db), user=Depends(current_user)):
    summary = db.query(m.Summary).filter_by(id=summary_id).first()
    if not summary:
        raise HTTPException(404, "Summary not found")
    topic_for(db, summary.topic_id, user.id)
    db.delete(summary)
    db.commit()


@router.post("/ai/summarize")
def summarize(body: s.GenerateIn, db=Depends(get_db), user=Depends(current_user)):
    topic = topic_for(db, body.topic_id, user.id)
    language = "Arabic" if body.language == "arabic" else "English"
    headings = "## 🌟 الفكرة الرئيسية، ## 🧠 المفاهيم المهمة، ## 🔑 المصطلحات، ## 🔗 ترابط الأفكار، ## 🎯 تذكّر هذا، ## ✅ مراجعة سريعة" if body.language == "arabic" else "## 🌟 Big Idea, ## 🧠 Key Concepts, ## 🔑 Important Terms, ## 🔗 How Ideas Connect, ## 🎯 Remember This, ## ✅ Quick Review"
    rules = {
        "detailed": "Cover every important concept, definition, fact, relationship, process, exception, and memorization point.",
        "key_points": "Extract concise key points only, grouped by concept.",
        "exam_review": "Create an exam-focused review with likely tested concepts, comparisons, processes, and common mistakes.",
        "memorize": "List exactly what the student should memorize, with short memory cues.",
        "simple": "Include only the main idea and the most important points. Keep it short and easy to review.",
    }[body.summary_type]
    prompt = f"""Create a beautiful, accurate {body.summary_type} study summary using only the student material.
{rules}
Write the entire summary in {language}. Do not mix languages except when an original technical term requires it.
Use these exact Markdown headings: {headings}.
Use short paragraphs and clear emoji bullets instead of decorative symbols.
Explain for a 10-year-old while preserving every important fact. Never add unsupported information."""
    content = provider().text(prompt, generation_context(topic, body, db, user))
    summary = m.Summary(topic_id=topic.id, content=content, summary_type=body.summary_type, language=body.language)
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


@router.get("/topics/{topic_id}/flashcards")
def flashcards(topic_id: int, db=Depends(get_db), user=Depends(current_user)):
    topic_for(db, topic_id, user.id)
    return db.query(m.Flashcard).filter_by(topic_id=topic_id).all()


@router.post("/ai/flashcards")
def generate_cards(body: s.GenerateIn, db=Depends(get_db), user=Depends(current_user)):
    topic = topic_for(db, body.topic_id, user.id)
    prompt = f"""Create exactly {body.count} high-quality study flashcards using only the student material.
Return a JSON array with question and answer fields. Every question must be natural and end with a question mark.
Mix recall, understanding, why/how, comparison, and application. Cover different concepts without repetition.
Answers must be accurate, concise, supported by the material, and answer the exact question in 1 to 3 simple sentences.
Never use source labels, point numbers, metadata, or commentary."""
    items = provider().structured(prompt, generation_context(topic, body, db, user))
    cards, seen = [], set()
    for item in items[:body.count]:
        question, answer = str(item.get("question", "")).strip(), str(item.get("answer", "")).strip()
        if not question or not answer or question.lower() in seen:
            continue
        if not question.endswith("?"):
            question += "?"
        seen.add(question.lower())
        cards.append(m.Flashcard(topic_id=topic.id, question=question, answer=answer))
    if not cards:
        raise RuntimeError("The AI did not create valid flashcards. Try generating them again.")
    db.query(m.Flashcard).filter_by(topic_id=topic.id).delete()
    db.add_all(cards)
    db.commit()
    return cards


@router.get("/topics/{topic_id}/concept-maps")
def concept_maps(topic_id: int, db=Depends(get_db), user=Depends(current_user)):
    topic_for(db, topic_id, user.id)
    return db.query(m.ConceptMap).filter_by(topic_id=topic_id).order_by(m.ConceptMap.id.desc()).all()


@router.post("/ai/concept-map")
def concept_map(body: s.GenerateIn, db=Depends(get_db), user=Depends(current_user)):
    topic = topic_for(db, body.topic_id, user.id)
    prompt = """Create a concept map using only the student material. Return one JSON object with nodes [{id,label,detail,level}] and edges [{source,target}].
Node 0 is the lesson title at level 0. Add 6 to 12 unique important concepts at levels 1 to 3. Connect every child to its real parent.
Labels must be short; details explain the relationship in one simple sentence. Every non-root node has exactly one incoming edge."""
    raw = provider().structured(prompt, generation_context(topic, body, db, user))
    nodes = raw.get("nodes", []) if isinstance(raw, dict) else []
    edges = raw.get("edges", []) if isinstance(raw, dict) else []
    clean_nodes, seen = [], set()
    for index, node in enumerate(nodes[:12]):
        node_id, label = str(node.get("id", index)), str(node.get("label", "")).strip()
        if not label or node_id in seen:
            continue
        seen.add(node_id)
        clean_nodes.append({"id": node_id, "label": label, "detail": str(node.get("detail", "")).strip(), "level": int(node.get("level", 0 if index == 0 else 1))})
    clean_edges = [{"source": str(edge.get("source")), "target": str(edge.get("target"))} for edge in edges if str(edge.get("source")) in seen and str(edge.get("target")) in seen]
    if not clean_nodes:
        raise RuntimeError("The AI did not create a valid concept map. Try again.")
    concept = m.ConceptMap(topic_id=topic.id, data={"nodes": clean_nodes, "edges": clean_edges})
    db.add(concept)
    db.commit()
    db.refresh(concept)
    return concept


@router.post("/ai/quiz")
def quiz(body: s.GenerateIn, db=Depends(get_db), user=Depends(current_user)):
    topic = topic_for(db, body.topic_id, user.id)
    format_rule = {
        "mcq": "Provide exactly four short, plausible, unique choices and only one correct answer.",
        "true_false": 'Choices must be exactly ["True","False"].',
        "essay": "Choices must be null and the correct answer must be a concise model answer.",
    }[body.quiz_type]
    items = provider().structured(f"""Create exactly {body.count} varied {body.quiz_type} questions using only the student material.
Return a JSON array with question, choices, correct_answer, and explanation. {format_rule}
Test different important ideas using recall, understanding, comparison, and application. Never repeat patterns or include metadata.""", generation_context(topic, body, db, user))
    quiz_record = m.Quiz(topic_id=topic.id, quiz_type=body.quiz_type)
    db.add(quiz_record)
    db.flush()
    added = 0
    for item in items[:body.count]:
        question = str(item.get("question", "")).strip()
        correct = str(item.get("correct_answer", "")).strip()
        choices = item.get("choices")
        if not question or not correct:
            continue
        if body.quiz_type == "mcq":
            choices = list(dict.fromkeys(str(choice).strip() for choice in (choices or []) if str(choice).strip()))
            if correct not in choices:
                choices.insert(0, correct)
            if len(choices) != 4:
                continue
        elif body.quiz_type == "true_false":
            choices = ["True", "False"]
        else:
            choices = None
        db.add(m.QuizQuestion(quiz_id=quiz_record.id, question=question, question_type=body.quiz_type, choices=choices, correct_answer=correct, explanation=str(item.get("explanation", "")).strip()))
        added += 1
    if not added:
        raise RuntimeError("The AI did not create valid quiz questions. Try again.")
    db.commit()
    db.refresh(quiz_record)
    return {
        "id": quiz_record.id,
        "topic_id": quiz_record.topic_id,
        "quiz_type": quiz_record.quiz_type,
        "score": quiz_record.score,
        "created_at": quiz_record.created_at,
        "questions": [{"id": item.id, "question": item.question, "question_type": item.question_type, "choices": item.choices} for item in quiz_record.questions],
    }
