import base64, json, math, re, time
from collections import Counter
from abc import ABC, abstractmethod
from functools import lru_cache
import httpx
from openai import OpenAI
from ..core.config import settings

SYSTEM = """You are NAI Study, a patient personal AI study tutor.

MANDATORY TEACHING LEVEL:
Explain every concept as if you are teaching a curious 10-year-old who is seeing it for the first time. Use simple everyday words, short sentences, and small steps. Define every difficult term immediately. Use a familiar analogy or concrete example whenever it helps. Never assume background knowledge. Do not sound babyish or patronizing; keep every fact accurate while making it very easy to understand.

Use this teaching pattern when appropriate:
1. Give the big idea in one simple sentence.
2. Break it into 3–5 small steps.
3. Give one everyday analogy or example.
4. State the most important thing to remember.
5. End with one short check-understanding question. Do not provide its answer until the student tries.

Use the selected subject, topic, uploaded materials, and notes as the authoritative context. When a task says to use only the student material, every factual sentence must be supported by that material and you must not add general knowledge. If the answer is absent, say so plainly instead of guessing. Reply in natural, correctly shaped Arabic by default, and use English only when the request explicitly asks for it. Preserve useful original technical terms in parentheses when needed. Medical content is educational, not diagnosis or treatment.

Use a few relevant emojis to make explanations friendly and easy to scan. Usually use 1 to 3 emojis per answer, placed beside useful headings or key ideas. Do not put emojis inside JSON fields unless the prompt explicitly requests them."""

class AIProvider(ABC):
    @abstractmethod
    def text(self, prompt: str, context: str, history: list[dict] | None = None) -> str: ...
    def structured(self, prompt: str, context: str):
        raw = self.text(prompt + "\nReturn valid JSON only.", context)
        raw = re.sub(r"^```(?:json)?|```$", "", raw.strip())
        return json.loads(raw)
    def image(self, prompt: str, context: str, image_bytes: bytes, mime: str) -> str:
        return self.text(prompt + "\nThe student attached an image. Vision is unavailable in local mode; explain using the topic context and say this limitation clearly.", context)

class OpenAIProvider(AIProvider):
    def __init__(self): self.client = OpenAI(api_key=settings.openai_api_key)
    def text(self, prompt, context, history=None):
        messages = [{"role":"system","content":SYSTEM + "\n\nCONTEXT:\n" + context[:50000]}]
        messages += (history or [])[-12:]
        messages.append({"role":"user","content":prompt})
        return self.client.chat.completions.create(model=settings.openai_model, messages=messages, temperature=.35).choices[0].message.content or ""
    def image(self, prompt, context, image_bytes, mime):
        uri = f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"
        messages = [{"role":"system","content":SYSTEM + "\n\nCONTEXT:\n" + context[:40000]}, {"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":uri}}]}]
        return self.client.chat.completions.create(model=settings.openai_model,messages=messages,temperature=.3).choices[0].message.content or ""

