# Decision Log

This file records key implementation decisions for interview and audit purposes.

## Phase 1: Project Foundation

Date: 2026-03-06

## Decision 1: Write README skeleton before coding

Context:
- Stage 1 required clear problem framing before implementation details grow.

Selected approach:
- Build a README skeleton first with overview, stack, architecture, setup placeholders, and build checklist.

Alternatives:
1. Write README after implementation.
   - Trade-off: Faster short-term coding, but increased documentation drift and lower design clarity.

Rationale:
- Early documentation creates a stable reference for scope, architecture, and onboarding.

Result:
- Clear baseline narrative established before feature work.

## Decision 2: Use PostgreSQL-only docker-compose baseline

Context:
- Need a reliable local data layer before parser and backend expansion.

Selected approach:
- Keep `docker-compose.yml` to only one service: PostgreSQL.

Alternatives:
1. Use each developer's local PostgreSQL installation.
   - Trade-off: Less immediate repo setup, but inconsistent environments and weaker portability.

Rationale:
- Compose-based DB standardizes local setup and reduces integration friction.

Result:
- Portable, reproducible database environment ready for upcoming phases.

## Decision 3: Add sample Zscaler log file immediately

Context:
- Parser development needs concrete example input to avoid ambiguity.

Selected approach:
- Add a small clean canonical file at `sample_logs/sample_zscaler.log`.

Alternatives:
1. Defer sample log creation until parser coding begins.
   - Trade-off: Slightly less setup now, but delayed parser decisions and uncertain input expectations.

Rationale:
- Early sample input enables deterministic parser design and test planning.

Result:
- Parser can be developed against a known baseline input shape.

## Decision 4: Keep explicit no-push guardrail

Context:
- Workflow preference requires remote updates only on explicit instruction.

Selected approach:
- Apply a strict rule: no push operation unless user explicitly requests it.

Alternatives:
1. Push after each completed stage by default.
   - Trade-off: Faster remote sync, but violates collaboration preference and can create unwanted history changes.

Rationale:
- Explicit push control preserves review discipline and user control.

Result:
- Local changes remain staged/committed as needed until push is explicitly requested.

## Phase 2: Backend Shell

Date: 2026-03-06

## Decision 5: Build runnable backend shell before parser/upload logic

Context:
- Stage 2 required a clean boot path before implementing ingestion features.

Selected approach:
- Implement backend shell first: dependency baseline, env template, app entrypoint, centralized config, and app factory.

Alternatives:
1. Implement uploads/parsing directly on top of minimal existing structure.
   - Trade-off: Faster feature coding initially, but repeated refactoring when adding DB, auth, and migrations.

Rationale:
- A stable bootstrapped shell reduces rework and keeps future logic changes isolated.

Result:
- Backend is structurally ready for feature work without architecture churn.

## Decision 6: Use modular app factory instead of single `app.py`

Context:
- Need maintainable initialization for DB, JWT, migrations, and routes.

Selected approach:
- Replace legacy single-file `backend/app.py` with:
  - `backend/run.py` as entrypoint
  - `backend/app/config.py` as central config
  - `backend/app/__init__.py` as factory and extension init
  - explicit route registration in `backend/routes`

Alternatives:
1. Keep one `backend/app.py` file.
   - Trade-off: Quicker initially, but harder to scale cleanly for testing, migrations, and module boundaries.

Rationale:
- Factory pattern keeps boot logic clean and supports long-term maintainability.

Result:
- Initialization is modular and ready for next-stage features.

## Decision 7: Define backend dependencies up front

Context:
- Stage 2 required Flask app boot with database, JWT, and migration support.

Selected approach:
- Explicitly add package requirements for each capability category.

Alternatives:
1. Add dependencies only when an import fails during development.
   - Trade-off: Smaller starting file, but unstable onboarding and unpredictable setup failures.

Rationale:
- Upfront dependency declaration provides deterministic environment setup.

Result:
- Backend installation requirements are complete and documented.

## Decision 8: Add `.env.example` before real secret usage

Context:
- Configuration variables must be visible without committing secrets.

Selected approach:
- Add `backend/.env.example` with all expected keys and safe placeholder values.

Alternatives:
1. Document env vars only in README text.
   - Trade-off: Less file overhead, but easier to miss variables and copy errors.

Rationale:
- Template file is the most practical onboarding artifact for environment setup.

Result:
- Config initialization is explicit, repeatable, and safer.

## Phase 3: Data Model

Date: 2026-03-06

## Decision 9: Define schema before parser logic

Context:
- Stage 3 required parser/upload features to target stable DB tables.

Selected approach:
- Implement schema first in `backend/app/models.py` with:
  - `User`
  - `Upload`
  - `Event`
  - `Anomaly`
  - optional `Summary`

Alternatives:
1. Parse first, persist later.
   - Trade-off: Faster initial prototyping, but weaker architecture narrative and higher refactor risk.

Rationale:
- Schema-first keeps service and route interfaces aligned to a real persistence contract.

Result:
- Domain model is explicit and ready for parser/upload integration.

## Decision 10: Generate migrations immediately after model definition

Context:
- Need versioned schema history as soon as initial models are in place.

Selected approach:
- Generated Flask-Migrate baseline and first migration revision from models.

Alternatives:
1. Delay migrations until parser/routes are implemented.
   - Trade-off: Less setup now, but poor schema traceability and bigger migration deltas later.
2. Use `db.create_all()` without Alembic revisions.
   - Trade-off: Quick local setup, but no reliable upgrade path across environments.

Rationale:
- Early migration baseline keeps schema evolution auditable and team-safe.

