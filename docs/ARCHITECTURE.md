# NAI Study architecture

## Shape

- `frontend`: Next.js App Router, TypeScript, Tailwind CSS.
- `backend`: FastAPI, SQLAlchemy 2, JWT bearer authentication, PostgreSQL.
- Uploaded files remain private on backend storage; only extracted text/metadata is exposed through owned routes.
- `integrations/ai.py` contains the replaceable `AIProvider` boundary and model-specific providers. `LocalStudyProvider` keeps the app usable for development without an API key.

## Ownership

Every request begins with the authenticated user. Nested resources are resolved through their parent (`Subject.user_id`, `Topic.subject.user_id`). No route accepts a client-supplied owner ID.

## Main routes

- `/auth/register`, `/auth/login`, `/auth/me`
- `/dashboard`, `/subjects`, `/subjects/{id}/topics`, `/topics/{id}`
- `/topics/{id}/materials`, `/topics/{id}/materials/text`, `/materials/{id}`
- `/topics/{id}/notes`, `/notes/{id}`
- `/topics/{id}/chat`, `/ai/chat`, `/ai/summarize`, `/ai/flashcards`, `/ai/concept-map`, `/ai/quiz`, `/ai/evaluate-answer`
- `/topics/{id}/summaries|flashcards|concept-maps|quizzes`
- `/tasks`, `/reminders`
- `/materials/{id}/pages|file|page/{number}`, `/study/context-action`
- `/review/due`, `/review/items`, `/review/mistakes`, `/progress`
- `/exams`, `/study-plans`, `/calendar`, `/study-sessions`
- `/ai/mock-exam`, `/mock-exams/{id}/submit`, `/search`

## Frontend pages

- `/login`, `/register`
- `/dashboard`, `/subjects`, `/subjects/[id]`, `/topics/[id]`
- `/tasks`, `/reminders`, `/settings`
- `/materials/[id]`, `/notes/[id]`, `/review`, `/progress`
- `/planner`, `/calendar`, `/focus`, `/exam-mode`, `/search`
- `/tools/[tool]`, `/results/[type]`

The topic page is a single connected workspace with Overview, Materials, Tutor, Summary, Flashcards, Concept Map, Quiz, and Notes tabs.
# Priority 1 study experience

NAI Study's first study-experience increment keeps the existing visual system and adds a focused learning loop:

- `frontend/features/study/StudyMode.tsx` owns the interactive Teach me, Quick review, and Quiz me experience.
- `backend/app/services/study.py` owns tutor-mode prompts, contextual response actions, semantic answer evaluation, and mistake retrieval.
- `backend/app/routers/study_sessions.py` exposes educational evaluation and mistake-review APIs while enforcing the existing ownership checks.
- The existing AI provider abstraction and local retrieval context remain the single path to uploaded lecture context.

Short-answer and essay evaluation is semantic when an AI provider is available, with a deterministic concept-coverage fallback for local/offline use. MCQ and True/False remain deterministic. Feedback is explicitly educational and stores the concepts that were correct, missing, or incorrect.

## Extended study workspace modules

- `routers/learning_content.py`: subjects, lectures, private materials, notes, and private library search.
- `routers/ai_tools.py`: tutor chat, summaries, flashcards, concept maps, and quizzes.
- `routers/material_reader.py`: owner-protected material files and page-level extracted text.
- `routers/review_memory.py`: spaced-repetition scheduling, due review, and progress signals.
- `routers/exam_mode.py`: answer-hidden mock exams and post-submission feedback.
- `routers/study_planning.py`: exams, plans, plan items, rescheduling, calendar, and study sessions.
- `routers/study_library.py`: saved summaries and generated-question library operations.
- `routers/dashboard.py`: dashboard aggregation and productivity overview.
- `routers/study_sessions.py`: study evaluation, mistakes, and context actions.

New relational entities cover material pages, exams and exam topics, study plans and plan items, study sessions, and topic progress. Existing data is preserved; SQLite-compatible additive migration logic handles new flashcard scheduling columns.

## Frontend organization

- `features/auth/`: authentication form and account entry experience.
- `features/dashboard/`: dashboard-only widgets and due-card overview.
- `features/library/pages/`: subjects, saved summaries, tests, results, and private search screens.
- `features/planning/`: task and reminder workspace.
- `features/planning/pages/`: calendar and study-plan screens.
- `features/study/TopicWorkspace.tsx`: the complete lecture workspace, including overview, materials, tutor, and notes panels.
- `features/study/*Studio.tsx`: reusable summary, flashcard, quiz, and concept-map workspaces shared by lecture pages and the global tools flow.
- `features/study/pages/`: material reader, note editor, review, focus, exam, progress, and tool-selection screens.
- `components/layout/`: shared application navigation and brand mark.
- `components/ui/`: small reusable presentation primitives such as the modal.
- Route `page.tsx` files are thin framework entry points that re-export their feature screen without changing URL behavior.

## Backend organization

- `core/config.py`: validated environment settings and application constants.
- `core/security.py`: password hashing, JWT creation, and authenticated-user dependency.
- `db/session.py`: SQLAlchemy engine, session factory, and request database dependency.
- `db/migrations.py`: safe additive initialization for existing SQLite/PostgreSQL data.
- `integrations/ai.py`: Gemini, OpenAI, Ollama, and local AI provider implementations.
- `services/ownership.py`: centralized per-user resource ownership checks.
- `services/study.py`: tutor prompting, evaluation, mistakes, and subject aggregation logic.
- `routers/`: HTTP transport only, grouped by concrete domain responsibility.
- `models.py` and `schemas.py`: SQLAlchemy persistence models and Pydantic API contracts respectively.
