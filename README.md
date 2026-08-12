# NAI Study

> Your Personal AI Study Tutor

NAI Study is a focused, full-stack private study tutor. A student organizes subjects and lectures, uploads private material, and uses an AI tutor to understand, summarize, memorize, map, and test that material.

## What NAI Study includes

- Secure account registration and JWT login with strict per-user ownership.
- Dashboard, subjects, lectures, recent activity, tasks, and in-app reminders.
- Private PDF/image/text uploads with page-aware extraction, an in-app reader, zoom/navigation, selected-text context, and a responsive material/tutor split view.
- Interactive Study Mode with Teach Me, Quick Review, Quiz Me, alternate explanations, examples, and understanding checks.
- Topic-aware Arabic/English tutor with intentional retrieval context, conversation history, and source awareness.
- Five summary modes, manual/AI flashcards, spaced repetition, daily review, concept maps, and AI-assisted rich study notes.
- MCQ, true/false, short-answer, essay, and timed mock exams with semantic educational feedback and mistake review.
- Upcoming exams, manual/AI study plans, rescheduling, integrated calendar, Focus Mode, and study-session tracking.
- Useful progress labels based on quiz and flashcard activity, plus private global search across the student's learning library.
- Responsive white, blue, and purple interface with loading/error states.
- Replaceable AI provider and useful local study mode when no API key exists.

## Screenshots

Add portfolio screenshots here after starting the application.

## Architecture

```text
Browser → Next.js / React → FastAPI REST API → PostgreSQL
                                ├─ private file storage / PDF extraction
                                └─ AIProvider → OpenAI (or local study mode)
```

See [the detailed architecture](docs/ARCHITECTURE.md).

## Stack

- Next.js 16, React 19, TypeScript, Tailwind CSS
- FastAPI, Pydantic, SQLAlchemy 2
- PostgreSQL (SQLite is the zero-setup local fallback)
- JWT, Passlib/bcrypt, pypdf, OpenAI-compatible provider boundary

## Setup

1. Copy `.env.example` to `.env`.
2. For PostgreSQL, run `docker compose up -d db`. To use the local SQLite fallback, omit `DATABASE_URL`.
3. Install and run the backend:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

4. In another terminal, install and run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Interactive API documentation is at `http://localhost:8000/docs`.

## Environment variables

| Name | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL SQLAlchemy URL; omit for local SQLite |
| `JWT_SECRET` | Long random token-signing secret |
| `AI_PROVIDER` | `gemini`, `openai`, `ollama`, or `local` |
| `OPENAI_API_KEY` | Server-only key; never exposed to Next.js |
| `OPENAI_MODEL` | Model used by the OpenAI provider |
| `GEMINI_API_KEY` | Google AI Studio API key (keep this in the backend only) |
| `GEMINI_MODEL` | Gemini model, defaults to the low-latency `gemini-3.1-flash-lite` |
| `FRONTEND_ORIGIN` | Allowed browser origin |
| `MAX_UPLOAD_MB` | Upload limit |
| `NEXT_PUBLIC_API_URL` | Browser-visible FastAPI base URL |

## Verification

```bash
cd backend && pytest -q
cd frontend && npm run build
```

## Project Structure

```text
NAI Study/
├── frontend/
│   ├── app/                 # Next.js routes and layouts
│   ├── features/            # Feature-owned screens and UI: auth, dashboard, library, planning, study
│   ├── components/          # Shared layout and reusable UI primitives
│   └── lib/                 # API client and shared study-tool metadata
├── backend/
│   ├── app/
│   │   ├── routers/         # FastAPI endpoints grouped by responsibility
│   │   ├── core/            # Environment configuration and authentication security
│   │   ├── db/              # SQLAlchemy session and additive migrations
│   │   ├── integrations/    # Replaceable external AI providers
│   │   └── services/        # Ownership checks and reusable study-domain logic
│   ├── tests/               # API flow and retrieval tests
│   └── uploads/             # Private uploaded files (ignored by Git)
├── docs/                    # Architecture and feature documentation
└── docker-compose.yml       # Optional PostgreSQL development service
```

Route files remain inside `frontend/app` because they are required by the Next.js App Router. Feature-specific components live with their feature; only genuinely shared layout and UI components live under `frontend/components`.

## Security notes

Passwords are hashed and private data is always resolved through the authenticated owner. Files are type/size validated, stored outside the public frontend, and ignored by Git. Replace the development JWT secret before deployment.

## Product scope

NAI Study stays focused on one connected learning loop: plan, study, understand, practice, identify mistakes, review, remember, and prepare for exams. Payments, communities, patient systems, and unrelated generic-productivity features remain out of scope.
