<div align="center">

# 💰 Finance Analytics API

### Production-grade financial backend built for the real world.

[![CI](https://github.com/Pavan8104/finance-analytics-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/Pavan8104/finance-analytics-backend/actions)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009485?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![Tests](https://img.shields.io/badge/Tests-52%20Passing-brightgreen?logo=pytest)](tests/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

**[Live Docs →](http://localhost:8000/api/v1/docs)** · **[API Reference](#-api-reference)** · **[Quick Start](#-quick-start)**

</div>

---

> A **REST API** for personal and enterprise financial analytics — built with the architecture, security posture, and operational standards expected in production FinTech systems. Not a demo. Deployable today.

---

## ⚡ 60-Second Overview

| What | How |
|------|-----|
| **Auth** | JWT (access + refresh tokens), bcrypt-12, rate-limited login |
| **RBAC** | Viewer / Analyst / Admin — factory-pattern, privilege escalation hardcoded blocked |
| **Transactions** | Full CRUD, ownership-isolated, 5 query filters, smart pagination |
| **Analytics** | Totals, balance, category breakdowns (%), monthly P&L — cached per user |
| **Security** | HSTS · CSP · X-Frame-Options · Permissions-Policy · timing-safe auth |
| **Observability** | Structured JSON logs, request/response middleware, rotating file handler |
| **Deployment** | Multistage Docker + Compose, Alembic migrations, GitHub Actions CI |

```bash
# Start the entire stack in one command
docker-compose up --build
# → API:      http://localhost:8000/api/v1/docs
# → Health:   http://localhost:8000/health
# → Ready:    http://localhost:8000/ready
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Client (Browser / Mobile / CLI)               │
└─────────────────────────────┬────────────────────────────────────┘
                              │ HTTPS / JWT Bearer
┌─────────────────────────────▼────────────────────────────────────┐
│                        FastAPI Application                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Middleware Chain                                        │   │
│  │  RequestLoggingMiddleware → CORSMiddleware               │   │
│  │  → SecurityHeadersMiddleware                             │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │  API Layer  /api/v1                                      │   │
│  │  /auth   /users   /transactions   /analytics   /admin   │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │  Service Layer  (Business Logic + Cache)                 │   │
│  │  AuthService · UserService · TransactionService          │   │
│  │  AnalyticsService (TTLCache, 5 min, per-user)           │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │  Data Layer                                              │   │
│  │  SQLAlchemy 2.0 ORM + Alembic Migrations                │   │
│  │  PostgreSQL (prod) / SQLite in-memory (test)            │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

**Design Decisions:**
- `api → service → model` strict separation — routes have zero business logic
- Services are independently unit-testable (no HTTP overhead)
- DB schema changes never touch endpoint files

---

## ✨ Features

### 🔐 Security — Layered Defense
- **JWT Authentication** — short-lived access tokens (30 min) + long-lived refresh tokens (7 days)
- **bcrypt password hashing** at cost factor 12 (OWASP minimum)
- **Rate limiting** — login endpoint capped at 10 req/min per IP
- **Timing-safe authentication** — bcrypt always runs even for non-existent users (prevents user enumeration via response timing)
- **Privilege escalation hardcoded blocked** — public signup always creates `viewer` role, regardless of request body
- **HTTP Security Headers** — HSTS, X-Frame-Options (DENY), CSP, Permissions-Policy, Referrer-Policy

### 👥 Role-Based Access Control
Three hierarchical roles with factory-pattern dependency injection:

```python
# Adding a new role to any endpoint is a single line
get_current_active_admin            = require_roles(RoleEnum.admin)
get_current_active_analyst_or_admin = require_roles(RoleEnum.analyst, RoleEnum.admin)
```

### 💳 Transaction Management
- Full CRUD with **ownership isolation** enforced at the service layer
- Filter by `type`, `category`, `start_date`, `end_date`
- Pagination with `total`, `pages`, `has_next`, `has_prev`, `next_skip`
- **`Numeric(12, 2)`** precision — no floating-point rounding errors in financial data
- Composite DB indexes on `(owner_id, date)` and `(owner_id, type)` for sub-millisecond analytics queries

### 📊 Analytics Engine
```json
{
  "total_income": "45000.00",
  "total_expenses": "18200.00",
  "balance": "26800.00",
  "transaction_count": 48,
  "avg_transaction_amount": "1312.50",
  "income_by_category": [
    { "category": "Salary", "total_amount": "40000.00", "percentage": 88.9 },
    { "category": "Freelance", "total_amount": "5000.00", "percentage": 11.1 }
  ],
  "monthly_breakdown": [
    { "month": "2024-07", "income": "15000.00", "expense": "6100.00", "net": "8900.00" }
  ]
}
```
- 5-minute **TTL cache per user** — eliminates repeated DB aggregation
- SQL-level `GROUP BY` — no Python-side loops
- Cache invalidated on every transaction mutation

### 🧾 Observability
- **Structured JSON logs** — machine-parseable by Datadog, CloudWatch, Loki, Splunk
- **Request/response middleware** — logs method, path, status, duration_ms, client_ip on every call
- Rotating file handler (10 MB cap, 5 backups)
- File logging disabled in test mode — clean CI output

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Framework** | FastAPI 0.115 | Async-native, OpenAPI auto-docs, Pydantic v2 |
| **ORM** | SQLAlchemy 2.0 | Type-safe queries, connection pooling, Alembic integration |
| **Database** | PostgreSQL 16 | ACID compliance, `NUMERIC` type for financial precision |
| **Auth** | python-jose + bcrypt | Industry-standard JWT + secure password hashing |
| **Validation** | Pydantic v2 | Compile-time schema validation, custom validators |
| **Caching** | cachetools TTLCache | Thread-safe in-process cache, zero infrastructure |
| **Rate Limiting** | slowapi | Per-IP limiting with Starlette middleware integration |
| **Testing** | pytest + httpx | In-memory SQLite, function-scoped isolation, role fixtures |
| **Containerization** | Docker + Compose | Multistage build, non-root user, health checks |
| **Migrations** | Alembic | Schema versioning, autogenerate from ORM models |
| **CI/CD** | GitHub Actions | Test + lint + Docker build — 3 parallel jobs |
| **Logging** | python-json-logger | Structured JSON, rotating file handler |

---

## 🚀 Quick Start

### Option 1 — Docker (Recommended)

```bash
# Clone
git clone https://github.com/Pavan8104/finance-analytics-backend.git
cd finance-analytics-backend

# Configure
cp .env.example .env
# Required: set SECRET_KEY to output of: openssl rand -hex 32
# Required: set POSTGRES_PASSWORD to a strong password

# Launch
docker-compose up --build

# Seed with sample data (optional)
docker-compose exec app python seed.py
```

**Open:** http://localhost:8000/api/v1/docs

---

### Option 2 — Local Python

```bash
git clone https://github.com/Pavan8104/finance-analytics-backend.git
cd finance-analytics-backend

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # Edit: set SECRET_KEY

python seed.py          # Bootstrap DB + sample data
uvicorn app.main:app --reload
```

**Open:** http://localhost:8000/api/v1/docs

---

## 🔑 Default Credentials

> ⚠️ Change these immediately in non-local environments.

| Role | Email | Password | Access |
|------|-------|----------|--------|
| Admin | admin@example.com | admin123 | Everything |
| Analyst | analyst@example.com | analyst123 | Analytics + Transactions |

---

## 📖 API Reference

### Authentication

```bash
# Login — returns access + refresh tokens
curl -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=admin@example.com" \
  -F "password=admin123"

# Response
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "refresh_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer"
}
```

### Transactions

```bash
# Create
curl -X POST http://localhost:8000/api/v1/transactions/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": "3500.00", "type": "income", "category": "Salary"}'

# List with filters + pagination
curl "http://localhost:8000/api/v1/transactions/?type=expense&skip=0&limit=20" \
  -H "Authorization: Bearer <token>"

# Paginated response
{
  "items": [...],
  "total": 48,
  "page": 1,
  "pages": 3,
  "has_next": true,
  "has_prev": false,
  "next_skip": 20
}
```

### Analytics *(Analyst / Admin)*

```bash
curl http://localhost:8000/api/v1/analytics/report \
  -H "Authorization: Bearer <analyst_or_admin_token>"
```

### Admin Stats *(Admin only)*

```bash
curl http://localhost:8000/api/v1/admin/stats \
  -H "Authorization: Bearer <admin_token>"

# Response
{
  "total_users": 42,
  "active_users": 39,
  "inactive_users": 3,
  "total_transactions": 1284,
  "total_income_all_users": "234500.00",
  "total_expenses_all_users": "98200.00",
  "users_by_role": { "viewer": 38, "analyst": 3, "admin": 1 }
}
```

---

## 🛡️ RBAC Matrix

| Endpoint | Viewer | Analyst | Admin |
|----------|:------:|:-------:|:-----:|
| `POST /auth/login` | ✅ | ✅ | ✅ |
| `POST /users/` (signup) | ✅ | ✅ | ✅ |
| `GET /users/me` | ✅ | ✅ | ✅ |
| `PATCH /users/me` | ✅ | ✅ | ✅ |
| Transaction CRUD (own) | ✅ | ✅ | ✅ |
| `GET /analytics/report` | ❌ | ✅ | ✅ |
| `GET /users/` (all users) | ❌ | ❌ | ✅ |
| `POST /users/admin` | ❌ | ❌ | ✅ |
| `GET /admin/stats` | ❌ | ❌ | ✅ |

> **Security Note:** The public signup endpoint (`POST /users/`) **always** creates a `viewer` account — regardless of any `role` field in the request body. Analyst and Admin accounts can only be created by an existing admin via `POST /users/admin`.

---

## 🧪 Testing

```bash
# Run full suite
make test

# With coverage report
make test-cov

# Run specific module
pytest tests/test_auth.py -v
```

**Test suite: 52 tests, 0 failures**

| Module | Tests | What's Covered |
|--------|-------|----------------|
| `test_auth.py` | 11 | Login, 401/403/422, enumeration prevention, system probes |
| `test_users.py` | 13 | Signup, privilege escalation attempts, admin CRUD |
| `test_transactions.py` | 19 | Full CRUD, ownership isolation, filters, pagination |
| `test_analytics.py` | 9 | RBAC enforcement, totals, category, data isolation |

**Infrastructure:**
- In-memory SQLite — zero DB setup needed, tests run in ~20 seconds
- Function-scoped fixtures with rollback — every test starts with a clean state
- Authenticated client fixtures for each role (`viewer_client`, `analyst_client`, `admin_client`)

---

## 🐳 Docker

```bash
make docker-up      # Start full stack (API + PostgreSQL)
make docker-down    # Stop stack
make docker-logs    # Follow API logs
make docker-seed    # Seed database inside container
```

**What runs:**
- `finance_api` — FastAPI app, port 8000, non-root user (uid 1001)
- `finance_db` — PostgreSQL 16 Alpine, port 5432, persistent named volume
- Health checks on both services; API waits for DB to be healthy before starting

---

## 🔄 Database Migrations

```bash
# Generate a migration from model changes
alembic revision --autogenerate -m "add column X"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ Prod | auto-gen | JWT signing key — `openssl rand -hex 32` |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `DATABASE_URL` | No | SQLite | PostgreSQL DSN in production |
| `CORS_ORIGINS` | No | `localhost:3000` | Comma-separated allowed origins |
| `ENVIRONMENT` | No | `development` | `development` / `staging` / `production` |
| `RATE_LIMIT_PER_MINUTE` | No | `60` | Global requests per minute per IP |
| `POSTGRES_PASSWORD` | Docker ✅ | — | PostgreSQL password |

---

## 🔒 Security Design

| Threat | Mitigation |
|--------|-----------|
| Hardcoded secrets | `SECRET_KEY` from `.env`; startup fails if default value detected |
| Privilege escalation | Public signup hardcoded to `viewer`; role assignment admin-only |
| User enumeration | `AuthService` always runs bcrypt — constant-time regardless of user existence |
| Brute-force login | `slowapi` rate limiter — 10 attempts/minute per IP |
| CORS wildcard | Explicit `CORS_ORIGINS` — never `*` |
| Raw error messages | Global exception handler — clean JSON, no stack traces |
| SQL injection | SQLAlchemy ORM with parameterised queries throughout |
| Weak passwords | Pydantic validators: min 8 chars, not all-numeric |
| Clickjacking | `X-Frame-Options: DENY` |
| MITM | `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` |
| Stale DB connections | `pool_pre_ping=True` on engine |

---

## 🗂️ Project Structure

```
finance-analytics-backend/
├── app/
│   ├── api/
│   │   ├── api_v1.py                   # Router aggregation
│   │   └── endpoints/
│   │       ├── auth.py                 # Login (rate-limited)
│   │       ├── users.py                # User CRUD + admin management
│   │       ├── transactions.py         # Financial transaction CRUD
│   │       ├── analytics.py            # Analytics report
│   │       └── admin.py                # System-wide stats
│   ├── core/
│   │   ├── config.py                   # Pydantic settings (reads .env)
│   │   ├── database.py                 # Engine + session + pool config
│   │   ├── dependencies.py             # JWT validation + RBAC factory
│   │   ├── exceptions.py               # Global exception handlers
│   │   └── security.py                 # JWT creation + bcrypt
│   ├── middleware/
│   │   ├── logging_middleware.py       # Request/response logger
│   │   └── security_headers.py         # HSTS, CSP, X-Frame-Options
│   ├── models/
│   │   ├── user.py                     # User model + RoleEnum
│   │   └── transaction.py              # Transaction model + indexes
│   ├── schemas/
│   │   ├── token.py                    # JWT schemas
│   │   ├── user.py                     # User input/output schemas
│   │   ├── transaction.py              # Transaction + pagination schemas
│   │   ├── analytics.py                # Analytics report schema
│   │   └── admin.py                    # System stats schema
│   ├── services/
│   │   ├── auth_service.py             # Timing-safe authentication
│   │   ├── user_service.py             # User business logic
│   │   ├── transaction_service.py      # Transaction CRUD logic
│   │   └── analytics_service.py        # Report + TTLCache
│   ├── utils/
│   │   └── logger.py                   # Structured JSON logger
│   └── main.py                         # App factory + lifespan
├── tests/
│   ├── conftest.py                     # Fixtures: DB, clients, users
│   ├── test_auth.py                    # Auth flow tests
│   ├── test_users.py                   # User management + RBAC tests
│   ├── test_transactions.py            # Transaction CRUD + isolation
│   └── test_analytics.py              # Analytics RBAC + data tests
├── alembic/                            # Database migration files
├── .github/workflows/ci.yml            # CI: test + lint + docker build
├── Dockerfile                          # Multistage production image
├── docker-compose.yml                  # App + PostgreSQL stack
├── Makefile                            # Developer workflow shortcuts
├── pyproject.toml                      # Pytest + coverage config
├── requirements.txt                    # Pinned dependencies
├── .env.example                        # Config template
└── seed.py                             # Database bootstrapper
```

---

## 🤖 CI/CD Pipeline

Three parallel jobs on every push and pull request:

```yaml
test:        pytest + coverage → Codecov
lint:        ruff static analysis
docker-build: Dockerfile validation with layer caching
```

No broken builds can reach `main`.

---

## 🧰 Developer Commands

```bash
make install      # Install dependencies
make run          # Start dev server with hot reload
make seed         # Seed database
make test         # Run test suite
make test-cov     # Tests + HTML coverage report
make docker-up    # Start full Docker stack
make docker-down  # Stop stack
make docker-logs  # Stream app logs
make clean        # Remove cache + temp files
```

---

## 📬 Contact

**Pavan** — [GitHub](https://github.com/Pavan8104) · [LinkedIn](https://linkedin.com/in/pavan8104)

---

<div align="center">

Built with precision. Deployed with confidence.

⭐ **Star this repo if you find it useful**

</div>