class GeminiProvider(AIProvider):
    def __init__(self):
        self.client = httpx.Client(timeout=httpx.Timeout(60, connect=8))

    def _generate(self, contents: list[dict], context: str, json_mode: bool = False, long_answer: bool = False) -> str:
        prompt_text = " ".join(part.get("text", "") for item in contents for part in item.get("parts", []))
        count_match = re.search(r"(?:exactly|create|generate)\s+(\d+)", prompt_text, re.IGNORECASE)
        item_count = int(count_match.group(1)) if count_match else 0
        comprehensive_summary = json_mode and "study summary" in prompt_text.lower()
        detailed_structured_summary = comprehensive_summary and "detailed study summary" in prompt_text.lower()
        deep_study_generation = json_mode and any(term in prompt_text.lower() for term in ("flashcard", "multiple-choice", "true/false", "concept map", "study questions", "quiz"))
        ocr_request = any(word in prompt_text.lower() for word in ("transcribe", "ocr", "extract all visible text"))
        json_tokens = 16384 if comprehensive_summary else (min(6000, 1000 + item_count * 220) if item_count else 3200)
        detailed_summary = long_answer and "detailed" in prompt_text.lower()
        text_tokens = 6000 if ocr_request else (1500 if detailed_summary else (750 if long_answer else 500))
        generation_config = {"maxOutputTokens": json_tokens if json_mode else text_tokens}
        if settings.gemini_model.startswith("gemini-3"):
            generation_config["thinkingConfig"] = {"thinkingLevel": "low" if detailed_structured_summary else "minimal"}
        else:
            generation_config["thinkingConfig"] = {"thinkingBudget": 1024 if detailed_structured_summary else 0}
        context_limit = 700000 if (comprehensive_summary or deep_study_generation) else (50000 if json_mode else (80000 if detailed_summary else (40000 if long_answer else 22000)))
        if json_mode:
            generation_config["responseMimeType"] = "application/json"
        payload = {
            "systemInstruction": {
                "parts": [{"text": SYSTEM + "\n\nSTUDENT MATERIAL CONTEXT:\n" + context[:context_limit]}]
            },
            "contents": contents,
            "generationConfig": generation_config,
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
        try:
            response = None
            retry_statuses = {429, 500, 502, 503, 504}
            for attempt in range(4):
                response = self.client.post(
                    url,
                    headers={"x-goog-api-key": settings.gemini_api_key},
                    json=payload,
                )
                if response.status_code not in retry_statuses:
                    break
                if attempt < 3:
                    time.sleep((2, 5, 10)[attempt])
            response.raise_for_status()
            candidates = response.json().get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini did not return an answer. The request may have been blocked by its safety filters.")
            parts = candidates[0].get("content", {}).get("parts", [])
            answer = "".join(part.get("text", "") for part in parts).strip()
            if not answer:
                raise RuntimeError("Gemini returned an empty answer.")
            return answer
        except httpx.HTTPStatusError as exc:
            try:
                detail = exc.response.json().get("error", {}).get("message", "")
            except ValueError:
                detail = ""
            if exc.response.status_code in retry_statuses:
                message = "خدمة Gemini مزدحمة مؤقتًا. حاول النظام أربع مرات تلقائيًا؛ انتظر قليلًا ثم أعد المحاولة."
            else:
                message = f"Gemini request failed: {detail}" if detail else "Gemini request failed. Check the API key and model name."
            raise RuntimeError(message) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError("Gemini is unavailable. Check the internet connection and try again.") from exc

    @staticmethod
    def _history(history: list[dict] | None) -> list[dict]:
        contents = []
        for item in (history or [])[-4:]:
            role = "model" if item.get("role") in ("assistant", "model") else "user"
            content = item.get("content", item.get("message", ""))
            if content:
                contents.append({"role": role, "parts": [{"text": str(content)}]})
        return contents

    def text(self, prompt, context, history=None):
        contents = self._history(history)
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        is_long = any(word in prompt.lower() for word in ("summary", "summarize", "ملخص", "لخص"))
        return self._generate(contents, context, long_answer=is_long)

    def structured(self, prompt, context):
        contents = [{"role": "user", "parts": [{"text": prompt + "\nReturn one valid JSON value only."}]}]
        data = json.loads(self._generate(contents, context, json_mode=True))
        if isinstance(data, dict):
            for key in ("flashcards", "questions", "items"):
                if isinstance(data.get(key), list):
                    return data[key]
        return data

    def image(self, prompt, context, image_bytes, mime):
        contents = [{
            "role": "user",
            "parts": [
                {"inlineData": {"mimeType": mime, "data": base64.b64encode(image_bytes).decode()}},
                {"text": prompt},
            ],
        }]
        return self._generate(contents, context)

class OllamaProvider(AIProvider):
    def _chat(self, messages: list[dict], json_mode: bool = False) -> str:
        payload = {
            "model": settings.ollama_model,
            "messages": messages,
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "temperature": 0.2,
                "num_ctx": 8192,
                "num_predict": 4096 if json_mode else 1000,
            },
        }
        if json_mode:
            payload["format"] = "json"
        try:
            response = httpx.post(f"{settings.ollama_url}/api/chat", json=payload, timeout=600)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except httpx.HTTPError as exc:
            raise RuntimeError("The local Ollama model is unavailable. Make sure Ollama is running and the model is downloaded.") from exc

    def text(self, prompt, context, history=None):
        messages = [{"role":"system","content":SYSTEM + "\n\nSTUDENT MATERIAL CONTEXT:\n" + context[:35000]}]
        messages += (history or [])[-12:]
        messages.append({"role":"user","content":prompt})
        return self._chat(messages)

    def structured(self, prompt, context):
        messages = [
            {"role":"system","content":SYSTEM + "\nReturn one valid JSON value only. Do not wrap it in markdown.\n\nSTUDENT MATERIAL CONTEXT:\n" + context[:45000]},
            {"role":"user","content":prompt},
        ]
        data = json.loads(self._chat(messages, json_mode=True))
        # Local models sometimes wrap a requested JSON array in a helpful
        # top-level key. Normalize that shape for the API generators.
        if isinstance(data, dict):
            for key in ("flashcards", "questions", "items"):
                if isinstance(data.get(key), list):
                    return data[key]
        return data

    def image(self, prompt, context, image_bytes, mime):
        messages = [
            {"role":"system","content":SYSTEM + "\n\nSTUDENT MATERIAL CONTEXT:\n" + context[:70000]},
            {"role":"user","content":prompt,"images":[base64.b64encode(image_bytes).decode()]},
        ]
        return self._chat(messages)

