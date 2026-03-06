# Workflow

## Purpose

This file tracks how each phase is executed, including alternatives, trade-offs, and rationale for interview-ready review.

## Global Workflow Rules

1. Define objective before writing code.
2. Document alternatives and trade-offs for each non-trivial step.
3. Validate file outputs after each step.
4. Keep changes scoped to the active phase.
5. Do not push to remote unless explicitly instructed.

## Phase 1: Project Foundation

Date: 2026-03-06

### Step 1: Create README skeleton first

Objective:
- Force architecture and setup clarity before implementation.

Approach chosen:
- Replaced `README.md` with a structured skeleton containing:
  - project overview
  - chosen stack
  - architecture summary
  - setup placeholders
  - build checklist

Alternative considered:
1. Write README at the end.

Trade-off:
- Writing at the end is faster short-term, but increases drift risk between implementation and intent.

Why this choice:
- Early README anchors decisions and keeps the team aligned while coding begins.

Validation:
- Confirmed `README.md` includes all requested sections.

Outcome:
- Stage 1 documentation baseline established before coding expansion.

### Step 2: Start docker-compose with PostgreSQL only

Objective:
- Provide consistent local database setup from day one.

Approach chosen:
- Reduced `docker-compose.yml` to a single `postgres` service with:
  - fixed local port mapping `5432:5432`
  - persistent named volume
  - baseline credentials for local development

Alternative considered:
1. Use developer-local PostgreSQL installation.

Trade-off:
- Local install has less immediate setup in repo files, but weaker portability and environment consistency.

Why this choice:
- Compose-based DB setup reduces "works on my machine" failures and standardizes onboarding.

Validation:
- Confirmed compose file contains only the PostgreSQL service and volume definition.

Outcome:
- Portable, reproducible local DB baseline established.

### Step 3: Add canonical sample log file early

Objective:
- Provide parser source-of-truth input from the start.

Approach chosen:
- Added `sample_logs/sample_zscaler.log` with a small clean set of representative entries.

Alternative considered:
1. Add sample logs later during parser implementation.

Trade-off:
- Delaying sample logs may save time now, but delays parser design and creates ambiguity in expected input format.

Why this choice:
- Early canonical sample makes parser behavior and field expectations explicit.

Validation:
- Confirmed sample file exists and includes normalized line structure.

Outcome:
- Parser design can proceed with concrete input assumptions.

## Phase 2: Backend Shell

Date: 2026-03-06

### Step 4: Expand backend dependencies (`requirements.txt`)

Objective:
- Define all packages needed for app boot, database integration, JWT, and migrations.

Approach chosen:
- Updated `backend/requirements.txt` with Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, `psycopg[binary]`, and `python-dotenv`.

Alternative considered:
1. Keep only Flask and add packages later.

Trade-off:
- Smaller initial dependency list, but repeated boot failures and fragmented setup in later steps.

Why this choice:
- A complete dependency baseline allows the backend shell to be installed and run as one unit.

Validation:
- Verified requirement entries include all Stage 2 dependency categories.

Outcome:
- Backend install contract is now explicit.

### Step 5: Add environment template (`.env.example`)

Objective:
- Make runtime configuration explicit and reproducible.

Approach chosen:
- Added `backend/.env.example` with app host/port, Flask mode, secret keys, JWT key, and DB URL.

Alternative considered:
1. Hardcode all config in Python files.

Trade-off:
- Fewer files at first, but weaker security hygiene and difficult environment switching.

Why this choice:
- Template-driven env config improves onboarding and separates code from secrets.

Validation:
- Confirmed all critical runtime variables are documented in a copy-ready template.

Outcome:
- Backend configuration is now discoverable and standardized.

### Step 6: Create runtime entrypoint (`run.py`)

Objective:
- Provide a single command target to start the backend.

Approach chosen:
- Added `backend/run.py` that instantiates the app via factory and runs using config-driven host/port/debug.

Alternative considered:
1. Keep startup logic directly inside package modules.

Trade-off:
- Slightly fewer files, but less clear launch boundary and harder migration to WSGI/ASGI commands later.

Why this choice:
- A dedicated entrypoint keeps startup behavior explicit and clean.

Validation:
- Verified `run.py` imports `create_app()` and starts the app from centralized config.

Outcome:
- Backend startup command is standardized.

### Step 7: Centralize configuration (`app/config.py`)

