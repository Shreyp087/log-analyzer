# Log Analyzer

## Project Overview

Log Analyzer ingests network and security logs, parses key fields, detects anomalies, and prepares summary outputs for analyst review.

Current scope includes Stage 1 foundation, Stage 2 backend shell bootstrapping, and Stage 3 data model + migrations.

## Chosen Stack

- Frontend: TypeScript-based web app (implementation pending)
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

### Frontend Setup

TBD in Phase 2.

## Build Checklist

- [x] Stage 1: README foundation skeleton
- [x] Stage 1: PostgreSQL-only `docker-compose.yml`
- [x] Stage 1: canonical sample log (`sample_logs/sample_zscaler.log`)
- [x] Stage 2: backend shell (`run.py`, app factory, config, env template)
- [x] Stage 3: data model + initial migrations
- [ ] Stage 4: parser implementation against sample logs
- [ ] Stage 5: anomaly detection module
- [ ] Stage 6: summarization pipeline
- [ ] Stage 7: API and frontend integration

## Documentation Workflow

- [docs/Workflow.md](docs/Workflow.md): execution steps and rationale format
- [docs/Decision_Log.md](docs/Decision_Log.md): alternatives, trade-offs, and decisions
