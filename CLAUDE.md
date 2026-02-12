# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BabySteps Digital School is an AI-enabled gamified digital education platform for students Class 1-12 (Indian curriculum, bilingual English/Telugu). Django REST backend + React TypeScript SPA frontend + local Ollama LLM.

## Commands

### Running the Application (3 services needed)

```bash
# Option 1: Automated startup (Windows PowerShell)
.\start_babysteps.ps1

# Option 2: Manual (3 separate terminals)
ollama serve                                    # Terminal 1: LLM server
python manage.py runserver 8000                 # Terminal 2: Django backend
cd frontend && npm start                        # Terminal 3: React frontend (port 3000)
```

### Backend Testing (pytest)

```bash
pytest                                          # Run all tests
pytest tests/test_curriculum_api.py             # Single test file
pytest tests/test_curriculum_api.py::TestClass::test_name  # Single test
pytest -k "test_name_pattern"                   # Pattern match
pytest --cov                                    # With coverage report
```

### Frontend Testing (Jest)

```bash
cd frontend
npm test                                        # Interactive watch mode
npm test -- --coverage                          # With coverage
npm test -- --watchAll=false                    # Single run (CI)
npm test -- --testPathPattern=progressReducer   # Single test file
```

### Database

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Build

```bash
cd frontend && npm run build                    # Production build to frontend/build/
```

## Architecture

```
Backend (Django 5.2 + DRF)          Frontend (React 18 + TS)       LLM (Ollama)
http://127.0.0.1:8000              http://localhost:3000           http://127.0.0.1:11434
├── backend/settings.py            ├── src/pages/                  Model: llama3.2
├── backend/urls.py                ├── src/components/
└── services/                      ├── src/services/  (API clients)
    ├── curriculum_loader_service/ ├── src/state/     (reducers)
    ├── mentor_chat_service/       ├── src/models/    (Zod schemas)
    ├── analytics_service/         └── src/contexts/  (TTS)
    ├── learning_engine/
    ├── llm_service/
    └── student_registration/
```

### Backend Service Pattern

Each Django app under `services/` is a self-contained service with its own `models.py`, `views.py`, `urls.py`, and `services.py`. They share a single SQLite database (dev) configured in `backend/settings.py`.

### API Routes

| Prefix | Service | Purpose |
|--------|---------|---------|
| `/api/curriculum/` | curriculum_loader_service | Lesson loading, question banks, caching |
| `/api/mentor/` | mentor_chat_service | AI chat with Ollama (teacher persona "Aarini") |
| `/api/analytics/` | analytics_service | Activity logging, progress, skill mastery |
| `/api/learning/` | learning_engine | Micro-lessons, adaptive difficulty, streaks |
| `/api/register/` | student_registration | Registration + admin approval workflow |
| `/admin/` | Django admin | Database management UI |

### LLM Integration

The `llm_service` uses Factory + Strategy patterns to abstract LLM providers. Currently uses Ollama (local, offline). Provider config is in `backend/settings.py` under `LLM_PROVIDER` and `LLM_CONFIG`. Mock Ollama responses are set up in `conftest.py` for tests.

### Frontend Key Patterns

- **Routing**: React Router v6 in `App.tsx`
- **Validation**: Zod schemas in `src/models/` for runtime type checking
- **State**: Reducer pattern in `src/state/` (XP system, spaced repetition)
- **TTS**: Browser Web Speech API via `TTSProvider` context (Indian English `en-IN`)
- **API calls**: Axios clients in `src/services/`

### Curriculum Content

JSON files in `curriculam/` (note spelling) organized as `class{N}/{Subject}/month{M}/week{W}/day{D}/lesson.json` and `qb.json`. 400+ files for Class 1 EVS alone.

## Coding Conventions (from rules.md)

- **Python**: PEP 8, snake_case functions/variables, PascalCase classes, 88 char line limit
- **Comments**: Date-prefixed format `# YYYY-MM-DD: Description` on every line
- **Docstrings**: Required on every public class, function, and module
- **Testing**: TDD mandatory. Tests in `tests/` directory. Target 99% coverage. Feature is not complete without passing tests.
- **Architecture**: Microservices pattern within Django monolith. SOLID principles.
- **Security**: Sanitize all inputs, no exposed stack traces, CSRF enabled, CORS restricted

## Test Configuration

pytest is configured in `pytest.ini` with markers: `django_db`, `slow`, `integration`, `unit`. Shared fixtures (api_client, sample_curriculum, sample_lesson, mock Ollama) are in `conftest.py`.

Frontend uses Jest + React Testing Library. ESLint config extends `react-app`.