Objective:
- Remove scattered settings and enforce environment-based config.

Approach chosen:
- Added `backend/app/config.py` with `BaseConfig`, environment-specific classes, and a `get_config()` selector.

Alternative considered:
1. Inline all settings in app initialization.

Trade-off:
- Quicker initially, but higher coupling and poor maintainability as settings grow.

Why this choice:
- Central config reduces drift and keeps environment behavior predictable.

Validation:
- Confirmed config includes DB URI, secrets, app network settings, and dev/test/prod modes.

Outcome:
- Configuration behavior is centralized and extensible.

### Step 8: Build app factory shell (`app/__init__.py`)

Objective:
- Make backend boot cleanly with extension setup and route registration.

Approach chosen:
- Added app factory pattern in `backend/app/__init__.py`, initialized DB/JWT/Migrate extensions, and registered routes through `backend/routes`.

Alternative considered:
1. Single-file app (`app.py`) with inline setup.

Trade-off:
- Faster initial coding, but harder to scale cleanly across modules, tests, and migrations.

Why this choice:
- Factory pattern is cleaner for growth, testing, and future CLI/migration integration.

Validation:
- Added `backend/routes/__init__.py` and `backend/routes/health.py`.
- Removed legacy single-file `backend/app.py`.
- Ran syntax validation (`python -m compileall backend`) to confirm files compile.
- Attempted import boot check (`python -c "from app import create_app"` path-adjusted); local environment is missing installed dependencies, so full runtime boot was not executed yet.

Outcome:
- Backend shell is structured, modular, and ready for parser/upload logic next.

## Phase 3: Data Model

Date: 2026-03-06

### Step 9: Define application schema in `backend/app/models.py`

Objective:
- Create concrete persistence targets before parser and upload logic.

Approach chosen:
- Added `User`, `Upload`, `Event`, `Anomaly`, and optional `Summary` models in `backend/app/models.py`.
- Added foreign keys and relationships to reflect expected flow:
  - user -> uploads
  - upload -> events/anomalies/summary
  - event -> anomalies
- Updated app factory to import models before migration autogeneration.

Alternative considered:
1. Parse first and persist later.

Trade-off:
- Good for rapid prototyping, but creates weak schema planning and usually causes rework in routes/services.

Why this choice:
- Schema-first gives parser/routes a stable contract and improves architecture consistency.

Validation:
- Ran `python -m compileall backend` after model addition.

Outcome:
- Core domain entities now exist with a database-backed structure.

### Step 10: Generate migration artifacts after models exist

Objective:
- Create versioned schema history from defined models.

Approach chosen:
- Generated Flask-Migrate scaffolding and initial migration:
  - `python -m flask --app run.py db init`
  - `python -m flask --app run.py db migrate -m "create stage3 core tables"`
- Used temporary `DATABASE_URL=sqlite:///stage3_dev.db` for autogeneration in local environment.

Alternative considered:
1. Skip migrations and use `db.create_all()`.

Trade-off:
- Faster setup, but weaker production path and no versioned schema history.

Why this choice:
- Migrations create a reproducible, reviewable schema evolution path.

Validation:
- Confirmed generated file `backend/migrations/versions/97b56d461f28_create_stage3_core_tables.py` contains all Stage 3 tables and indexes.
- During validation, `psycopg2-binary` proved incompatible with this local Python runtime, so dependency was updated to `psycopg[binary]==3.2.13` and installation was re-validated successfully.
- Ran `python -m flask --app run.py db upgrade` against temporary SQLite URL to verify migration application end-to-end.
- Ran `python -m flask --app run.py db current` and confirmed head revision `97b56d461f28`.

Outcome:
- Initial migration baseline is now present and ready for `db upgrade`.

## Phase 4: Minimum Working API

Date: 2026-03-06

### Step 11: Add health route in `backend/app/routes/health.py`

Objective:
- Provide a zero-dependency endpoint that confirms app boot and route registration.

Approach chosen:
- Added `GET /health` returning `{ "status": "ok" }`.

Alternative considered:
1. Start directly with upload or parser routes.

Trade-off:
- Faster visible feature progress, but weaker base verification if startup/routing is broken.

Why this choice:
- Health route gives immediate operational confirmation and shortens debugging loop.

Validation:
- Verified `health_bp` registration in app route package.

Outcome:
- Minimal operational readiness endpoint is available.

