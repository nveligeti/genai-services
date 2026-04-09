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

**Tests:** 17 passed ✅

**Completed — Phase 1:** Project structure, settings, middleware, health endpoint, exception handlers.

**Up next — Phase 2:** Mock LLM client + document upload endpoint (Chapters 3, 4, 5).

## Key Fixes

- Pinned `pydantic-settings==2.3.4` (no Rust needed)
- Monkey-patched `get_settings` in `conftest.py` to fix `lru_cache` test isolation issue
