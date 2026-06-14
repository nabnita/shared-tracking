# Expense Import Service

A full-stack web application designed to safely ingest, normalize, and audit complex, messy expense CSVs. It features a robust anomaly detection engine that flags inconsistencies without aborting imports, ensuring maximum data retention.

## Features
- **Fail-Safe Ingestion:** Malformed CSV rows generate warnings/errors but do not block valid rows from importing.
- **Anomaly Detection:** Automatically flags duplicate transactions, ambiguous dates, formatting issues, percentage splits that don't equal 100%, and more.
- **Auto-Categorization:** Infers Refunds and Settlements based on negative amounts and description keywords.
- **Rich Dashboard:** A React/Vite UI that provides detailed reports on every imported CSV.

## AI Usage Acknowledgment
**This project was heavily scaffolded and assisted by AI.**
- **AI Agent:** Antigravity IDE (Gemini 3.1 Pro)
- Please see the `AI_USAGE.md` file for details on the exact prompts used, tools utilized, and concrete instances where the AI made mistakes that required human intervention.

## Documentation
- `SCOPE.md`: Contains the Anomaly Log (every data problem found in the CSV and how it was handled) and the Database Schema.
- `DECISIONS.md`: The decision log explaining significant architectural choices.
- `AI_USAGE.md`: Details the AI usage and debugging process.
- `import_report.json`: An example JSON payload produced by the application when it ingests the `Expenses Export.csv`.

---

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Node.js (v20+) & Python (3.12+) (if running bare-metal)

### 1. Running Locally (Docker Compose)
The easiest way to run the entire stack locally is using Docker Compose. This automatically spins up the PostgreSQL database, the FastAPI backend, and the React frontend.

```bash
# Start all services
docker-compose up -d --build
```

- **Frontend UI:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000`
- **API Docs (Swagger):** `http://localhost:8000/docs`

*Note: Alembic database migrations run automatically when the backend container starts.*

### 2. Running Locally (Bare Metal)

#### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start local postgres (or use your own)
docker-compose up -d postgres

# Run database migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Deploying to Railway
This project is configured to be deployed natively on Railway with zero configuration needed for building.

1. **Create a PostgreSQL database** in your Railway project.
2. **Deploy the Backend:** Connect your GitHub repo, select the `/backend` folder as the root directory. Railway will automatically detect the Dockerfile.
   - Add the variable `DATABASE_URL` pointing to your Railway Postgres database.
   - Add the variable `PORT` to bind to.
3. **Deploy the Frontend:** Connect your GitHub repo again, select the `/frontend` folder as the root directory.
   - Add the variable `VITE_API_URL` pointing to your deployed backend URL (e.g. `https://your-backend.up.railway.app/api/v1`).
   - Railway will natively inject this variable into the Docker build phase and serve the React app via Nginx.