### Step 12: Add auth routes in `backend/app/routes/auth.py`

Objective:
- Prove protected workflow path with register/login and token-based identity endpoint.

Approach chosen:
- Added endpoints:
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /auth/me` (JWT-protected)
- Routes integrate with `User` model and SQLAlchemy session.

Alternative considered:
1. Build upload route first.

Trade-off:
- Upload-first gives faster visible product value, but leaves auth design unresolved and increases refactor risk for protected endpoints later.

Why this choice:
- Authentication is foundational and should be settled before data-ingest workflows.

Validation:
- Executed Flask test-client flow for register -> login -> me using JWT access token.

Outcome:
- Minimum auth lifecycle is functional.

### Step 13: Add security helpers in `backend/app/utils/security.py`

Objective:
- Keep credential handling centralized and reusable.

Approach chosen:
- Added helper functions:
  - `hash_password()`
  - `verify_password()`

Alternative considered:
1. Inline password hashing logic inside route handlers.

Trade-off:
- Slightly fewer files now, but weaker separation of concerns and harder testing/reuse.

Why this choice:
- Small utility module keeps auth route logic focused and maintainable.

Validation:
- Verified auth routes call helper functions for both register and login flows.

Outcome:
- Password handling is encapsulated and ready for future security hardening.

## Phase 5: Parsing Layer

Date: 2026-03-06

### Step 14: Add Zscaler parser service in `backend/app/services/parser.py`

Objective:
- Convert raw Zscaler log lines into normalized fields aligned to the `Event` model contract.

Approach chosen:
- Added parser functions:
  - `parse_zscaler_line(raw_line)` for one-row parsing
  - `parse_zscaler_lines(lines)` for batch parsing with structured error collection
- Parser behavior:
  - ignores comments/blank lines
  - validates row shape
  - normalizes keys to `event_time`, `username`, `source_ip`, `destination`, `action`, `category`, `bytes_transferred`, and `raw_line`
  - raises/records explicit parse errors for invalid timestamp, invalid byte value, or malformed row

Alternative considered:
1. Put parsing directly inside upload route handlers.

Trade-off:
- Faster initial endpoint coding, but route bloat, weaker testability, and harder architecture explanation.

Why this choice:
- Service-layer parsing keeps API routes thin and gives reusable analysis primitives.

Validation:
- Parsed `sample_logs/sample_zscaler.log` with output `events=4`, `errors=0`.
- Verified invalid row handling returns structured parse errors with line numbers.

Outcome:
- Reusable parser layer now provides normalized event payloads for ingestion pipelines.

### Step 15: Add normalization helpers in `backend/app/services/normalizer.py`

Objective:
- Centralize low-level conversion/cleanup logic used by the parser.

Approach chosen:
- Added helper functions for:
  - timestamp parsing (`parse_timestamp`)
  - integer conversion (`parse_int`)
  - null/empty handling (`clean_text`)
  - action cleanup (`normalize_action`)

Alternative considered:
1. Keep conversion code inline in parser functions.

Trade-off:
- Fewer files now, but duplicated conversion logic and harder future reuse.

Why this choice:
- Normalizer helpers isolate data hygiene concerns and keep parser flow readable.

Validation:
- Verified helpers are used by parser and produce expected normalized output on sample data.

Outcome:
- Parser internals are cleaner and easier to extend for additional log formats.

## Phase 6: Upload and Summary Flow

Date: 2026-03-06

### Step 16: Add authenticated upload route in `backend/app/routes/uploads.py`

Objective:
- Connect ingestion, parsing, and persistence through a single protected endpoint.

Approach chosen:
- Added `POST /uploads` with JWT protection.
- Endpoint flow:
  - validates multipart file input and source
  - resolves authenticated user
  - persists `Upload` record
  - stores file on disk via storage service
  - parses rows via parser service
  - persists `Event` rows
  - computes and persists `Summary`
  - returns upload status, parse errors, and summary payload

Alternative considered:
1. Upload and return parsed JSON without storing.

Trade-off:
- Simpler implementation, but weaker full-stack story and no durable analysis history.

Why this choice:
- Persisted upload flow creates real end-to-end backend value and supports future analytics features.

Validation:
- Executed Flask test-client upload flow with authenticated user and `sample_zscaler.log`.
- Verified HTTP `201` and persisted records (`Upload=1`, `Event=4`, `Summary=1` in test run).

Outcome:
- End-to-end ingestion pipeline is now operational.

### Step 17: Add storage helpers in `backend/app/services/storage.py`

Objective:
- Centralize file path generation and disk save behavior.

Approach chosen:
- Added `build_storage_filename()` and `save_upload_file()`.
- Storage includes unique filename generation with upload ID, timestamp, and random suffix.

Alternative considered:
1. Save files inline in route with ad hoc paths.

Trade-off:
- Faster initially, but higher risk of path collisions and less reusable logic.

Why this choice:
- Dedicated storage helper keeps route code focused and makes file-handling behavior consistent.

Validation:
- Confirmed uploaded file is written to configured upload directory and filename returned in response.

Outcome:
- File persistence is deterministic and reusable.

### Step 18: Add summary generator in `backend/app/services/summary.py`

Objective:
- Produce key aggregate metrics required after ingesting parsed events.

Approach chosen:
- Added `generate_summary_metrics()` to compute:
  - total events
  - blocked events
  - unique IPs
  - top categories
  - top destinations
  - top source IPs
- Persisted these metrics into `Summary` record.

Alternative considered:
1. Compute summary directly inside upload route.

Trade-off:
- Less abstraction initially, but harder testing and lower reuse in future batch jobs.

Why this choice:
- Service-level summary logic is easier to validate and reuse across workflows.

Validation:
- Verified summary payload and persisted fields from sample upload:
  - `total_events=4`
  - `blocked_events=1`
  - `unique_ips=4`
  - top lists populated for categories/destinations/source IPs.

Outcome:
- Upload response now includes actionable summary insights and persisted analytics baseline.

## Phase 7: Anomaly Detection

Date: 2026-03-06

### Step 19: Add anomaly rules service in `backend/app/services/anomaly.py`

Objective:
- Detect suspicious events from normalized parser output with explicit explanations.

Approach chosen:
- Added `detect_anomalies(events)` with rule-based checks:
  - blocked request
  - suspicious destination keyword match
  - zero-byte allowed request
  - excessive data transfer
- Each anomaly returns:
  - anomaly type
  - explanation text
  - severity
  - confidence score
  - event index reference

Alternative considered:
1. Start anomaly logic before parser stabilization.

Trade-off:
- Earlier visible security logic, but fragile behavior due to unstable ingestion format.

Why this choice:
- Stable normalized events from Stage 5 provide reliable inputs for deterministic rules.

Validation:
- Executed anomaly detection via upload flow and confirmed anomalies persisted and returned in API response.

Outcome:
- Rule-based anomaly layer is now active and explainable.

### Step 20: Add scoring helpers in `backend/app/services/scoring.py`

Objective:
- Keep confidence scoring logic isolated as anomaly rules expand.

Approach chosen:
- Added helpers for:
  - score clamping
  - combining signal boosts/penalties
  - severity mapping from confidence

Alternative considered:
1. Keep all scoring logic inline inside anomaly rules.

Trade-off:
- Slightly fewer files initially, but harder calibration and lower maintainability as rule set grows.

Why this choice:
- Scoring helper module creates a single place to tune confidence behavior across rules.

Validation:
- Verified anomaly service uses scoring helpers and produces stable confidence/severity output.

Outcome:
- Confidence scoring is reusable and easier to evolve.

### Stage 7 Integration Note

Approach chosen:
- Integrated anomaly detection into `POST /uploads` pipeline:
  - detect anomalies from parsed events
  - persist `Anomaly` records
  - set `Summary.total_anomalies`
  - return anomaly details in response

Validation:
- End-to-end test run confirmed upload success with persisted anomalies and updated summary counts.

## Phase 8: Frontend Shell

Date: 2026-03-06

### Step 21: Replace `frontend/package.json` with real Next.js project scripts/dependencies

Objective:
- Turn frontend from placeholder scaffold into runnable app shell.

Approach chosen:
- Added Next.js + React + TypeScript toolchain with `dev`, `build`, `start`, and `lint` scripts.

Alternative considered:
1. Keep placeholder scripts until UI features are implemented.

Trade-off:
- Minimal setup now, but delays frontend execution and makes integration harder to validate.

Why this choice:
- Runnable shell is required before API integration work can proceed cleanly.

Validation:
- Confirmed package scripts and dependency blocks are present.

Outcome:
- Frontend project now has executable runtime/build commands.

### Step 22: Add `frontend/tsconfig.json`

Objective:
- Establish strict TypeScript baseline for Next.js App Router project.

Approach chosen:
- Added strict TS config with Next plugin, path alias support, and no-emit workflow.

Alternative considered:
1. Use JavaScript-only shell initially.

Trade-off:
- Faster first render, but weaker type safety and later migration overhead.

Why this choice:
- Strong typing aligns with maintainable API contract consumption.

Validation:
- Confirmed TS include/exclude and Next plugin configuration are set.

Outcome:
- Frontend type-checking baseline established.

### Step 23: Add `frontend/next.config.js`

Objective:
- Centralize Next runtime config for shell behavior.

Approach chosen:
- Added strict mode, typed routes, and `NEXT_PUBLIC_API_BASE_URL` default.

Alternative considered:
1. Keep default config only.

Trade-off:
- Less configuration now, but weaker explicitness around API base URL and route typing.

Why this choice:
- Explicit config reduces ambiguity before API integration.

Validation:
- Confirmed config file loads ESM export and expected keys.

Outcome:
- Frontend runtime config is now explicit and ready for contract consumption.

### Step 24: Add `frontend/app/layout.tsx`

Objective:
- Define global shell layout and metadata.

Approach chosen:
- Added App Router root layout with global CSS import and selected typography setup.

Alternative considered:
1. Keep bare default layout.

Trade-off:
- Faster baseline, but less intentional global structure and weaker visual identity.

Why this choice:
- Root layout is the correct integration point for global UI shell settings.

Validation:
- Verified metadata and root structure render path are defined.

Outcome:
- Frontend has a stable top-level app container.

### Step 25: Add `frontend/app/page.tsx`

Objective:
- Provide first functional landing page tied to existing backend API shapes.

Approach chosen:
- Added shell dashboard page displaying:
  - backend route contract list
  - build stage progress
  - API base URL context

Alternative considered:
1. UI-first mock screen without backend contract references.

Trade-off:
- More visually motivating, but often causes rework when backend contracts differ.

Why this choice:
- Contract-aware shell minimizes frontend/backend drift.

Validation:
- Confirmed page content maps to current backend endpoints and stage status.

Outcome:
- Frontend shell now communicates real integration targets.

### Step 26: Add `frontend/app/globals.css`

Objective:
- Establish global styles for desktop/mobile rendering quality.

Approach chosen:
- Added responsive CSS variables, gradient background, card/grid shell, and typography styles.

Alternative considered:
1. Keep unstyled defaults.

Trade-off:
- Lower effort, but less usable shell and weaker demonstration value.

Why this choice:
- A clear baseline style improves development readability and interview/demo quality.

Validation:
- Verified stylesheet defines responsive layout behavior and global tokenized styling.

Outcome:
- Frontend shell is visually coherent and mobile-safe for early integration.

## Phase 9: Frontend Auth Layer

Date: 2026-03-06

### Step 27: Add API wrappers in `frontend/lib/api.ts`

Objective:
- Standardize API calls and error handling before UI feature wiring.

Approach chosen:
- Added `apiRequest()` wrapper with:
  - base URL resolution
  - auth header injection
  - JSON serialization/parsing
  - typed error (`ApiRequestError`)
- Added auth-oriented request helpers:
  - `loginUser`
  - `registerUser`
  - `fetchCurrentUser`

Alternative considered:
1. Use raw `fetch` directly inside pages/components.

Trade-off:
- Faster in short-term, but repeated boilerplate and inconsistent error handling.

Why this choice:
- Centralized API wrapper keeps frontend auth flow clean and testable.

Validation:
- Verified login form integration uses wrapper and typed error handling.

Outcome:
- Frontend has consistent request primitives for protected workflows.

### Step 28: Add token/session helpers in `frontend/lib/auth.ts`

Objective:
- Encapsulate browser-side auth persistence.

Approach chosen:
- Added localStorage-backed helpers:
  - `setAuthSession`
  - `getAuthSession`
  - `getAuthToken`
  - `clearAuthSession`
  - `hasAuthSession`

Alternative considered:
1. Store tokens directly in component state only.

Trade-off:
- Simpler flow per page, but no persistence across refresh/navigation.

Why this choice:
- Session helper layer keeps auth state management reusable and explicit.

Validation:
- Confirmed login flow writes/clears auth session through utility functions.

Outcome:
- Token persistence is centralized for upcoming authenticated UI features.

### Step 29: Add shared frontend types in `frontend/types/index.ts`

Objective:
- Establish typed contracts for API/auth payloads.

Approach chosen:
- Added shared interfaces for:
  - auth session
  - login/register requests and responses
  - authenticated user
  - API error payload

Alternative considered:
1. Infer shapes ad hoc in each component.

Trade-off:
- Less upfront typing, but weaker maintainability and easier contract drift.

Why this choice:
- Shared type definitions improve contract consistency across UI modules.

Validation:
- Verified API wrappers and login form consume shared type interfaces.

Outcome:
- Frontend auth layer now has a typed contract baseline.

### Step 30: Add login route in `frontend/app/login/page.tsx`

Objective:
- Provide dedicated authentication entry point before upload UI.

Approach chosen:
- Added App Router login page that hosts reusable login form and links back to dashboard.

Alternative considered:
1. Build upload UI first.

Trade-off:
- Upload-first can be motivating, but protected flow remains unresolved and causes rework.

Why this choice:
- Assignment core requires authenticated workflow; login should be stable first.

Validation:
- Confirmed `/login` route builds and renders via Next.js production build.

Outcome:
- Frontend has a concrete authentication route for protected workflows.

### Step 31: Add reusable login form in `frontend/components/LoginForm.tsx`

Objective:
- Isolate credential form logic from page-level layout.

Approach chosen:
- Added client component with:
  - controlled email/password inputs
  - loading and feedback states
  - login request call
  - token/session persistence
  - post-login navigation

Alternative considered:
1. Keep login form logic directly in page component.

Trade-off:
- Fewer files now, but harder reuse and larger page complexity.

Why this choice:
- Reusable form component supports cleaner page structure and future auth variants.

Validation:
- Ran frontend lint and build successfully after form integration.

Outcome:
- Frontend auth flow is functional and modular.

## Phase 10: Upload UI

Date: 2026-03-06

### Step 32: Add dashboard route in `frontend/app/dashboard/page.tsx`

Objective:
- Provide authenticated landing area after login with clear action routing.

Approach chosen:
- Added client-side dashboard page that:
  - validates auth session
  - fetches current user from `/auth/me`
  - exposes primary actions (go to upload, logout)

Alternative considered:
1. Redirect login directly to upload page without dashboard.

Trade-off:
- Faster path to action, but weaker navigation hub for future workflows.

Why this choice:
- Dashboard acts as stable post-login landing and organizes next user actions.

Validation:
- Confirmed login now redirects to `/dashboard` and page enforces session presence.

Outcome:
- Authenticated users now land in a dedicated workflow entry point.

### Step 33: Add upload page in `frontend/app/upload/page.tsx`

Objective:
- Build first primary user workflow after authentication.

Approach chosen:
- Added protected upload page with context text and back-navigation to dashboard.
- Page hosts reusable upload interaction component.

Alternative considered:
1. Trigger upload inside dashboard card only.

Trade-off:
- Fewer routes, but cramped interaction space and weaker separation of concerns.

Why this choice:
- Dedicated upload page keeps workflow focused and scalable for future analysis UI.

Validation:
- Confirmed `/upload` route is generated in Next.js build output.

Outcome:
- Upload workflow now has a dedicated UI surface.

### Step 34: Add upload interaction component in `frontend/components/UploadDropzone.tsx`

Objective:
- Provide reusable file upload experience connected to backend `/uploads`.

Approach chosen:
- Added dropzone component with:
  - drag-and-drop + file picker input
  - upload action via `uploadLogFile()`
  - progress/error state
  - summary/anomaly result preview

Alternative considered:
1. Place all upload logic directly inside upload page.

Trade-off:
- Faster first page implementation, but harder reuse and larger page complexity.

Why this choice:
- Reusable upload component supports modular UI and future embedding.

Validation:
- Ran frontend lint and build successfully.
- Verified Next build output includes `/dashboard` and `/upload` static routes.

Outcome:
- First full authenticated user workflow (login -> dashboard -> upload) is now implemented.

## Phase 11: Analysis Display

Date: 2026-03-06

### Step 35: Add analysis route in `frontend/app/analysis/[id]/page.tsx`

Objective:
- Render full analysis output after a successful upload.

Approach chosen:
- Added protected analysis page that:
  - validates auth session
  - reads upload analysis payload by ID from browser storage
  - renders summary, timeline, anomalies, and findings in ordered sections
  - handles missing analysis data with recovery navigation

Alternative considered:
1. Fetch analysis details from a new backend `GET /uploads/{id}` endpoint.

Trade-off:
- Backend fetch route is more durable and shareable across sessions, but requires extra backend contract work not scoped to this stage.

Why this choice:
- Stage 11 focused on analysis rendering; local cached payload enables immediate display with minimal backend churn.

Validation:
- Confirmed dynamic route file exists and composes all Stage 11 components in the requested order.

Outcome:
- Frontend now has dedicated analysis result page.

### Step 36: Build summary section component in `frontend/components/SummaryCards.tsx`

Objective:
- Surface highest-level analysis metrics first.

Approach chosen:
- Implemented reusable summary cards for totals, blocked ratio, anomalies, unique IPs, and parse errors.

Alternative considered:
1. Show metrics inline in the analysis page without component extraction.

Trade-off:
- Inline rendering is faster initially, but lowers reusability and increases page complexity.

Why this choice:
- Summary cards form a stable reusable block and match the requested top-down analysis narrative.

Validation:
- Verified metric mapping aligns to backend upload response fields.

Outcome:
- Analysis page now starts with concise high-level KPI visibility.

### Step 37: Build timeline section component in `frontend/components/TimelineTable.tsx`

Objective:
- Show event-level detail after summary context.

Approach chosen:
- Added event preview table with columns for time, user, source IP, action, category, destination, and bytes.

Alternative considered:
1. Render raw JSON event preview payload.

Trade-off:
- Raw JSON is quicker to implement but less readable and weaker for analyst workflows.

Why this choice:
- Structured table improves scanability and preserves a clear timeline flow.

Validation:
- Confirmed component gracefully handles empty event preview data.

Outcome:
- Event-level analysis is now visible in an analyst-friendly format.

### Step 38: Build anomaly section component in `frontend/components/AnomaliesTable.tsx`

Objective:
- Display anomaly detections with severity and confidence details.

Approach chosen:
- Added anomaly table with severity chips and confidence percentage formatting.

Alternative considered:
1. Merge anomalies into timeline rows.

Trade-off:
- Single table reduces components but mixes concerns and weakens focused anomaly review.

Why this choice:
- Dedicated anomaly section keeps threat signals clearly separated from baseline event telemetry.

Validation:
- Confirmed severity class mapping and fallback empty-state rendering.

Outcome:
- Anomaly details are now explicit and visually prioritized.

### Step 39: Build findings panel in `frontend/components/FindingsPanel.tsx`

Objective:
- Provide short, interview-friendly narrative takeaways from computed metrics.

Approach chosen:
- Added derived findings list (status, blocked ratio, top category/destination/source, anomaly and parse-error notes).

Alternative considered:
1. Skip findings and rely only on raw tables/cards.

Trade-off:
- Raw-only display is simpler, but less effective for rapid interpretation and presentation.

Why this choice:
- Findings panel summarizes implications and improves communication of analysis outcomes.

Validation:
- Confirmed findings are generated from response fields without extra backend dependencies.

Outcome:
- Stage 11 analysis page now includes an explicit interpretation layer.

### Stage 11 Integration Note

Approach chosen:
- Updated upload flow to persist successful response payload by upload ID and added "View Full Analysis" navigation.
- Extended upload API response with `events_preview` payload for timeline rendering.
- Added CSS classes for analysis grid, tables, severity chips, and findings panel.

Alternative considered:
1. Delay persistence/navigation wiring until a dedicated backend retrieval endpoint exists.

Trade-off:
- Delayed wiring reduces short-term complexity, but blocks end-to-end Stage 11 usability.

Why this choice:
- Immediate local handoff enables full analysis rendering now while preserving room for later backend retrieval enhancement.

Validation:
- Verified compile/lint/build checks after integration changes.

Outcome:
- Upload -> Analysis user workflow is complete for current stage scope.

## Step Template (For Next Phases)

```md
### Step <n>: <title>
Objective:
- <goal>

Approach chosen:
- <implementation>

Alternative considered:
1. <alternative>

Trade-off:
- <cost/benefit>

Why this choice:
- <rationale>

Validation:
- <what was checked>

Outcome:
- <result>
```
