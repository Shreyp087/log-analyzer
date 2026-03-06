# Log Analyzer

Project scaffold for a log-analysis application with separate frontend and backend services.

## Documentation Workflow

To keep execution and reasoning interview-ready, use:

- `docs/WORKFLOW.md` for step-by-step execution standards
- `docs/DECISION_LOG.md` to record approach alternatives, trade-offs, and rationale

## Structure

- `frontend/`: frontend app shell (`app`, `components`, `lib`, `package.json`)
- `backend/`: Python API and analysis services
- `sample_logs/`: sample CSV datasets for testing
- `docs/`: workflow standard and decision records
- `docker-compose.yml`: local multi-service runtime template

## Quick Start

1. Backend
   - `cd backend`
   - `pip install -r requirements.txt`
   - `python app.py`
2. Frontend
   - `cd frontend`
   - `npm install`
   - `npm run dev`
