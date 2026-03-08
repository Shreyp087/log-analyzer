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

### One-command Docker run (frontend + backend + postgres)

From repository root:

```powershell
docker compose up --build
```

Services:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

Notes:
- Backend runs migrations automatically on container start (`flask db upgrade`).
- `backend/.env` is loaded in the backend container (for keys like `OPENAI_API_KEY`).

### Manual local run (without Docker for app services)

#### 1. Start PostgreSQL

From repository root:

```powershell
docker compose up -d postgres
```

#### 2. Configure and Run Backend

```powershell
cd backend
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m flask --app run.py db upgrade
python run.py
```

Backend base URL: `http://127.0.0.1:8000`

#### 3. Configure and Run Frontend

In a separate terminal:

```powershell
cd frontend
npm install
@"
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
"@ | Set-Content .env.local
npm run dev
```

Use `http://127.0.0.1:8000` instead of `localhost` to avoid Windows IPv6 loopback conflicts where another service can intercept `localhost:8000`.

Frontend URL: `http://localhost:3000`

## API Endpoints

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

### AI-Assisted Anomaly Detection (Brief)

In addition to deterministic rules, the backend now runs an unsupervised AI detector (`backend/app/services/ai_anomaly.py`) using **Isolation Forest**:
- Model type: `IsolationForest` (outlier detection on unlabeled traffic)
- Input features: bytes, action flags, category risk flags, suspicious destination signals, hour-of-day, and per-entity frequency ratios (source/user/destination)
- Trigger policy: enabled only when dataset size is at least 30 events (to avoid unstable baselines)
- Output: `ai_behavioral_outlier` findings with confidence, severity, explanation, and `detectionMethod=ai_isolation_forest`

Final anomaly output is hybrid: rule findings remain primary, while AI contributes behavioral outliers as a secondary signal.

## AI & Detection Methodology

### OpenAI Executive Summary
- Endpoint: `POST https://api.openai.com/v1/chat/completions`
- Model: `gpt-4o-mini` with `response_format: { type: "json_object" }`
- Generation controls: `temperature: 0.2` for consistent factual output
- Prompt input (structured): `{ totalEvents, blockedCount, blockRate, anomalies[], topSourceIPs[], topCategories[], threatsDetected }`
- Returned JSON: `{ riskLevel, executiveSummary, keyFindings[], recommendations[], immediateActions[] }`
- Failure handling: if API key is missing, rate-limited, or request fails, backend uses a deterministic fallback that returns the **same JSON shape**.
- Estimated cost: `~$0.0002` per analysis (negligible for this scope)

> Fallback risk is derived from blockRate thresholds and anomaly severity counts, so UI rendering is identical whether OpenAI is available or not.

### Statistical / Algorithmic Detection (Non-LLM)
- Z-score formula: `z = (x - mu) / sigma` on normalized aggregates (per-IP frequency, outbound volume).
- Temporal burst logic: sliding 60s windows compare current request burst vs entity baseline.
- Volume baseline: compares outbound bytes vs peer-group baseline to detect exfiltration outliers.
- Alerting uses these methods because they are deterministic, auditable, and non-hallucinatory.

| Algorithm | Method | Detects | Example |
|---|---|---|---|
| Z-Score Frequency | Statistical (μ, σ on per-IP counts) | Brute force, DoS | 11 POST /login in 11 seconds from 10.0.0.5 |
| Temporal Burst | Sliding 60s window, max burst count | Credential stuffing | 6 requests/minute vs baseline of 1 |
| Volume Baseline | Z-score on outbound bytes per entity | Data exfiltration | 70MB sent to Dropbox vs 2KB group mean |
| Threat Signature | Keyword + category field matching | Known malware/C2/phishing | action=ALLOW, category=Malware, url=c2.* |
| Policy Violation | Per-entity BLOCK event frequency | Insider threat, bypass | 3 blocked requests across Malware + Phishing |
| Destination Fan-out | Unique dest IP count per source IP | Lateral movement, scanning | 1 IP contacting 6 unique destinations |

### Confidence Score Methodology
- Scores are computed from explicit signals (action, category risk, byte volume, destination indicators, temporal deviation), not arbitrary constants.
- Each detector has bounded boosts/penalties and severity mapping thresholds.
- Confidence is capped to avoid overstatement from one strong signal.

### Limitations (Current Dataset Size)
- Small samples reduce z-score reliability.
- Benign batch jobs can mimic burst/exfil patterns.
- Sparse category labels reduce signature precision.

> LLM output (`gpt-4o-mini`) is used for narrative synthesis only. Detection logic is produced by deterministic rules plus the auditable Isolation Forest outlier model.

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
