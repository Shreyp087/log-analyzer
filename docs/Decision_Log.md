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

## Phase 7: Anomaly Detection

Date: 2026-03-06

## Decision 20: Build anomaly detection after parser normalization is stable

Context:
- Anomaly rules require clean normalized inputs to avoid noisy/fragile detections.

Selected approach:
- Added `backend/app/services/anomaly.py` after parsing layer was validated.
- Implemented rule-based detection with explanations and confidence scores.

Alternatives:
1. Start anomaly logic earlier during parser development.
   - Trade-off: More exciting early output, but unstable behavior and frequent refactors.

Rationale:
- Stable ingestion first makes anomaly rules more reliable and easier to defend.

Result:
- Detection output is deterministic and grounded in normalized event fields.

## Decision 21: Add scoring helper module for confidence calibration

Context:
- Confidence/severity logic grows quickly across multiple anomaly rules.

Selected approach:
- Added `backend/app/services/scoring.py` to centralize confidence math and severity mapping.

Alternatives:
1. Keep confidence calculations inside anomaly service methods.
   - Trade-off: Slightly simpler now, but harder to tune consistently later.

Rationale:
- Central scoring helpers improve consistency and maintainability of detection output.

Result:
- Confidence scoring is reusable and easier to calibrate over time.

## Decision 22: Persist anomalies during upload processing

Context:
- Stage 6 ingestion flow already parses and stores events; anomaly stage should extend this flow.

Selected approach:
- Integrated anomaly detection into `POST /uploads`:
  - detect anomalies from parsed events
  - persist `Anomaly` records
  - update `Summary.total_anomalies`
  - include anomaly details in response

Alternatives:
1. Return anomaly findings without persistence.
   - Trade-off: Simpler response logic, but no historical detection records.

Rationale:
- Persisted anomalies strengthen the full-stack security story and support downstream review/reporting.

Result:
- Upload endpoint now provides and stores actionable anomaly intelligence.

## Phase 8: Frontend Shell

Date: 2026-03-06

## Decision 23: Start frontend shell only after backend contracts stabilized

Context:
- Stage 8 initiated UI work after health/auth/upload/summary/anomaly backend contracts were established.

Selected approach:
- Built frontend shell referencing real backend endpoints and API base URL expectations.

Alternatives:
1. UI-first implementation before backend contract stability.
   - Trade-off: Visually motivating early progress, but high risk of UI/API rework.

Rationale:
- Backend-first contract clarity reduces frontend integration churn.

Result:
- Frontend shell now targets known endpoint shapes instead of assumptions.

## Decision 24: Use Next.js TypeScript App Router shell

Context:
- Need maintainable frontend baseline with clean route/layout conventions.

Selected approach:
- Added `package.json`, `tsconfig.json`, `next.config.js`, and App Router root files.

Alternatives:
1. Keep plain React/Vite shell.
   - Trade-off: Viable, but diverges from requested file structure and app-router workflow.
2. Delay framework setup and build static HTML first.
   - Trade-off: Faster prototype, but no scalable project foundation.

Rationale:
- Next.js App Router offers a clear, production-oriented shell aligned to requested structure.

Result:
- Frontend now has executable project scaffolding for API integration.

## Decision 25: Build contract-aware landing page rather than decorative placeholder

Context:
- Initial UI page should support upcoming integration work.

Selected approach:
- Added `app/page.tsx` displaying live contract checklist (routes + stage progress) and API base URL.

Alternatives:
1. Create design-only placeholder screen.
   - Trade-off: Better visual polish early, but weaker technical relevance for integration stage.

Rationale:
- Contract-aware UI shell provides immediate value for integration and testing.

Result:
- Frontend page now communicates backend readiness and next integration targets.

## Phase 9: Frontend Auth Layer

Date: 2026-03-06

## Decision 26: Implement login/auth flow before upload UI

Context:
- Stage 9 required authenticated frontend flow as a core assignment capability.

Selected approach:
- Built frontend auth layer first:
  - API wrapper
  - auth storage helper
  - shared types
  - `/login` page
  - reusable login form component

Alternatives:
1. Build upload UI first.
   - Trade-off: Faster visible feature progress, but unresolved auth flow leads to integration rework.

Rationale:
- Protected workflow is foundational and should be validated before upload interactions.

Result:
- Frontend now has a stable authentication baseline for protected feature expansion.

## Decision 27: Use centralized `api.ts` fetch wrapper

