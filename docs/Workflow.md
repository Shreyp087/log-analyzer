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
