# Log Analyzer

## Project Overview

Log Analyzer ingests network and security logs, parses key fields, detects anomalies, and prepares summary outputs for analyst review.

Current scope includes Stage 1 foundation, Stage 2 backend shell bootstrapping, Stage 3 data model + migrations, Stage 4 minimum working API routes, Stage 5 parsing layer services, Stage 6 upload + summary flow, Stage 7 anomaly detection, Stage 8 frontend shell, Stage 9 frontend auth layer, Stage 10 upload UI workflow, and Stage 11 analysis display.

## Chosen Stack

- Frontend: Next.js (TypeScript, App Router)
- Backend API and services: Python
- Database: PostgreSQL (Docker Compose for local consistency)
- Data source format: line-based log files in `sample_logs/`

## Architecture Summary

- Ingestion layer: reads raw log lines from sample or uploaded files.
- Parsing layer: normalizes log lines into structured records.
- Detection layer: applies anomaly rules over normalized records.
- Summary layer: produces aggregates and human-readable findings.
- Persistence layer: stores processed records and metadata in PostgreSQL.

## Setup (Placeholder)

### Local Development Setup

TBD in Phase 2.

### Environment Configuration

TBD in Phase 2.

### Backend Setup

1. Copy env template:
   - `cd backend`
   - `cp .env.example .env` (Linux/macOS)
   - `Copy-Item .env.example .env` (PowerShell)
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run migrations:
   - `python -m flask --app run.py db upgrade`
4. Start app:
   - `python run.py`
5. Verify core routes:
   - `GET /health`
   - `POST /auth/register`
   - `POST /auth/login`
   - `GET /auth/me` (Bearer token)
   - `POST /uploads` (Bearer token + multipart file)
6. Parser modules:
   - `backend/app/services/parser.py`
   - `backend/app/services/normalizer.py`
7. Upload/summary modules:
   - `backend/app/routes/uploads.py`
   - `backend/app/services/storage.py`
   - `backend/app/services/summary.py`
8. Anomaly modules:
   - `backend/app/services/anomaly.py`
   - `backend/app/services/scoring.py`
9. Frontend auth modules:
   - `frontend/lib/api.ts`
   - `frontend/lib/auth.ts`
   - `frontend/types/index.ts`
   - `frontend/components/LoginForm.tsx`
   - `frontend/app/login/page.tsx`
10. Frontend upload modules:
    - `frontend/app/dashboard/page.tsx`
    - `frontend/app/upload/page.tsx`
    - `frontend/components/UploadDropzone.tsx`
11. Frontend analysis modules:
    - `frontend/app/analysis/[id]/page.tsx`
    - `frontend/components/SummaryCards.tsx`
    - `frontend/components/TimelineTable.tsx`
    - `frontend/components/AnomaliesTable.tsx`
    - `frontend/components/FindingsPanel.tsx`

### Frontend Setup

1. Move into frontend:
   - `cd frontend`
2. Install dependencies:
   - `npm install`
3. Start dev server:
   - `npm run dev`
4. Open:
   - `http://localhost:3000`

## Build Checklist

- [x] Stage 1: README foundation skeleton
- [x] Stage 1: PostgreSQL-only `docker-compose.yml`
- [x] Stage 1: canonical sample log (`sample_logs/sample_zscaler.log`)
- [x] Stage 2: backend shell (`run.py`, app factory, config, env template)
- [x] Stage 3: data model + initial migrations
- [x] Stage 4: minimum working API (`health`, `auth`)
- [x] Stage 5: parser implementation against sample logs
- [x] Stage 6: upload and summary flow
- [x] Stage 7: anomaly detection module
- [x] Stage 8: frontend shell
- [x] Stage 9: frontend auth layer
- [x] Stage 10: upload UI workflow
- [x] Stage 11: analysis display workflow

## Documentation Workflow

- [docs/Workflow.md](docs/Workflow.md): execution steps and rationale format
- [docs/Decision_Log.md](docs/Decision_Log.md): alternatives, trade-offs, and decisions