Context:
- Multiple frontend modules will call backend endpoints with consistent error/auth behavior.

Selected approach:
- Added typed `apiRequest()` wrapper and endpoint helpers for login/register/me.

Alternatives:
1. Use direct `fetch` in each component.
   - Trade-off: Less abstraction initially, but duplicated error handling and request setup.

Rationale:
- Central request utility reduces duplication and enforces contract consistency.

Result:
- API interaction logic is reusable and predictable.

## Decision 28: Persist auth session in `lib/auth.ts`

Context:
- Login state should survive refresh/navigation and remain easy to clear on failure/logout.

Selected approach:
- Implemented localStorage-based session helpers.

Alternatives:
1. Keep token in component state only.
   - Trade-off: Simpler per component, but no persistence and fragile UX.

Rationale:
- Session helper layer is practical for current frontend scope and easy to replace later if needed.

Result:
- Frontend auth state management is centralized and persistent.

## Decision 29: Keep login form as reusable component

Context:
- Login UI/logic should remain composable for future pages (e.g., modal, admin login, onboarding).

Selected approach:
- Added `components/LoginForm.tsx` and kept page-level composition in `app/login/page.tsx`.

Alternatives:
1. Implement form directly inside page.
   - Trade-off: Faster initial page setup, but reduced reusability and larger page file complexity.

Rationale:
- Component separation improves maintainability and future reuse.

Result:
- Login flow is modular and easier to evolve.

## Phase 10: Upload UI

Date: 2026-03-06

## Decision 30: Implement upload UI immediately after frontend auth layer

Context:
- Stage 10 defines first main authenticated user action in frontend.

Selected approach:
- Built upload workflow only after Stage 9 login/session flow was stable.

Alternatives:
1. Build upload UI before login flow.
   - Trade-off: Faster visible feature, but broken protected workflow and likely rework.

Rationale:
- Upload is meaningful only inside authenticated session constraints.

Result:
- UI now follows coherent flow: login -> dashboard -> upload.

## Decision 31: Add dedicated dashboard and upload routes

Context:
- Need clear post-login landing plus focused upload workspace.

Selected approach:
- Added:
  - `frontend/app/dashboard/page.tsx`
  - `frontend/app/upload/page.tsx`

Alternatives:
1. Single-page flow combining dashboard + upload.
   - Trade-off: Fewer routes, but lower clarity and reduced extensibility.

Rationale:
- Route separation keeps navigation clear and scales better as workflows expand.

Result:
- Frontend has structured authenticated navigation.

## Decision 32: Use reusable dropzone component for upload interaction

Context:
- Upload interaction includes file selection, drag/drop, API state handling, and result rendering.

Selected approach:
- Added `frontend/components/UploadDropzone.tsx` and integrated with typed upload API helper.

Alternatives:
1. Keep upload logic inline in upload page.
   - Trade-off: Less upfront abstraction, but larger page complexity and weaker reuse.

Rationale:
- Dedicated component keeps page simple and supports future reuse.

Result:
- Upload UX is modular, typed, and integrated with backend summary/anomaly response shape.

## Phase 11: Analysis Display

Date: 2026-03-06

## Decision 33: Render Stage 11 via dedicated dynamic analysis route

Context:
- Stage 11 required a full analysis screen after upload completion.

Selected approach:
- Added `frontend/app/analysis/[id]/page.tsx` as a protected route that loads cached upload analysis payload by upload ID and renders components in summary -> timeline -> anomalies -> findings order.

Alternatives:
1. Implement backend retrieval endpoint (`GET /uploads/{id}`) and fetch analysis on page load.
   - Trade-off: Better long-term durability across sessions, but increases backend scope for this stage.

Rationale:
- Dynamic route plus cached payload provides immediate end-to-end Stage 11 behavior with minimal contract expansion.

Result:
- Analysis results are now accessible through a dedicated URL after upload.

## Decision 34: Persist upload response in browser storage for route handoff

Context:
- Analysis page needed access to full upload response payload without adding new backend endpoints in this stage.

Selected approach:
- Updated upload UI to store response under `analysis_result_<upload_id>` and linked users to `/analysis/<upload_id>`.

Alternatives:
1. Pass payload only through React state/navigation.
   - Trade-off: Simpler state flow but breaks on refresh and direct URL open.
2. Use query-string encoded payload.
   - Trade-off: Quick handoff, but URL bloat and poor security/readability.

