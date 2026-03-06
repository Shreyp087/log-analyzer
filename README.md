# Log Analyzer

Project scaffold for a log-analysis application with separate frontend and backend services.

## Structure

- `frontend/`: frontend app shell (`app`, `components`, `lib`, `package.json`)
- `backend/`: Python API and analysis services
- `sample_logs/`: sample CSV datasets for testing
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