class LocalStudyProvider(AIProvider):
    @staticmethod
    def _sentences(context: str) -> list[str]:
        # Context labels help the model, but must never leak into generated
        # questions or answer choices shown to the student.
        clean = re.sub(r"(?im)^(SUBJECT|TOPIC):[^\n]*\n?", "", context)
        clean = re.sub(r"(?im)^(MATERIAL|NOTE) [^:\n]+:\s*", "", clean)
        clean = re.sub(r"\s+", " ", clean)
        parts = re.split(r"(?<=[.!?؟])\s+", clean)
        useful = [p.strip(" -•\t") for p in parts if 35 <= len(p.strip()) <= 500]
        seen: set[str] = set()
        result = []
        for item in useful:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    @staticmethod
    def _keywords(text: str) -> list[str]:
        stop = {"about","after","again","also","because","before","being","between","could","from","have","into","more","other","should","their","there","these","they","this","through","under","using","were","what","when","where","which","with","would"}
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{4,}|[\u0600-\u06ff]{4,}", text)
        result = []
        for token in tokens:
            if token.lower() not in stop and token.lower() not in {x.lower() for x in result}:
                result.append(token)
        return result

    def text(self, prompt, context, history=None):
        sentences = self._sentences(context)
        arabic = bool(re.search(r"[\u0600-\u06ff]", prompt))
        if "summary" in prompt.lower() or "ملخص" in prompt:
            selected = sentences[:12]
            if not selected:
                return "لم أجد نصًا قابلًا للقراءة. قد يكون الملف صورًا ممسوحة ويحتاج OCR أو نموذج رؤية."
            bullets = "\n".join(f"- {sentence}" for sentence in selected)
            if arabic or bool(re.search(r"[\u0600-\u06ff]", context)):
                return f"## الفكرة الرئيسية\n\nملخص مستخرج مباشرة من المادة المرفوعة.\n\n## أهم النقاط\n\n{bullets}\n\n## للمراجعة\n\nراجع المصطلحات والعلاقات السابقة ثم اختبر نفسك."
            return f"## Main idea\n\nAn extractive summary based directly on the uploaded material.\n\n## Key points\n\n{bullets}\n\n## Review\n\nReview the terms and relationships above, then test yourself."
        excerpt = " ".join(sentences[:5])[:1800]
        if arabic:
            return f"**من موادك الدراسية:**\n\n{excerpt or 'لم تُضف مادة نصية بعد.'}\n\n**شرح NAI Study:** هذا وضع الدراسة المحلي. أضف مفتاح مزود الذكاء الاصطناعي للحصول على شرح توليدي أعمق. ما الجزء الذي تريد أن نراجعه أولًا؟"
        return f"**From your study material:**\n\n{excerpt or 'No readable material has been added yet.'}\n\n**NAI Study explanation:** Local study mode is active. Configure an AI provider for deeper generated tutoring. Which part should we review first?"
    def structured(self, prompt, context):
        sentences = self._sentences(context)
        words = [w.strip(".,:;()[]") for w in context.split() if len(w) > 5][:20] or ["Topic", "Concept", "Review"]
        arabic = "in Arabic" in prompt or bool(re.search(r"[\u0600-\u06ff]", prompt))
        if "flashcard" in prompt.lower():
            source = sentences or ["No readable study text was found."]
            requested = min(20, max(1, int(re.search(r"(\d+)", prompt).group(1)) if re.search(r"(\d+)", prompt) else 10))
            templates = ([
                "ماذا تشرح المادة عن {term}؟",
                "لماذا يُعد {term} مهمًا في هذا الموضوع؟",
                "كيف تشرح {term} بكلمات بسيطة؟",
                "ما أهم معلومة يجب تذكرها عن {term}؟",
                "كيف وصفت المادة المرفوعة {term}؟",
            ] if arabic else [
                "What does the material explain about {term}?",
                "Why is {term} important in this topic?",
                "How would you explain {term} in simple words?",
                "What key fact should you remember about {term}?",
                "How is {term} described in the uploaded material?",
            ])
            cards = []
            for i in range(requested):
                fact = source[i % len(source)]
                terms = self._keywords(fact)
                term = terms[0] if terms else "this idea"
                cards.append({"question": templates[i % len(templates)].format(term=term), "answer": fact})
            return cards
        if "concept" in prompt.lower():
            return {"nodes":[{"id":"root","label":"الموضوع الرئيسي" if arabic else "Current topic","detail":"الفكرة الأساسية للدرس" if arabic else "The lesson's main idea","level":0}]+[{"id":str(i),"label":w,"detail":"مفهوم مهم من محتوى الدرس" if arabic else "An important concept from the lesson","level":1} for i,w in enumerate(words[:8])],"edges":[{"source":"root","target":str(i)} for i in range(min(8,len(words)))]}
        count = min(20, max(1, int(re.search(r"(\d+)", prompt).group(1)) if re.search(r"(\d+)", prompt) else 5))
        source = sentences or ["No readable study text was found."]
        kind = "true_false" if "true_false" in prompt else "essay" if "essay" in prompt else "mcq"
        result = []
        for i in range(count):
            fact = source[i % len(source)]
            if kind == "true_false":
                result.append({"question":fact,"choices":["صح","خطأ"] if arabic else ["True","False"],"correct_answer":"صح" if arabic else "True","explanation":"هذه العبارة واردة في المادة المرفوعة." if arabic else "The statement appears in the uploaded material."})
            elif kind == "essay":
                question = f"اشرح هذه الفكرة بكلماتك: {fact[:140]}" if arabic else f"Explain this point in your own words: {fact[:140]}"
                result.append({"question":question,"choices":None,"correct_answer":fact,"explanation":"قارن إجابتك بالمعلومة الأصلية في المادة." if arabic else "Compare your answer with the original material."})
            else:
                fact_terms = self._keywords(fact)
                all_terms = self._keywords(" ".join(source))
                target = fact_terms[min(i, len(fact_terms)-1)] if fact_terms else f"Point {i+1}"
                blanked = re.sub(rf"\b{re.escape(target)}\b", "_____", fact, count=1, flags=re.IGNORECASE)
                distractors = [term for term in all_terms if term.lower() != target.lower()][:3]
                while len(distractors) < 3:
                    distractors.append(f"Option {len(distractors)+2}")
                choices = [target, *distractors]
                shift = i % 4
                choices = choices[shift:] + choices[:shift]
                question = f"أكمل العبارة الآتية من المادة:\n{blanked}" if arabic else f"Complete this statement from the material:\n{blanked}"
                result.append({"question":question,"choices":choices,"correct_answer":target,"explanation":""})
        return result

