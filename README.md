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


## Phase 6: JWT Authentication + RBAC Authorization

Here's exactly what we build and why each piece matters.

---

### What Phase 6 Delivers

```
Phase 6:
─────────────────────────────────────────────────────
✅ User registration with bcrypt password hashing
✅ JWT token issuance on login
✅ Token validation on every protected request
✅ Token revocation on logout
✅ RBAC guards — USER vs ADMIN roles
✅ Protect all existing endpoints behind auth
✅ Unit + integration + E2E tests (Chapter 11)
```

---

### How It Connects to the Book

```
Chapter 8 concept              What we implement
─────────────────────────────────────────────────────
Basic auth                   → Skip (dev only)
JWT authentication           → Full implementation
Password hashing + salting   → bcrypt via passlib
Token service                → Create/decode/revoke
Auth service                 → Register/login/logout
OAuth                        → Phase 6 stretch goal
RBAC                         → USER/ADMIN roles
Authorization guards         → FastAPI dependencies
401 vs 403 distinction       → Separate exceptions
```

---

### New Files Created

```
app/
├── core/
│   └── security.py              ← JWT encode/decode + bcrypt
├── modules/
│   └── auth/
│       ├── entities.py          ← User + Token ORM models
│       ├── schemas.py           ← Login/register Pydantic schemas
│       ├── repository.py        ← User + Token DB operations
│       ├── service.py           ← AuthService orchestration
│       ├── dependencies.py      ← get_current_user, is_admin guards
│       └── router.py            ← /auth/register, /login, /logout

tests/
├── unit/
│   └── test_auth_service.py     ← password hashing, token logic
├── integration/
│   └── test_auth_repository.py  ← user/token DB operations
└── e2e/
    └── test_auth.py             ← register → login → access → logout
```

---

### New Dependencies

```txt
# requirements.txt additions
passlib[bcrypt]==1.7.4    ← password hashing
python-jose[cryptography]==3.3.0  ← JWT encode/decode
```

---

### What Gets Protected

```
BEFORE Phase 6:          AFTER Phase 6:
──────────────           ──────────────
GET  /health      →      GET  /health         (public)
POST /documents   →      POST /documents      (USER + ADMIN)
POST /rag/query   →      POST /rag/query      (USER + ADMIN)
POST /chat        →      POST /chat           (USER + ADMIN)
GET  /conversations →    GET  /conversations  (USER + ADMIN)
                         DELETE /conversations (ADMIN only)
                         POST /auth/register  (public)
                         POST /auth/login     (public)
                         POST /auth/logout    (authenticated)
```

---

### The Auth Flow We Implement

```
Registration:
  POST /auth/register
  { email, password }
       ↓
  Hash password with bcrypt + salt
       ↓
  Store User in DB
       ↓
  Return UserOut (no password)

Login:
  POST /auth/login
  { email, password }
       ↓
  Fetch user from DB
       ↓
  Verify password against hash
       ↓
  Create JWT token (exp: 60 min)
       ↓
  Store Token record in DB
       ↓
  Return { access_token, token_type: "bearer" }

Protected Request:
  POST /chat
  Authorization: Bearer <token>
       ↓
  Decode JWT → get user_id + token_id
       ↓
  Verify token is active in DB
       ↓
  Fetch User from DB
       ↓
  Inject User into route handler ✅

Logout:
  POST /auth/logout
  Authorization: Bearer <token>
       ↓
  Decode JWT → get token_id
       ↓
  Mark Token.is_active = False in DB
       ↓
  Future requests with same token → 401 ✅
```

---

### New Alembic Migration

```sql
-- Creates two new tables
CREATE TABLE users (
    id          VARCHAR(32) PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    role        VARCHAR(20) DEFAULT 'USER',
    created_at  TIMESTAMP,
    updated_at  TIMESTAMP
);

CREATE TABLE tokens (
    id          VARCHAR(32) PRIMARY KEY,
    user_id     VARCHAR(32) REFERENCES users(id),
    expires_at  TIMESTAMP NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP
);
```

---

### Test Coverage Plan

```
Unit tests:
  ✅ Password hash is not plain text
  ✅ Same password → different hashes (salting)
  ✅ Correct password verifies successfully
  ✅ Wrong password fails verification
  ✅ JWT token has 3 parts (header.payload.signature)
  ✅ Decoded token contains correct claims
  ✅ Tampered token raises UnauthorizedException
  ✅ Expired token raises UnauthorizedException

Integration tests:
  ✅ Register stores user in DB
  ✅ Duplicate email rejected
  ✅ Login returns valid JWT
  ✅ Wrong password returns 401
  ✅ Token stored in DB on login
  ✅ Token marked inactive on logout

E2E tests:
  ✅ Register → Login → Access protected endpoint
  ✅ Logout → same token rejected (401)
  ✅ No token → 401
  ✅ Invalid token → 401
  ✅ USER role → 403 on admin endpoint
  ✅ ADMIN role → 200 on admin endpoint
  ✅ Full horizontal workflow test
```

---

### Ready to Start?

Say **"Phase 6 go"** and I'll write all the code. Or if you have any questions about the plan first, ask away! 🚀

