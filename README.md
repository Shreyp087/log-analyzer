# Log Analyzer

## Project Overview

Log Analyzer is a full-stack cybersecurity take-home project that ingests Zscaler-style logs, stores normalized events, detects anomalies, and renders analyst-facing summaries and findings.

Current implementation includes:
- Authenticated workflow (register/login -> upload -> analysis)
- PostgreSQL persistence for users, uploads, events, anomalies, and summaries
- Rule-based anomaly detection with confidence/severity
- Next.js dashboard, upload UI, and analysis display

## Chosen Stack

- Frontend: Next.js 14 (TypeScript, App Router)
- Backend: Flask + Flask-SQLAlchemy + Flask-Migrate + Flask-JWT-Extended
- Database: PostgreSQL 16 (Docker Compose)
- Local file storage: `backend/uploads`

## Architecture

1. **Frontend UI**
- `/register` and `/login` for authentication
- `/dashboard` as authenticated home
- `/upload` for log ingestion
- `/analysis/[id]` for summary + timeline + anomalies + findings

2. **API Layer**
- Auth routes for register/login/current-user
- Upload route for file ingestion and analysis pipeline execution

3. **Processing Layer**
- Parser normalizes raw Zscaler lines into structured event fields
- Summary service computes aggregate metrics
- Anomaly service applies deterministic security rules

4. **Persistence Layer**
- PostgreSQL stores all core entities
- Raw uploaded files are saved to local upload directory

## Setup

### Prerequisites

- Docker Desktop (or Docker Engine)
- Python 3.11+ with `venv`
- Node.js 18+ and npm

### 1. Start PostgreSQL

From repository root:

```powershell
docker compose up -d postgres
```

### 2. Configure and Run Backend

```powershell
cd backend
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m flask --app run.py db upgrade
python run.py
```

Backend base URL: `http://localhost:8000`  
Health check: `GET http://localhost:8000/health`

### 3. Configure and Run Frontend

In a separate terminal:

```powershell
cd frontend
npm install
@"
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
"@ | Set-Content .env.local
npm run dev
```

Frontend URL: `http://localhost:3000`

## API Endpoints

### Health

- `GET /health`  
Returns service readiness.

### Auth

- `POST /auth/register`  
Body: `{ "email": "user@example.com", "password": "StrongPass123" }`

- `POST /auth/login`  
Body: `{ "email": "user@example.com", "password": "StrongPass123" }`

- `GET /auth/me`  
Requires Bearer JWT token.

### Upload + Analysis

- `POST /uploads`  
Requires Bearer JWT token and multipart form data:
  - `file` (log file)
  - `source` (currently `zscaler`)

Returns:
- upload metadata
- parse error preview
- summary metrics
- anomaly list
- `events_preview` for timeline display

## Anomaly Explanation

Anomaly detection is currently rule-based (`backend/app/services/anomaly.py`):

1. `blocked_request`
- Trigger: action is `BLOCK`

2. `suspicious_destination`
- Trigger: destination contains threat keywords  
Keywords: `malicious`, `phish`, `command-and-control`, `cnc`, `tor`, `darkweb`

3. `zero_byte_allowed_request`
- Trigger: action is `ALLOW` or `PERMIT` and bytes transferred is `0`

4. `excessive_data_transfer`
- Trigger: bytes transferred >= `50,000,000`

Each anomaly includes:
- `anomaly_type`
- `description`
- `confidence` (0-1)
- `severity` derived from confidence

## Where AI Is Used

Current runtime behavior in this repo is deterministic and does **not** require an external LLM call to function.

AI is used in this project in two ways:

1. Development acceleration
- Assisted scaffold/code generation and documentation drafting.

2. Extension point (future)
- The summary/findings layer can be upgraded with LLM-generated narrative explanations, but this is not mandatory for current execution.

## Sample Credentials

There is no seeded default user. Create one at `/register`.

For demo purposes, you can use:
- Email: `analyst.demo@company.com`
- Password: `StrongPass123`

If this user already exists in your local DB, use `/login` with the same credentials.

## Sample Log Details

### 1. Baseline sample
- File: `sample_logs/sample_zscaler.log`
- Purpose: clean, small dataset for parser sanity checks.

### 2. Suspicious demo sample
- File: `sample_logs/suspicious_zscaler.log`
- Purpose: concentrated anomaly triggers for demo walkthrough.
- Contains examples of:
  - blocked suspicious destinations
  - zero-byte allowed requests
  - high-volume transfers
  - threat-keyword destination matches

### 3. Legacy CSV samples
- `sample_logs/normal_traffic.csv`
- `sample_logs/suspicious_traffic.csv`

## Build Checklist

- [x] Stage 1: foundation and canonical sample
- [x] Stage 2: backend shell
- [x] Stage 3: data model + migrations
- [x] Stage 4: minimum API (health + auth)
- [x] Stage 5: parser + normalizer
- [x] Stage 6: upload + summary flow
- [x] Stage 7: anomaly detection
- [x] Stage 8: frontend shell
- [x] Stage 9: frontend auth
- [x] Stage 10: frontend upload flow
- [x] Stage 11: analysis display
- [x] Stage 12: final polish and demo docs

## Documentation

- [docs/Workflow.md](docs/Workflow.md)
- [docs/Decision_Log.md](docs/Decision_Log.md)
- [docs/demo-script.md](docs/demo-script.md)
