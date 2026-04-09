# DocuMind

RAG-powered document intelligence service.

## Tech Stack

- Python 3.x
- FastAPI 0.111.1
- Pydantic 2.7.4
- pydantic-settings 2.3.4
- Mock LLM (no real API key)
- Git Bash on Windows
- Virtual env at `.venv/Scripts/activate`

## Project Structure

```
documind/
├── app/
│   ├── main.py
│   ├── settings.py
│   ├── exceptions.py
│   ├── middleware.py
│   ├── modules/health/router.py
│   └── providers/llm.py        # empty — Phase 2
├── tests/
│   ├── conftest.py
│   ├── unit/test_settings.py
│   └── e2e/test_health.py
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

## Getting Started

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Verify key packages:

```bash
pip show fastapi pydantic pydantic-settings loguru pytest | grep -E "Name|Version"
```

Run tests:

```bash
pytest tests/ -v
```

## Git Setup

```bash
git config core.autocrlf input
git add setup.sh documind/
git commit -m "Phase 1 of the project"
git push origin main
```

## Status

**Tests:** 46 passed ✅

## Key Fixes

- Pinned `pydantic-settings==2.3.4` (no Rust needed)
- Monkey-patched `get_settings` in `conftest.py` to fix `lru_cache` test isolation issue

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Project structure, settings, middleware, health endpoint | ✅ Done |
| 2 | Mock LLM client, document upload, PDF extraction, 46 tests | ✅ Done |
| 3 | RAG pipeline — embed documents into Qdrant | ⏳ Pending |
| 4 | SSE streaming chat endpoint | ⏳ Pending |
| 5 | Postgres + Alembic replaces in-memory store | ⏳ Pending |
| 6 | JWT authentication | ⏳ Pending |