Rationale:
- Local storage keying by upload ID balances simplicity with refresh resilience for the current architecture.

Result:
- Upload -> analysis navigation now works reliably within the current browser session.

## Decision 35: Keep summary/timeline/anomalies/findings as separate components

Context:
- Stage 11 includes multiple presentation layers and clear section ordering.

Selected approach:
- Implemented `SummaryCards`, `TimelineTable`, `AnomaliesTable`, and `FindingsPanel` as standalone reusable components.

Alternatives:
1. Build one monolithic analysis page with inline sections.
   - Trade-off: Fewer files initially, but weaker maintainability and harder targeted iteration/testing.

Rationale:
- Component separation keeps responsibility boundaries clear and preserves clean workflow progression for solo delivery.

Result:
- Analysis UI remains modular and easier to extend.

## Decision 36: Add backend `events_preview` in upload response for timeline rendering

Context:
- Timeline display required event-level data, but full event retrieval route was not yet introduced.

Selected approach:
- Extended `POST /uploads` response to include capped `events_preview` list with serializable fields and ISO timestamps.

Alternatives:
1. Omit timeline data and show only summary/anomalies.
   - Trade-off: Less backend change, but incomplete Stage 11 display requirements.
2. Return all events with no cap.
   - Trade-off: Easier implementation, but larger payloads and slower UI for large uploads.

Rationale:
- Capped preview payload delivers useful detail while keeping response size controlled.

Result:
- Frontend can render timeline context immediately after upload.

## Decision 37: Add explicit analysis-specific CSS system

Context:
- Stage 11 introduced dense data tables and severity visualization not covered by prior shell styles.

Selected approach:
- Extended `frontend/app/globals.css` with analysis grid cards, table wrappers, truncation, severity chips, and responsive adjustments.

Alternatives:
1. Keep browser-default table styles.
   - Trade-off: Minimal work, but weak readability and poor visual hierarchy.

Rationale:
- Structured styling improves legibility and keeps the analysis view presentation-ready.

Result:
- Stage 11 screens render clearly on desktop and mobile.

## Auth Enhancement: Register Flow Completion

Date: 2026-03-06

## Decision 38: Add backend CORS support for direct frontend auth calls

Context:
- Auth endpoints were implemented, but browser-based cross-origin calls from frontend required explicit CORS handling.

Selected approach:
- Added `Flask-Cors` integration in app factory and configured allowed origins via `CORS_ORIGINS` environment variable.

Alternatives:
1. Keep backend without CORS and use server-side proxy only.
   - Trade-off: Avoids backend CORS config, but couples frontend implementation and complicates local troubleshooting.

Rationale:
- Native API access from frontend is simpler for this project structure and keeps auth flow transparent.

Result:
- Browser auth requests can execute reliably against backend API.

## Decision 39: Strengthen auth validation for register/login input

Context:
- Signup/login feedback should fail early with clear user-facing errors.

Selected approach:
- Added email format validation in both register and login routes while preserving existing password length checks.

Alternatives:
1. Keep only "field required" and credential mismatch checks.
   - Trade-off: Less code, but lower input quality and more ambiguous user feedback.

Rationale:
- Explicit validation improves UX and reduces invalid auth attempts reaching credential checks.

Result:
- Auth endpoints now return cleaner, more specific validation errors.

## Decision 40: Build dedicated register page + reusable form component

Context:
- Frontend had login only, which forced manual API registration and broke UX expectations.

Selected approach:
- Added `frontend/app/register/page.tsx` and `frontend/components/RegisterForm.tsx` with confirm-password guard and post-register session bootstrap.

Alternatives:
1. Keep registration API-only and document curl commands.
   - Trade-off: Minimal UI work, but poor usability for normal product flow.
2. Combine login and register in one form component/page.
   - Trade-off: Fewer routes, but more state complexity and less clear UX.

Rationale:
- Separate register route keeps intent clear and matches common authentication patterns.

Result:
- Users can sign up directly from UI without command-line steps.

## Decision 41: Improve auth discoverability with explicit navigation links

Context:
- New register route must be discoverable from existing entry points.

Selected approach:
- Added links from login page and home page to register flow.

Alternatives:
1. Keep register route unlinked and rely on direct route knowledge.
   - Trade-off: Cleaner UI, but higher onboarding friction.

Rationale:
- Clear entry points reduce confusion and improve first-run success.

Result:
- Auth journey is now fully navigable for first-time users.
