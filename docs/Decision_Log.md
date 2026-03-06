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
