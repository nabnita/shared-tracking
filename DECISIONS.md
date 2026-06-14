# Decision Log

This document outlines the significant architectural and design decisions made during the development of the Expense Import Service, the options considered, and the rationale behind the final choices.

---

### 1. Architectural Pattern
**Decision:** Build a Modular Monolith (FastAPI + React/Vite) rather than a Microservices architecture.
- **Options Considered:**
  1. Microservices (Ingestion Service, Query Service, Frontend)
  2. Serverless (AWS Lambda / Vercel Functions)
  3. Modular Monolith
- **Why chosen:** Given the scope of a single CSV parsing pipeline with high relational coupling (expenses tied to participants tied to reports), microservices would introduce unnecessary network latency and deployment complexity. A monolithic FastAPI backend provides type safety, high performance (async), and an extremely straightforward local development experience via Docker Compose.

### 2. Frontend Framework
**Decision:** Use React + Vite + TypeScript + Tailwind CSS instead of server-side rendered HTML (Jinja2).
- **Options Considered:**
  1. FastAPI Jinja2 Templates + Bootstrap (Server-Side Rendering)
  2. Next.js (Fullstack React)
  3. React SPA (Vite) + Tailwind CSS
- **Why chosen:** Handling asynchronous file uploads, paginated tables, and interactive anomaly reports requires complex DOM state management. React handles this seamlessly. Vite was chosen over Next.js because this app doesn't require SEO, and deploying a lightweight static SPA decoupled from the backend is cheaper and faster on platforms like Railway.

### 3. Database ORM & Paradigm
**Decision:** Use SQLAlchemy 2.0 (Async) with PostgreSQL.
- **Options Considered:**
  1. Raw AsyncPG SQL strings.
  2. Prisma (Python Client).
  3. SQLAlchemy 2.0 (Async Session).
- **Why chosen:** SQLAlchemy 2.0 introduces strong typing that pairs perfectly with Pydantic and FastAPI. It prevents SQL injection inherently and provides an excellent migration system (`alembic`). Raw SQL would make participant share calculations overly verbose, while Prisma for Python is still relatively immature compared to SQLAlchemy's ecosystem.

### 4. Anomaly Detection Engine Design
**Decision:** Implement the rule engine as a pipeline of pure, stateless functions rather than stateful classes.
- **Options Considered:**
  1. Stateful object-oriented validators (`Validator.feed(row)`).
  2. Stateless pure functional pipeline mapping `NormalizedRow` to `RowDecision`.
- **Why chosen:** Pure functions (`NormalizedRow -> list[Anomaly]`) are infinitely easier to unit test. We can pass mock rows into a rule without worrying about the database state or previous rows. The pipeline orchestrator handles the state accumulation, leaving the rules purely functional.

### 5. Error Handling Philosophy (Fail-Safe Import)
**Decision:** A malformed row in the CSV does *not* crash or abort the import.
- **Options Considered:**
  1. **Fail-Fast**: If Row 10 is malformed, reject the entire CSV and rollback the database transaction.
  2. **Fail-Safe**: Import all valid rows, categorize malformed rows as `REJECTED`, and questionable rows as `WARNING`, saving everything.
- **Why chosen:** In real-world accounting, CSVs from different banks always have formatting quirks. Rejecting a 5,000-row file because row 4,000 has a missing date causes extreme user frustration. The fail-safe approach imports what it can and provides an interactive dashboard (`Anomalies` view) for the user to manually reconcile the broken rows later.

### 6. Deployment Strategy
**Decision:** Dockerize both services but decouple them for Railway.
- **Options Considered:**
  1. Single Docker container running Nginx for the frontend and Uvicorn for the backend via Supervisord.
  2. Two distinct Docker containers communicating via network URLs.
- **Why chosen:** Decoupling allows the frontend to be scaled or rebuilt infinitely without restarting the database connections of the backend. We utilized Nginx multi-stage builds for the frontend and a robust `start.sh` script for the backend to automatically handle Alembic database migrations on startup.
