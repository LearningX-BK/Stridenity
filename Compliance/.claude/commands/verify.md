---
description: Run the full quality gate (backend lint/types/tests/isolation, frontend typecheck/lint/build, UI check) and fix failures
---

From `Compliance/`, run in order and fix anything that fails before reporting (skip a step only if
that part does not exist yet, and say so):

1. `uv run --project backend ruff check backend` and `uv run --project backend ruff format --check backend`
2. `uv run --directory backend mypy app`
3. `uv run --project backend lint-imports --config backend/.importlinter` (context boundaries, ADR-002)
4. `uv run --project backend pytest -q` (then `-m slow` once if the task has perf acceptance)
5. `uv run --project backend pytest -q backend/tests/isolation` — must be green, always
6. `npm --prefix frontend run typecheck`, `npm --prefix frontend run lint`, `npm --prefix frontend run test`, `npm --prefix frontend run build`
7. If UI pages exist: `uv run --project backend python scripts/ui_check.py --label verify --pages / --no-mobile --e2e`
8. Content: `uv run --project backend python -m app.content validate content/packs` (once T06 exists)
9. Grep guardrails:
   - no provider SDK imports outside `backend/app/contexts/ai/providers/`
   - no hex colour literals in `frontend/src/**/*.tsx` (only `styles/tokens.css`)
   - no `print(` in `backend/app` (use logging)
   - every route under `/api/v1/ai/` returns an `action` field
   - no repository class that does not extend `TenantRepository` (except tenancy registry)
   - no hard-coded statutory rates/thresholds in `backend/app` (e.g. `0.12`, `21000`, `15000` near PF/ESI) — they belong in packs

Report a compact pass/fail table. If you changed code to fix failures, commit `fix: verify gate`.