@lru_cache(maxsize=1)
def provider():
    if settings.ai_provider == "openai" and settings.openai_api_key:
        return OpenAIProvider()
    if settings.ai_provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError("Gemini is selected, but GEMINI_API_KEY is missing from backend/.env.")
        return GeminiProvider()
    if settings.ai_provider == "ollama":
        return OllamaProvider()
    return LocalStudyProvider()

def topic_context(topic):
    chunks = [f"SUBJECT: {topic.subject.name}\nTOPIC: {topic.title}\n{topic.description}"]
    chunks += [f"MATERIAL {m.file_name}:\n{m.extracted_text}" for m in topic.materials if m.extracted_text and getattr(m, "deleted_at", None) is None]
    chunks += [f"NOTE {n.title}:\n{n.content}" for n in topic.notes]
    return "\n\n".join(chunks)

_RAG_STOP_WORDS = {
    "about","after","also","and","are","can","could","explain","for","from","how","into","is","it","of","on","or","that","the","their","this","to","what","when","where","which","why","with","would",
    "اشرح","الى","إلى","التي","الذي","عن","على","في","ما","ماذا","من","هذا","هذه","هل","هو","هي","و","وش","كيف","لماذا"
}

def _rag_tokens(text: str) -> list[str]:
    normalized = text.lower().replace("أ","ا").replace("إ","ا").replace("آ","ا").replace("ى","ي").replace("ة","ه")
    return [token for token in re.findall(r"[a-z0-9\u0600-\u06ff]{2,}", normalized) if token not in _RAG_STOP_WORDS]

