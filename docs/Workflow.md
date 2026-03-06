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
