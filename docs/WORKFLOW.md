# Engineering Workflow

This document defines how work should be executed and documented in this repository.

## Goals

1. Document every task clearly and consistently.
2. Capture alternatives and trade-offs for each major step.
3. Keep a clean, repeatable workflow.

## Standard Execution Flow

For each task, follow this order:

1. Define objective and constraints.
2. List candidate approaches.
3. Compare trade-offs.
4. Choose one approach with rationale.
5. Implement in small, clear steps.
6. Validate with checks/tests.
7. Record outcome and next actions.

## Step Record Template

Use this template for each major step.

```md
### Step: <short title>
Date: <YYYY-MM-DD>
Objective:
- <what this step must achieve>

Approach Chosen:
- <what was done>

Alternatives Considered:
1. <alternative A>
   - Pros: <...>
   - Cons: <...>
2. <alternative B>
   - Pros: <...>
   - Cons: <...>

Trade-offs:
- <performance vs simplicity, speed vs maintainability, etc.>

Why This Choice:
- <interview-ready rationale>

Validation:
- <commands run, tests checked, expected/actual results>

Outcome:
- <result>
```

## Clean Workflow Rules

1. Keep commits scoped to one logical change.
2. Use descriptive commit messages.
3. Run checks before push (tests/lint if available).
4. Update `docs/DECISION_LOG.md` for non-trivial decisions.
5. Avoid undocumented shortcuts.
