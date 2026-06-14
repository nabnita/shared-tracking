# Expense Import Service

A production-quality full-stack expense management application that imports expense CSVs, detects data anomalies, stores cleaned data, and provides visibility into import decisions.

## Architecture

```
shared-tracking/
├── backend/          # Python + FastAPI + SQLAlchemy + PostgreSQL
├── frontend/         # React + Vite + TypeScript + TailwindCSS
├── docs/             # Architecture, ERD, anomaly analysis
└── docker-compose.yml
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic |
| Database | PostgreSQL 16 |
| Frontend | React 18, Vite 5, TypeScript, TailwindCSS 3 |
| Containerization | Docker Compose |
| Deployment | Render |

## Local Setup

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.12+

### 1. Clone the repository

```bash
git clone <repo-url>
cd shared-tracking
```

### 2. Configure environment variables

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 3. Start with Docker Compose

```bash
docker compose up --build
```

This starts:
- PostgreSQL on port 5432
- Backend API on http://localhost:8000
- Frontend on http://localhost:5173

### 4. Run migrations

```bash
cd backend
alembic upgrade head
```

### 5. API Documentation

FastAPI auto-generates OpenAPI docs at: http://localhost:8000/docs

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Sync PostgreSQL URL (Alembic) | `postgresql://expense_user:expense_pass@localhost:5432/expense_db` |
| `ASYNC_DATABASE_URL` | Async PostgreSQL URL (FastAPI) | `postgresql+asyncpg://...` |
| `SECRET_KEY` | Application secret | — |
| `ENVIRONMENT` | `development` or `production` | `development` |
| `ALLOWED_ORIGINS` | CORS origins | `http://localhost:5173` |

### Frontend (`frontend/.env`)

| Variable | Description | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000/api/v1` |

## Development

### Backend only

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend only

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
cd backend
pytest --cov=app tests/ --cov-report=term-missing
```

## Deployment

See [docs/deployment.md](docs/deployment.md) — updated after Phase 12.

---

*See [SCOPE.md](SCOPE.md), [DECISIONS.md](DECISIONS.md), and [AI_USAGE.md](AI_USAGE.md) for full documentation.*
