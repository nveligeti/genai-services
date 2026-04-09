# Project - DocuMind — RAG-powered document intelligence service

TECH STACK:
- FastAPI 0.111.1
- Pydantic 2.7.4
- pydantic-settings 2.3.4
- Python 3.x
- Mock LLM (no real API key)
- Git Bash on Windows
- Virtual env at .venv/Scripts/activate


STRUCTURE:
documind/
├── app/
│   ├── main.py
│   ├── settings.py
│   ├── exceptions.py
│   ├── middleware.py
│   ├── modules/health/router.py
│   └── providers/llm.py (empty — Phase 2)
├── tests/
│   ├── conftest.py
│   ├── unit/test_settings.py
│   └── e2e/test_health.py
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini

TEST STATUS: 17 passed ✅


# genai-services dependencies
pip install -r requirements-dev.txt
# Check all key packages are present
pip show fastapi pydantic pydantic-settings loguru pytest | grep -E "Name|Version"

pytest tests/ -v
git config  core.autocrlf input
git add  setup.sh documind/
git commit -m "Phase 1 of the project"
git push origin main

COMPLETED:
- Phase 1: Project structure, settings, middleware,
  health endpoint, exception handlers, 17 passing tests

KEY FIXES APPLIED:
- Pinned pydantic-settings==2.3.4 (no Rust needed)
- Monkey-patched get_settings in conftest.py
  to fix lru_cache test isolation issue

NEXT: Phase 2 — Mock LLM client + document upload endpoint
      Chapters 3, 4, 5 applied

      