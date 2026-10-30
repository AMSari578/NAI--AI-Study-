from pathlib import Path
import re
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
    conversation = db.query(m.ChatConversation).filter(m.ChatConversation.topic_id == topic_id, m.ChatConversation.deleted_at.is_(None)).order_by(m.ChatConversation.id.desc()).first()
    return {"conversation_id": conversation.id if conversation else None, "messages": conversation.messages if conversation else []}


@router.delete("/conversations/{conversation_id}/messages", status_code=204)
def clear_conversation(conversation_id: int, db=Depends(get_db), user=Depends(current_user)):
    conversation = conversation_for(db, conversation_id, user.id)
    for message in conversation.messages:
        if message.image_path:
            Path(message.image_path).unlink(missing_ok=True)
    db.query(m.ChatMessage).filter_by(conversation_id=conversation.id).delete()
    db.commit()


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int, db=Depends(get_db), user=Depends(current_user)):
    conversation = conversation_for(db, conversation_id, user.id)
    conversation.deleted_at = m.now()
    db.commit()


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
    reply = provider().text(tutor_prompt(body.message, body.mode, body.action, body.language), context, history)
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
    return db.query(m.Summary).filter(m.Summary.topic_id == topic_id, m.Summary.deleted_at.is_(None)).order_by(m.Summary.id.desc()).all()


@router.delete("/summaries/{summary_id}", status_code=204)
def delete_summary(summary_id: int, db=Depends(get_db), user=Depends(current_user)):
    summary = db.query(m.Summary).filter_by(id=summary_id).first()
    if not summary:
        raise HTTPException(404, "Summary not found")
    topic_for(db, summary.topic_id, user.id)
    summary.deleted_at = m.now()
    db.commit()