Result:
- `backend/migrations` now contains an initial revision for all Stage 3 tables.

## Decision 11: Use `psycopg[binary]` instead of `psycopg2-binary`

Context:
- Stage 3 validation exposed local Python compatibility issues with `psycopg2-binary`.

Selected approach:
- Switched database driver dependency to `psycopg[binary]==3.2.13`.

Alternatives:
1. Keep `psycopg2-binary` and require a different local Python toolchain.
   - Trade-off: Keeps older driver line, but increases onboarding friction and install failures.
2. Use source-built `psycopg2` with system `pg_config`.
   - Trade-off: Works in controlled environments, but adds native build prerequisites.

Rationale:
- `psycopg[binary]` provides cleaner install behavior on modern Python while preserving PostgreSQL support.

Result:
- `pip install -r backend/requirements.txt` validated successfully in this environment.

## Phase 4: Minimum Working API

Date: 2026-03-06

## Decision 12: Implement health route first

Context:
- Stage 4 required the smallest useful API path with high confidence in app readiness.

Selected approach:
- Added `GET /health` in `backend/app/routes/health.py`.

Alternatives:
1. Start with upload route first.
   - Trade-off: Faster feature visibility, but slower root-cause isolation if core boot/routing fails.

Rationale:
- Health endpoint is the fastest reliable proof that app initialization and route registration work.

Result:
- Basic runtime readiness check is available.

## Decision 13: Implement auth before upload

Context:
- Protected workflow is a core requirement and must be validated early.

Selected approach:
- Added `register`, `login`, and JWT-protected `me` endpoints in `backend/app/routes/auth.py`.

Alternatives:
1. Build upload route before auth.
   - Trade-off: Faster visible value, but authentication concerns are deferred and often cause later API redesign.

Rationale:
- Early auth baseline reduces downstream coupling risks and clarifies protected route patterns.

Result:
- Minimum secure workflow is established for upcoming upload/parse routes.

## Decision 14: Extract password handling into utility module

Context:
- Auth route handlers should remain focused on request/response flow.

Selected approach:
- Added `backend/app/utils/security.py` with `hash_password` and `verify_password`.

Alternatives:
1. Keep hashing logic inline in auth handlers.
   - Trade-off: Fewer modules, but lower reusability and harder testing.

Rationale:
- Utility isolation improves maintainability and keeps security behavior centralized.

Result:
- Credential handling is consistent and reusable.

## Phase 5: Parsing Layer

Date: 2026-03-06

## Decision 15: Implement parser in service layer, not route layer

Context:
- Stage 5 needed real analysis value by converting raw Zscaler rows to normalized event fields.

Selected approach:
- Added `backend/app/services/parser.py` with single-row and batch parse functions.
- Parser outputs normalized event keys and structured parse errors for malformed input.

Alternatives:
1. Put parsing directly in upload route logic.
   - Trade-off: Faster initial delivery, but quickly becomes messy and harder to explain or test.

Rationale:
- Service-layer parsing preserves route simplicity and creates reusable core analysis logic.

Result:
- Parsing capability now exists independently of API endpoint implementation.

## Decision 16: Extract normalization helpers into dedicated module

Context:
- Parser requires repeated cleanup and conversion operations.

Selected approach:
- Added `backend/app/services/normalizer.py` for:
  - timestamp parsing
  - integer conversion
  - null handling
  - text/action cleanup

Alternatives:
1. Keep conversion logic inline in parser methods.
   - Trade-off: Less initial structure, but duplicated logic and harder maintenance.

Rationale:
- Dedicated normalizers improve readability and reduce conversion bugs across parsing flows.

Result:
- Parsing code is cleaner and easier to evolve for additional log sources.

## Phase 6: Upload and Summary Flow

Date: 2026-03-06

## Decision 17: Implement persisted upload pipeline instead of transient parse response

Context:
- Stage 6 required connecting ingestion to persistence for end-to-end utility.

Selected approach:
- Added authenticated `POST /uploads` route that stores upload metadata, saves file, parses rows, persists events, and persists summary.

Alternatives:
1. Upload and return parsed JSON without storing.
   - Trade-off: Simpler and faster, but weaker full-stack architecture story and no durable records.

Rationale:
- Persisted ingestion enables auditability, repeatability, and future analytics workflows.

Result:
- Application now supports useful end-to-end ingest -> parse -> persist behavior.

## Decision 18: Extract storage logic into `storage.py`

Context:
- Upload processing requires consistent file naming and path handling.

Selected approach:
- Added storage helpers for deterministic filename generation and file save operations.

Alternatives:
1. Keep file save logic inline in upload route.
   - Trade-off: Less initial structure, but route complexity and duplicated storage behavior.

Rationale:
- Dedicated storage service keeps route handlers focused and storage behavior reusable.

Result:
- File handling is centralized and easier to evolve.

## Decision 19: Implement summary generation in dedicated service and persist richer metrics

Context:
- Upload endpoint should produce actionable post-ingest insights.

Selected approach:
- Added `summary.py` for metrics generation and expanded `Summary` schema with:
  - `unique_source_ips`
  - `top_categories`
  - `top_destinations`
  - `top_source_ips`
- Added migration to support new persisted summary fields plus `Upload.file_path`.

Alternatives:
1. Compute summary only in response and skip persistence.
   - Trade-off: Quick response value, but no historical summary storage.
2. Compute summary inside route directly.
   - Trade-off: Fewer files, but lower testability and reuse.

Rationale:
- Service-based summary logic with persistence creates a stronger architecture baseline for reporting and anomaly stages.

Result:
- Summary insights are now both returned by API and stored in database.
