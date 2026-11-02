# Declairo

A personal project for tracking cryptocurrency transactions and estimating taxes. It brings transaction imports, portfolio views, reconciliation, and report exports into one web application.

## Features

- Import transactions from CSV files, exchanges, and blockchain wallets.
- View portfolio balances and transaction history.
- Calculate cost basis, gains, and losses.
- Reconcile transactions and prepare tax reports.

Work in progress. Calculations require independent verification and do not replace professional tax advice.

## Tech stack

**Frontend:** React, TypeScript, Vite, Tailwind CSS, TanStack Query, Recharts.

**Backend:** Python, FastAPI, SQLAlchemy, Alembic, CCXT. SQLite is used for local development; the project also includes PostgreSQL, Redis, and Docker Compose configuration.

## Run locally

Prerequisites: Python 3.11+ and Node.js 22.12+. Run the following commands in PowerShell from the project root.

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item .env.example backend/.env
.\.venv\Scripts\python.exe backend/scripts/generate_secrets.py
```

Copy the generated `JWT_SECRET_KEY` and `ENCRYPTION_KEY` into `backend/.env`. External integrations require your own API credentials and can be configured separately.

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.api.server:app --reload
```

Development mode creates the SQLite tables on startup. API documentation: <http://localhost:8000/docs>.

### Frontend

In another terminal, from the project root:

```powershell
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` requests to the local backend.

## Project structure

- `frontend/` — web interface.
- `backend/app/` — API, calculations, and integrations.
- `backend/migrations/` — database migrations.
- `backend/app/tests/` — backend tests.
- `docs/` — additional documentation.

## Configuration

Only `.env*.example` templates belong in the repository. Local configuration, private keys, databases, backups, and generated reports are excluded through `.gitignore`. Set deployment secrets through environment variables. `VITE_*` values are public in the browser and must never contain private credentials.

## Tests

Install the backend test dependencies, then run the same coverage gate as CI:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-test.txt
cd backend
..\.venv\Scripts\python.exe -m pytest --cov=app --cov-config=.coveragerc --cov-fail-under=65
```

Frontend checks (from `frontend/`): `npm run typecheck`, `npm test -- --run`, and `npm run build`.
