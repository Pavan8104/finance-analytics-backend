# AI-Ready Finance Analytics Backend System

## 🚀 Overview
The AI-Ready Finance Analytics Backend System is a robust, production-ready, RESTful API built with **FastAPI** to manage personal or enterprise financial transactions. It demonstrates clean architecture, scalable design patterns, and high-performance querying. This project serves as a comprehensive showcase of modern Python backend engineering.

## 🛠 Tech Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL (Production) / SQLite (Local/Fallback)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Authentication**: JWT (JSON Web Tokens) with Passlib & Bcrypt
- **Caching**: In-Memory TTL Cache (cachetools) for Analytics
- **Containerization**: Docker & Docker Compose

## 🎯 Key Features
- **Authentication & RBAC**: Secure JWT-based login with Admin, Analyst, and Viewer roles.
- **Transaction Management**: Efficient CRUD operations for managing income and expenses.
- **Advanced Filtering**: Filter transactions by date range, category, and type along with offset/limit pagination.
- **Analytics Engine**: Real-time aggregation of financial metrics (Total Income, Expenses, Balance, Category breakdowns).
- **In-Memory Caching**: Implements `TTLCache` on heavy analytics operations to reduce database load.
- **Clean Architecture**: Strong separation of concerns across models, schemas, services, and API layers.

## 📁 Project Structure
```text
.
├── app/
│   ├── api/             # Routers & API endpoints
│   ├── core/            # Configs, deps, and DB connection
│   ├── models/          # SQLAlchemy Models
│   ├── schemas/         # Pydantic validation schemas
│   ├── services/        # Business logic layer
│   ├── utils/           # Helper scripts (Logging)
│   └── main.py          # FastAPI application entrypoint
├── requirements.txt     # Python dependencies
├── Dockerfile           # Multistage build script
├── docker-compose.yml   # Stack composition
├── .env.example         # Environment template
└── seed.py              # Script to bootstrap the base state
```

## ⚙️ Getting Started

### Option 1: Docker (Recommended)
1. Clone the repository and navigate into it.
2. Build and start the services:
   ```bash
   docker-compose up --build
   ```
3. The API will be available at `http://localhost:8000`.

### Option 2: Local Environment (SQLite)
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` (Optional, defaults to SQLite via `finance.db`):
   ```bash
   cp .env.example .env
   ```
3. Seed the database with mock data:
   ```bash
   python seed.py
   ```
4. Run the server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📖 API Documentation & Endpoints
FastAPI automatically generates interactive API documentation.
Navigate to the following URLs in your browser after starting the application:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Core Endpoints Overview
| HTTP Method | Endpoint | Description | Access | 
| ----------- | -------- | ----------- | ------ |
| `POST` | `/api/v1/auth/login` | Login and get JWT access token | Public |
| `POST` | `/api/v1/users/` | Create a new user (Sign-up) | Public |
| `GET` | `/api/v1/users/me` | Fetch detailed user info | Authenticated |
| `GET` | `/api/v1/transactions/` | Paginated and filtered transactions | Authenticated |
| `POST` | `/api/v1/transactions/` | Create a new transaction | Authenticated |
| `GET` | `/api/v1/analytics/report` | Cached financial insights and categories | Analyst/Admin |

## 💼 Why this is "Resume-Ready"
This project isn't just another checklist app. It covers essential complexities found in real enterprise backends:
1. **Security**: We don't just store passwords; we hash them with Bcrypt and manage stateless sessions via JWT.
2. **Architecture**: Keeping routes dumb (`api/endpoints`) and keeping logical operations contained (`services/`) ensures unit-testability and decoupled growth.
3. **Performance Awareness**: Using `cachetools` for dashboard numbers proves an understanding of when not to hammer a database.

---
_Designed using best practices to secure that interview!_
