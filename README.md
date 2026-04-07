# Finance Analytics Backend

## 👨‍💻 Project By
Pavan Sharma

---

## 📌 About This Project

This project is a backend API built using FastAPI for managing personal financial records and generating useful insights.

The main idea was to create a simple and practical system where users can track their income and expenses, apply filters, and view analytics like totals and category-wise breakdowns.

While building this, I focused on understanding how real backend systems are structured — including authentication, role-based access control, and clean separation between routes, services, and models.

---

## ⚙️ Features

- User authentication using JWT (access + refresh tokens)
- Create, update, delete, and view financial transactions
- Filter transactions by type, date range, and category
- Analytics:
  - Total income and expenses
  - Current balance
  - Category-wise breakdown (with percentages)
  - Monthly summaries
- Role-based access control:
  - Viewer → manage own transactions  
  - Analyst → access analytics  
  - Admin → system-level access  
- Input validation using Pydantic  
- Global error handling for clean API responses  
- Structured logging for debugging and monitoring  
- Rate limiting on sensitive endpoints (like login)  

---

## 🛠️ Tech Stack

- FastAPI  
- SQLAlchemy (PostgreSQL / SQLite for testing)  
- Pydantic  
- Alembic (database migrations)  
- JWT (authentication)  
- bcrypt (password hashing)  
- Docker & docker-compose  
- Pytest (testing)  

---

## 🚀 How to Run

### 🔹 Option 1: Using Docker

1. Copy `.env.example` to `.env`
2. Set `SECRET_KEY` (example: `openssl rand -hex 32`)
3. Set database credentials (e.g., `POSTGRES_PASSWORD`)
4. Run:

```bash
docker-compose up --build

## How to Run

### With Docker (easiest)

1. Copy `.env.example` to `.env` and set `SECRET_KEY` (use `openssl rand -hex 32`) and `POSTGRES_PASSWORD`
2. Run `docker-compose up --build`
3. API at http://localhost:8000/api/v1/docs (Swagger UI)
4. Seed data: `docker-compose exec app python seed.py`

### Local Python

1. `python -m venv venv; source venv/bin/activate`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`, set `SECRET_KEY`
4. `python seed.py`
5. `uvicorn app.main:app --reload`

Default login: admin@example.com / admin123 (admin role)

## API Documentation

Interactive docs at `/api/v1/docs` or `/api/v1/redoc`.

Quick examples:

**Login:**
```
curl -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=admin@example.com" -F "password=admin123"
```

**Create transaction (use your token):**
```
curl -X POST http://localhost:8000/api/v1/transactions/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": "100.50", "type": "income", "category": "Salary"}'
```

**Analytics (analyst/admin only):**
```
curl http://localhost:8000/api/v1/analytics/report \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Endpoints: /auth, /users, /transactions, /analytics, /admin/stats

## Learning and Future Improvements

I learned a ton building this: proper dependency injection for RBAC, caching analytics to avoid slow queries, and keeping services separate from routes. Next, I'd add real-time updates with WebSockets, more analytics like trends over time, file uploads for bank statements, and deploy to a cloud like Railway or Vercel with proper secrets.

Run `make test` to check everything works.