ARABIC_ORDINALS = ["أولًا", "ثانيًا", "ثالثًا", "رابعًا", "خامسًا", "سادسًا", "سابعًا", "ثامنًا", "تاسعًا", "عاشرًا"]
ARABIC_LETTERS = ["أ", "ب", "ج", "د", "هـ", "و", "ز", "ح", "ط", "ي"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"]


def _clean(value) -> str:
    """Flatten an AI field to one Markdown-safe line."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _section_label(index: int, arabic: bool) -> str:
    if arabic:
        return ARABIC_ORDINALS[index] if index < len(ARABIC_ORDINALS) else f"{index + 1}."
    return f"{ROMAN[index]}." if index < len(ROMAN) else f"{index + 1}."


def _subsection_label(index: int, arabic: bool) -> str:
    if arabic:
        return f"{ARABIC_LETTERS[index]}." if index < len(ARABIC_LETTERS) else f"{index + 1}."
    return f"{chr(65 + index)}." if index < 26 else f"{index + 1}."


def _points_markdown(points) -> list[str]:
    lines = []
    for number, point in enumerate(points or [], start=1):
        if isinstance(point, dict):
            term, explanation = _clean(point.get("term")), _clean(point.get("explanation"))
        else:
            term, explanation = "", _clean(point)
        if term and explanation:
            lines.append(f"{number}. **{term.strip('*')}** — {explanation}")
        elif term or explanation:
            lines.append(f"{number}. {term or explanation}")
    return lines


def summary_markdown(data: dict, arabic: bool) -> str:
    """Render the structured summary as Markdown in the layout of the student summary template."""
    blocks = [f"# {_clean(data.get('title')) or ('ملخص الدرس' if arabic else 'Lesson summary')}"]
    if _clean(data.get("subtitle")):
        blocks.append(f"> {_clean(data.get('subtitle'))}")
    if _clean(data.get("introduction")):
        blocks.append(_clean(data.get("introduction")))
    sections = [section for section in data.get("sections") or [] if isinstance(section, dict) and _clean(section.get("heading"))]
    for index, section in enumerate(sections):
        emoji = _clean(section.get("emoji"))
        blocks.append(f"## {_section_label(index, arabic)} {emoji + ' ' if emoji else ''}{_clean(section.get('heading'))}")
        if _clean(section.get("paragraph")):
            blocks.append(_clean(section.get("paragraph")))
        blocks.extend(_points_markdown(section.get("points")))
        subsections = [sub for sub in section.get("subsections") or [] if isinstance(sub, dict) and _clean(sub.get("heading"))]
        for sub_index, sub in enumerate(subsections):
            blocks.append(f"### {_subsection_label(sub_index, arabic)} {_clean(sub.get('heading'))}")
            if _clean(sub.get("paragraph")):
                blocks.append(_clean(sub.get("paragraph")))
            blocks.extend(_points_markdown(sub.get("points")))
    table = data.get("key_table") if isinstance(data.get("key_table"), dict) else {}
    rows = [row for row in table.get("rows") or [] if isinstance(row, list) and len(row) >= 2]
    if rows:
        columns = [_clean(column) for column in (table.get("columns") or [])[:2]]
        if len(columns) < 2 or not all(columns):
            columns = ["المصطلح", "المعنى"] if arabic else ["Term", "Meaning"]
        cell = lambda value: _clean(value).replace("|", "/")
        blocks.append(f"## 📊 {'جدول المفاهيم الأساسية' if arabic else 'Key Concepts at a Glance'}")
        blocks.append("\n".join([f"| {cell(columns[0])} | {cell(columns[1])} |", "| --- | --- |"] + [f"| {cell(row[0])} | {cell(row[1])} |" for row in rows]))
    remember = [_clean(item) for item in data.get("remember") or [] if _clean(item)]
    if remember:
        blocks.append(f"## ⭐ {'تذكّر للاختبار' if arabic else 'Remember for the Exam'}")
        blocks.extend(f"- {item}" for item in remember)
    if _clean(data.get("conclusion")):
        blocks.append("---")
        blocks.append(f"## 🏁 {'الخلاصة' if arabic else 'Conclusion'}")
        blocks.append(_clean(data.get("conclusion")))
    return "\n\n".join(blocks)


@router.post("/ai/summarize")
def summarize(body: s.GenerateIn, db=Depends(get_db), user=Depends(current_user)):
    topic = topic_for(db, body.topic_id, user.id)
    arabic = body.language == "arabic"
    language = "Arabic" if arabic else "English"
    depth = {
        "simple": "SIMPLE: the central idea and only the highest-value information. 3 to 4 sections, 2 to 4 points each, no subsections, 3 to 5 table rows, 3 to 5 remember items.",
        "medium": "BALANCED: every major part of the file with its core definitions, lists, steps, and comparisons. 4 to 7 sections, 3 to 6 points each, subsections only where the file has clear sub-parts, 5 to 8 table rows, 5 to 7 remember items.",
        "detailed": "COMPREHENSIVE: every concept, definition, list item, step, role, condition, exception, number, and stated example that a student could be tested on. As many sections as the file needs (usually 6 to 12), with subsections for each sub-part, 6 to 12 table rows, 7 to 10 remember items. Do not stop after an overview.",
        "key_points": "KEY POINTS: concise points grouped by concept. 4 to 6 sections, 3 to 5 points each.",
        "exam_review": "EXAM REVIEW: the concepts, comparisons, and processes most likely to be tested, and common mistakes to avoid.",
        "memorize": "MEMORIZE: exactly what the student must memorize, each with a short memory cue.",
    }[body.summary_type]
    if body.material_id:
        selected = material_for(db, body.material_id, user.id)
        if selected.topic_id != topic.id:
            raise HTTPException(400, "Material does not belong to the selected topic")
        readable_materials = [selected] if selected.extracted_text and selected.extracted_text.strip() else []
    else:
        readable_materials = [item for item in topic.materials if item.deleted_at is None and item.extracted_text and item.extracted_text.strip()]
    if not readable_materials:
        raise HTTPException(400, "لا يوجد نص مقروء في الملفات. ارفع ملفًا نصيًا أو PDF قابلًا لاستخراج النص أولًا.")
    full_source = "\n\n".join(str(item.extracted_text).strip() for item in readable_materials)
    # The provider accepts up to 700k characters for summaries, so most files are read in one pass.
    chunk_size = 450000
    contexts = []
    if len(full_source) > chunk_size:
        start = 0
        while start < len(full_source):
            end = min(len(full_source), start + chunk_size)
            if end < len(full_source):
                boundary = max(full_source.rfind("\n", start + chunk_size // 2, end), full_source.rfind(". ", start + chunk_size // 2, end), full_source.rfind("؟", start + chunk_size // 2, end))
                if boundary > start:
                    end = boundary + 1
            contexts.append(full_source[start:end])
            start = end
    else:
        contexts = [full_source]
    part_note = "" if len(contexts) == 1 else "\nThe file is long and you are reading one part of it. Summarize only this part; other parts are summarized separately."
    prompt = f"""Create a {body.summary_type} study summary of the student's FILE, written in {language}.
You are an expert teacher preparing a beautiful study sheet. Read the whole FILE first, then pull out what a student needs to understand and remember for the exam.
{depth}{part_note}

WHAT TO EXTRACT:
- Core ideas, definitions, key terms, lists, steps and processes (in order), types and categories, comparisons, causes and effects, roles, conditions, exceptions, formulas, numbers, dates, and stated examples.
- Skip metadata that does not help studying: page numbers, headers and footers, course codes, author or instructor contact details, copyright lines, and tables of contents.

HOW TO WRITE:
- Explain in simple, clear {language}, as a friendly teacher would. Short sentences. Define every hard term the first time it appears.
- Rephrase and simplify freely, but every fact must come from the FILE. Do not add facts, numbers, or examples that are not in the FILE.
- Keep numbers, dates, names, and formulas exactly as written in the FILE.
- {"عند وجود مصطلح إنجليزي في الملف، اكتب المصطلح العربي ثم الأصل الإنجليزي بين قوسين، مثل: إدارة المخاطر (Risk Management)." if arabic else "Keep original technical terms as written in the FILE."}
- Use **double asterisks** to bold the most important words inside a sentence, sparingly.
- Headings must name the real concept from the FILE (for example "Phases of the Project Life Cycle"), never generic words like "Section 1" or "Details".
- Give each section one fitting emoji that matches its content (🎯 goals, 📌 definitions, 🔄 processes, ⚖️ comparisons, 🧩 types, 👥 roles, ⚠️ risks or mistakes, 🔢 numbers, 💡 ideas, 📚 background).
- Follow the FILE's own logical order.

Return one JSON object with exactly these keys:
{{
  "title": "the real subject of the file, short",
  "subtitle": "one sentence: what this file teaches",
  "introduction": "2 to 4 sentences that give the big picture",
  "sections": [
    {{
      "emoji": "one emoji",
      "heading": "concept name",
      "paragraph": "1 to 3 sentences explaining this part, or an empty string",
      "points": [{{"term": "key term or short label", "explanation": "clear explanation in 1 to 2 sentences"}}],
      "subsections": [{{"heading": "sub-part name", "paragraph": "optional short explanation", "points": [{{"term": "...", "explanation": "..."}}]}}]
    }}
  ],
  "key_table": {{"columns": ["{"المصطلح" if arabic else "Term"}", "{"المعنى" if arabic else "Meaning"}"], "rows": [["term", "short meaning"]]}},
  "remember": ["a short fact the student must remember for the exam"],
  "conclusion": "2 to 3 sentences tying the ideas together"
}}
Use an empty array for subsections when a section has none. Return valid JSON only."""
    parts = []
    for context_part in contexts:
        result = provider().structured(prompt, context_part)
        if isinstance(result, dict) and isinstance(result.get("sections"), list):
            parts.append(result)
    if not parts or not any(part.get("sections") for part in parts):
        raise RuntimeError("تعذر إنشاء ملخص من نص الملف. جرّب مرة أخرى أو ارفع ملفًا أوضح.")
    merged = {**parts[0], "sections": [], "remember": [], "key_table": {"columns": (parts[0].get("key_table") or {}).get("columns"), "rows": []}, "conclusion": parts[-1].get("conclusion", "")}
    seen_terms: set[str] = set()
    for part in parts:
        merged["sections"].extend(part.get("sections") or [])
        merged["remember"].extend(part.get("remember") or [])
        for row in (part.get("key_table") or {}).get("rows") or []:
            if isinstance(row, list) and len(row) >= 2 and _clean(row[0]).lower() not in seen_terms:
                seen_terms.add(_clean(row[0]).lower())
                merged["key_table"]["rows"].append(row)
    merged["remember"] = merged["remember"][:12]
    merged["key_table"]["rows"] = merged["key_table"]["rows"][:16]
    content = summary_markdown(merged, arabic)
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
    language = "Arabic" if body.language == "arabic" else "English"
    prompt = f"""Create exactly {body.count} high-quality study flashcards using only the student material.
Write every question and answer in {language}. Do not mix languages except for necessary original technical terms.
Return a JSON array with question and answer fields. Every question must be natural and end with a question mark.
Mix recall, understanding, why/how, comparison, and application. Cover different concepts without repetition.
Answers must be accurate, concise, supported by the material, and answer the exact question in 1 to 3 simple sentences.
Read the complete material from beginning to end before selecting questions. Distribute the cards across all major sections, including definitions, lists, steps, conditions, comparisons, roles, exceptions, and stated examples.
Never use source labels, point numbers, metadata, or commentary."""
    items = provider().structured(prompt, generation_context(topic, body, db, user))
    cards, seen = [], set()
    for item in items[:body.count]:
        question, answer = str(item.get("question", "")).strip(), str(item.get("answer", "")).strip()
        if not question or not answer or question.lower() in seen:
            continue
        if not question.endswith(("?", "؟")):
            question += "؟" if body.language == "arabic" else "?"
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
    return db.query(m.ConceptMap).filter(m.ConceptMap.topic_id == topic_id, m.ConceptMap.deleted_at.is_(None)).order_by(m.ConceptMap.id.desc()).all()


@router.delete("/concept-maps/{concept_id}", status_code=204)
def delete_concept_map(concept_id: int, db=Depends(get_db), user=Depends(current_user)):
    item = db.query(m.ConceptMap).filter(m.ConceptMap.id == concept_id, m.ConceptMap.deleted_at.is_(None)).first()
    if not item:
        raise HTTPException(404, "Concept map not found")
    topic_for(db, item.topic_id, user.id)
    item.deleted_at = m.now()
    db.commit()


@router.delete("/quizzes/{quiz_id}", status_code=204)
def delete_quiz(quiz_id: int, db=Depends(get_db), user=Depends(current_user)):
    item = db.query(m.Quiz).filter(m.Quiz.id == quiz_id, m.Quiz.deleted_at.is_(None)).first()
    if not item:
        raise HTTPException(404, "Quiz not found")
    topic_for(db, item.topic_id, user.id)
    item.deleted_at = m.now()
    db.commit()


@router.post("/ai/concept-map")
def concept_map(body: s.GenerateIn, db=Depends(get_db), user=Depends(current_user)):
    topic = topic_for(db, body.topic_id, user.id)
    language = "Arabic" if body.language == "arabic" else "English"
    prompt = f"""Create a concept map using only the student material. Return one JSON object with nodes [{{id,label,detail,level}}] and edges [{{source,target}}].
Write every label and detail in {language}. Do not mix languages except for necessary original technical terms.
Node 0 is the lesson title at level 0. Add 6 to 12 unique important concepts at levels 1 to 3. Connect every child to its real parent.
Labels must be short; details explain the relationship in one simple sentence. Every non-root node has exactly one incoming edge."""
    raw = provider().structured(prompt + "\nRead the complete material from beginning to end. Cover every major section and preserve the real relationships between concepts.", generation_context(topic, body, db, user))
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
    language = "Arabic" if body.language == "arabic" else "English"
    format_rule = {
        "mcq": "Provide exactly four short, plausible, unique choices and only one correct answer.",
        "true_false": 'Choices must be exactly ["صح","خطأ"].' if body.language == "arabic" else 'Choices must be exactly ["True","False"].',
        "essay": "Choices must be null and the correct answer must be a concise model answer.",
    }[body.quiz_type]
    items = provider().structured(f"""Create exactly {body.count} varied {body.quiz_type} questions using only the student material.
Write the questions, choices, correct answers, and explanations in {language}. Do not mix languages except for necessary original technical terms.
Return a JSON array with question, choices, correct_answer, and explanation. {format_rule}
Read the complete material from beginning to end before writing the questions.
Distribute questions across the beginning, middle, and end of the file and across every major section.
Include definitions, explicit lists, steps, conditions, exceptions, comparisons, roles, causes, results, and stated examples when present.
Test different important ideas using recall, understanding, comparison, and application. Never repeat patterns or include metadata.""", generation_context(topic, body, db, user))
    quiz_record = m.Quiz(topic_id=topic.id, quiz_type=body.quiz_type)
    db.add(quiz_record)
    db.flush()
    added, seen_questions = 0, set()
    for item in items[:body.count]:
        question = str(item.get("question", "")).strip()
        correct = str(item.get("correct_answer", "")).strip()
        choices = item.get("choices")
        question_key = question.casefold()
        if not question or not correct or question_key in seen_questions:
            continue
        if body.quiz_type == "mcq":
            choices = list(dict.fromkeys(str(choice).strip() for choice in (choices or []) if str(choice).strip()))
            matching = next((choice for choice in choices if choice.casefold() == correct.casefold()), None)
            if matching:
                correct = matching
            elif correct not in choices:
                choices.insert(0, correct)
            if len(choices) != 4:
                continue
        elif body.quiz_type == "true_false":
            choices = ["صح", "خطأ"] if body.language == "arabic" else ["True", "False"]
            truthy = correct.casefold() in {"true", "صح", "صحيح", "yes"}
            correct = choices[0] if truthy else choices[1]
        else:
            choices = None
        db.add(m.QuizQuestion(quiz_id=quiz_record.id, question=question, question_type=body.quiz_type, choices=choices, correct_answer=correct, explanation=str(item.get("explanation", "")).strip()))
        seen_questions.add(question_key)
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