def _rag_chunks(topic, chunk_size: int = 1400, overlap: int = 180) -> list[dict]:
    sources = [("Topic overview", f"{topic.title}\n{topic.description}")]
    sources += [(f"Material: {item.file_name}", item.extracted_text) for item in topic.materials if item.extracted_text and getattr(item, "deleted_at", None) is None]
    sources += [(f"Note: {item.title}", item.content) for item in topic.notes if item.content]
    result=[]
    for source,text_value in sources:
        text_value=re.sub(r"\r\n?","\n",str(text_value)).strip()
        if not text_value: continue
        start=0
        while start<len(text_value):
            end=min(len(text_value),start+chunk_size)
            if end<len(text_value):
                boundary=max(text_value.rfind("\n",start,end),text_value.rfind(". ",start,end),text_value.rfind("؟",start,end))
                if boundary>start+chunk_size//2: end=boundary+1
            content=text_value[start:end].strip()
            if content: result.append({"source":source,"content":content,"tokens":_rag_tokens(content)})
            if end>=len(text_value): break
            start=max(start+1,end-overlap)
    return result

def retrieval_context(topic, query: str, max_chunks: int = 7, max_chars: int = 14000) -> str:
    """Local privacy-friendly RAG: rank lecture chunks against the question."""
    chunks=_rag_chunks(topic)
    if not chunks: return topic_context(topic)
    query_tokens=_rag_tokens(query)
    document_frequency=Counter(token for token in set(query_tokens) for chunk in chunks if token in set(chunk["tokens"]))
    ranked=[]
    for index,chunk in enumerate(chunks):
        counts=Counter(chunk["tokens"]);score=0.0
        for token in query_tokens:
            if counts[token]:
                inverse=math.log((len(chunks)+1)/(document_frequency[token]+1))+1
                score+=inverse*(1+math.log(counts[token]))
        if query.strip().lower() in chunk["content"].lower(): score+=4
        ranked.append((score,-index,chunk))
    ranked.sort(reverse=True,key=lambda item:(item[0],item[1]))
    selected=ranked[:max_chunks] if ranked and ranked[0][0]>0 else ranked[:min(4,max_chunks)]
    header=f"SUBJECT: {topic.subject.name}\nTOPIC: {topic.title}\nRAG retrieved {len(selected)} relevant passages. Use the source labels when judging support."
    parts=[header]
    used=len(header)
    for _,_,chunk in selected:
        block=f"SOURCE [{chunk['source']}]:\n{chunk['content']}"
        if used+len(block)>max_chars: break
        parts.append(block);used+=len(block)
    return "\n\n".join(parts)
