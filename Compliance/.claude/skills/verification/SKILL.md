---
name: verification
description: How to prove a ANUPAL task is done — test strategy, fixtures, running the app headless, Windows/cloud quirks. Use when writing tests, closing a task, or debugging the dev environment.
---

# Verification

- "Done" = the task's Acceptance list executed for real in this session, outputs observed.
  Never mark done on "should work".
- Fixtures: `backend/tests/conftest.py` provides `db` (fresh SQLite in tmp, migrated),
  `demo_db` (session-scoped demo seed, `--scale 0.2`), `tenant_ctx`, `two_tenants` (isolation), `client`
  (FastAPI TestClient with `DEFAULT_LLM_PROVIDER=mock`), `fake_provider` factory for gateway tests.
- Markers: `slow` (perf/50k; assert at 2× target, print measured time), `e2e`. SQLite locally; CI also runs on Postgres (`-m postgres` tests need `ANUPAL_TEST_PG_URL`).
- Embeddings in tests: always `EMBEDDER=tfidf` (no model download).
- Fake clock (`freezegun` or injected `Clock`) for calendar, reminders, SLA, escalation, break-glass expiry.
- Every new repository: add it to `tests/isolation/` (two tenants, assert no cross reads/writes).
- Never call real LLM APIs or real government portals or messaging providers in tests. httpx `MockTransport` or mocks only.
- Running the app for checks: backend `uvicorn app.main:app --port 8091 --app-dir backend` in the
  background, poll `/api/health` until ok (max 30 s), then run checks, then stop it.
- Playwright: Chromium only. In Claude Code cloud sessions Chromium is preinstalled — do not run
  `playwright install`; if versions mismatch, launch with `executablePath` from env
  `PLAYWRIGHT_BROWSERS_PATH`. Locally on Windows, `npx playwright install chromium` once.
- Windows quirks: use `pathlib`; open files with `encoding="utf-8"`; no `fork`-dependent code;
  uvicorn `--reload` only in dev; avoid long path issues (keep fixture paths short); scripts must
  exist as `.ps1` and `.sh`.
- Performance checks print measured numbers into the hand-off note.
- After fixing a failing test, re-run the full suite for that package, not just the one test.
- UI/e2e checks: `uv run --project backend python scripts/ui_check.py --label Txx --pages /route1 /route2 [--e2e spec.ts]` is the one supported way (works in headless runs and in cloud sessions;
  handles stale node_modules and a mismatched preinstalled Chromium). Read the PNGs afterwards.
