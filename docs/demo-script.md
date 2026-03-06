# Demo Script

## Goal

Provide a clean, interview-ready walkthrough of the Log Analyzer application from setup to anomaly insights.

## 1. Opening (30-45 seconds)

1. Introduce the project:
- "This is a full-stack log analysis platform for Zscaler-style traffic logs."
- "It supports authentication, ingestion, normalization, anomaly detection, and analyst-friendly result views."

2. Clarify scope:
- "The project is structured in progressive stages from foundation to final polish."

## 2. Environment Setup (45-60 seconds)

1. Show services:
- Start PostgreSQL with `docker compose up -d postgres`.
- Start backend with `python run.py`.
- Start frontend with `npm run dev`.

2. Show readiness checks:
- `GET /health` returns `{"status":"ok"}`.
- Open frontend at `http://localhost:3000`.

## 3. Auth Flow (45-60 seconds)

1. Open `/register`.
2. Create demo user:
- Email: `analyst.demo@company.com`
- Password: `StrongPass123`
3. Confirm redirect to dashboard.
4. Mention JWT-based protected route flow (`/auth/me`, `/uploads` require token).

## 4. Upload and Analysis Flow (60-90 seconds)

1. Navigate to `/upload`.
2. Upload `sample_logs/suspicious_zscaler.log`.
3. Call out upload response metrics:
- events saved
- anomalies detected
- blocked events
- unique IPs
4. Click "View Full Analysis".

## 5. Analysis Page Breakdown (90-120 seconds)

Walk top-to-bottom:

1. `SummaryCards`
- high-level KPI snapshot.

2. `TimelineTable`
- parsed event preview with action/category/destination/bytes.

3. `AnomaliesTable`
- anomaly type, severity, confidence, and explanation.

4. `FindingsPanel`
- concise analyst narrative for quick interpretation.

## 6. Anomaly Logic Explanation (60 seconds)

Explain the four rule groups:

1. `blocked_request`
2. `suspicious_destination` (keyword-based)
3. `zero_byte_allowed_request`
4. `excessive_data_transfer`

Then note:
- confidence scoring is centralized in `scoring.py`
- severity is derived from confidence

## 7. Architecture and Trade-offs (60-90 seconds)

1. Architecture summary:
- Next.js frontend
- Flask API
- PostgreSQL persistence
- service-layer parser/summary/anomaly modules

2. Key trade-offs:
- Chose service modules over inline route logic for maintainability.
- Chose rule-based anomaly detection now for determinism and explainability.
- Chose staged backend-first approach to stabilize contracts before frontend.

## 8. Where AI Is Used (30-45 seconds)

1. Current runtime is deterministic (no mandatory external LLM dependency).
2. AI was used as development acceleration for scaffolding/documentation.
3. Future extension: AI-generated narrative summaries over anomaly/event context.

## 9. Closing (20-30 seconds)

1. Recap:
- "End-to-end flow works from auth to actionable analysis."
2. Optional next steps:
- add `GET /uploads/{id}` retrieval endpoint
- improve role-based access
- introduce streaming or large-file batch processing
