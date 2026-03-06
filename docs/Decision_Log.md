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
