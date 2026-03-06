# Log Analyzer

## Project Overview

Log Analyzer ingests network and security logs, parses key fields, detects anomalies, and prepares summary outputs for analyst review.

Current scope is Stage 1 project foundation: baseline documentation, local database container, and canonical sample log input.

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

TBD in Phase 2.

### Frontend Setup

TBD in Phase 2.

## Build Checklist

- [x] Stage 1: README foundation skeleton
- [x] Stage 1: PostgreSQL-only `docker-compose.yml`
- [x] Stage 1: canonical sample log (`sample_logs/sample_zscaler.log`)
- [ ] Stage 2: parser implementation against sample logs
- [ ] Stage 3: anomaly detection module
- [ ] Stage 4: summarization pipeline
- [ ] Stage 5: API and frontend integration

## Documentation Workflow

- [docs/Workflow.md](docs/Workflow.md): execution steps and rationale format
- [docs/Decision_Log.md](docs/Decision_Log.md): alternatives, trade-offs, and decisions
