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
│   ├── core/           # SQLAlchemy engine + session
│   ├── modules/
│   │   ├── health/
│   │   ├── documents/
│   │   ├── rag/
│   │   ├── chat/
│   │   └── conversations/
│   └── providers/
│       └── llm.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic/
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

## Getting Started

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest tests/ -v
```

## Git Setup

```bash
git config core.autocrlf input
```

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Project structure, settings, middleware, health endpoint | ✅ Done |
| 2 | Mock LLM client, document upload, PDF extraction | ✅ Done |
| 3 | RAG pipeline — Qdrant vector store, semantic search | ✅ Done |
| 4 | SSE streaming chat endpoint, RAG-augmented prompts | ✅ Done |
| 5 | Postgres + Alembic, persistent conversation history | ✅ Done |
| 6 | JWT authentication | ⏳ Pending |

## Key Notes

### FastAPI dependency overrides

Always use `app.dependency_overrides` to mock FastAPI dependencies — never `monkeypatch`. FastAPI resolves dependencies by function object identity, not module name.

```python
# Wrong — FastAPI still calls the original
monkeypatch.setattr("module.get_rag_pipeline", mock)

# Correct — patches the exact reference FastAPI holds
app.dependency_overrides[get_rag_pipeline] = lambda: mock
```

### App factory pattern

`create_app()` must be called on demand, not at module level. Module-level code runs at import time — before test fixtures can override dependencies. The factory pattern gives tests full control over the environment before the app is instantiated.

### Windows + psycopg event loop

Windows defaults to `ProactorEventLoop` (Python 3.8+), but psycopg's async driver requires `SelectorEventLoop`. Fix:

```python
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

### Known fixes

- Pinned `pydantic-settings==2.3.4` (no Rust needed)
- Monkey-patched `get_settings` in `conftest.py` to fix `lru_cache` test isolation
