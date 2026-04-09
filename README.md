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


Phase 3 delivers:
─────────────────────────────────────────────────────
✅ Qdrant vector database setup (Chapter 5)
✅ Text chunking + embedding pipeline (Chapter 5)
✅ Vector repository pattern (Chapter 7)
✅ RAG service — store + retrieve (Chapter 5)
✅ Query endpoint (Chapter 2)
✅ Semantic search with cosine similarity (Chapter 5)
✅ Unit + integration + E2E tests (Chapter 11)

Phase 3 connects Chapters 5 and 7 — building the vector database pipeline that lets users query their uploaded documents semantically.

Phase 4 delivers:
─────────────────────────────────────────────────────
✅ SSE streaming chat endpoint (Chapter 6)
✅ RAG-augmented prompt builder (Chapter 10)
✅ Chat schemas with conversation history (Chapter 4)
✅ Async stream generator (Chapter 5)
✅ DONE sentinel + error handling (Chapter 6)
✅ Unit + integration + E2E tests (Chapter 11)

Phase 4 connects Chapters 6, 5, and 10 — real-time streaming responses that combine RAG context with the Mock LLM using Server-Sent Events.

monkeypatch.setattr patches the module-level name
but FastAPI's DI system holds a reference to the
original function object — not the module name.

dependency_overrides[get_rag_pipeline] patches
the exact function object FastAPI uses internally.

monkeypatch:          module.get_rag_pipeline = mock
                      FastAPI still calls original ❌

dependency_overrides: FastAPI.di[get_rag_pipeline] = mock
                      FastAPI calls mock ✅

Chapter 11 lesson: Always use app.dependency_overrides to mock FastAPI dependencies — never monkeypatch. FastAPI's DI system resolves dependencies by function object identity, not by module name. monkeypatch replaces the name in the module namespace but FastAPI already captured the original reference.

