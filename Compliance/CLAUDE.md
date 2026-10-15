# ANUPAL — AI compliance OS for Indian MSMEs (a Stridenity Solutions product)

Managed **multi-tenant SaaS** (Stridenity operates it on a cloud provider; every tenant's data
is isolated) that works out which compliance obligations apply to each unit, guides what data to
feed, drafts the content with AI, routes everything through maker → checker → approver, and
keeps an inspection-ready evidence trail. Sectors: manufacturing, healthcare, construction,
electrical; India (Central + Maharashtra) first, region-agnostic core.
The product name lives in ONE place (`backend/app/core/config.py: APP_NAME`, `frontend/src/config.ts`).

**Location:** this product is the `Compliance/` folder of the monorepo `LearningX-BK/Stridenity`.
All paths below are relative to `Compliance/`; run every command from this folder (in a cloud
session started at the repo root: `cd Compliance` first — the shell keeps the cwd).

Read before writing code, in this order:
1. `docs/plan/PROGRESS.md` — where the build is + last hand-off note
2. `docs/plan/TASKS.md` — ONLY the section of the task you are on
3. `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/WORKFLOWS.md`, `docs/UX.md`,
   `docs/COMPLIANCE_UNIVERSE.md` — only the sections your task touches
4. The skill(s) your task lists under **Skills** (`.claude/skills/<name>/SKILL.md`)

## Build protocol (non-negotiable — this is how work survives a token cut-off)

- The build is a sequence of tasks in `docs/plan/tasks.json`. ONE task per session, via
  `/next-task`. Never start a task whose dependencies are not `done`.
- **One builder at a time (ADR-014).** Before work: `python scripts/tasks.py claim local` (or
  `cloud` when `CLAUDE_CODE_REMOTE=true`). Exit code 3 = the other side is building → print
  `TASK_BUSY` and stop without changing anything. Commit + push the claim.
- Start: `git pull --rebase` → `python scripts/tasks.py next` → read the hand-off note. If
  `git status` shows uncommitted changes, a previous session was cut off: inspect, keep what is
  sound, continue — do not blindly reset.
- Mark the task `in_progress` (`python scripts/tasks.py start Txx`) and commit immediately.
- **Checkpoint often**: after every sub-step that leaves the tree working, append 1–3 hand-off
  lines in PROGRESS.md (done / next / gotcha — written for a stranger), commit
  `wip(Txx): <what>`, push.
- Finish: run every **Acceptance** item for real → `/verify` → `python scripts/tasks.py done Txx`
  → commit `feat(Txx): <title>` → push → print `TASK_COMPLETE Txx`.
- Can't meet an acceptance item? Don't mark done: `python scripts/tasks.py block Txx "reason"`,
  commit, push, print `TASK_BLOCKED Txx: reason`, stop.
- Never rewrite git history (no force-push, no rebase of pushed commits, no `reset --hard`).
- Scope discipline: do what the task says; ideas go to `docs/plan/BACKLOG.md`. New scope is added
  as NEW tasks in TASKS.md (then `python scripts/tasks.py sync`), never by changing done tasks.
- A doc decision is wrong? Record an ADR in `docs/DECISIONS.md` and fix the doc in the same commit.
- Only touch files under `Compliance/` (plus `/.github/workflows/compliance-ci.yml` and the root
  `CLAUDE.md`/`.claude/` router). Other top-level folders belong to other Stridenity products.

## Token economy (the 5-hour usage window is the scarcest resource)

- **Short sessions.** `/next-task` has a step budget (default 2 sub-steps), then hands off with
  `TASK_CONTINUE`. Context size is what costs — every turn re-sends it.
- Targeted checks while building (`pytest backend/tests/<area> -x -q`); full suite, slow tests,
  ui_check only at acceptance. Pipe noisy output through `tail`.
- Never read big/generated files whole (`data/`, `content/seed/obligations.seed.json`, lockfiles,
  `dist/`, logs) — use `head`, `grep`, `python -c`. Don't re-read files already in context.
- Content-heavy output (packs, templates, fixtures, seed data): write each file once; generate
  repetitive data with code.
- One quality pass: one review round per task; fix high/medium, backlog the rest.
- Subagents cost a fresh context each: Explore only for > 10 files; reviewer once per task.

## Stack

- **Backend**: Python 3.12 (`requires-python = ">=3.11,<3.13"`), FastAPI, Pydantic v2,
  SQLAlchemy 2.0 typed + **sync** sessions (ADR-011), Alembic, httpx, pytest, uv. No packages
  needing a C compiler on Windows.
- **DB**: SQLite for dev/demo/tests (`sqlite:///./data/anupal.db`, WAL, busy_timeout);
  **PostgreSQL 16 in production** with RLS (ADR-006/007). Dialect specifics only in `db/dialect.py`.
- **Frontend**: React 18 + Vite + TypeScript strict + Tailwind + Radix primitives, TanStack Query,
  React Router, Zustand (UI state only), Recharts, lucide-react, react-i18next.
- **LLM**: own gateway in `backend/app/contexts/ai/` (skill `llm-gateway`). Provider SDKs only in
  `contexts/ai/providers/`.

## Layout

```
backend/app/
  core/        config, logging, crypto (envelope keys), errors
  db/          base, session routing (tenant tier), dialect, migrations (alembic)
  platform/    audit log (hash chain), jobs/outbox, settings
  contexts/    tenancy · identity · org · content · applicability · calendar · workflow ·
               evidence · intake · audit · contractor · regchange · ai · notify · reporting
               (each: models.py, repo.py, service.py, api.py (public interface), router.py, schemas.py)
  demo/        demo tenants seed + planted stories
  ops/         operator CLI (tenants, migrate, audit verify)
  main.py, worker.py
backend/tests/ mirrors app/; tests/isolation/ cross-tenant suite
frontend/src/  app/ (shell, routes, theme) · components/ui/ · components/ · features/<area>/ ·
               features/ops/ · lib/ (api client, rules.ts, format) · styles/tokens.css · i18n/
content/       seed/ (v0 library + generator) · packs/<jurisdiction>/<pack>/ (YAML)
scripts/       tasks.py, build-loop.ps1/.sh, setup-git-sync.ps1, bootstrap.ps1, dev.ps1/.sh, ui_check.py
docs/          PRD, ARCHITECTURE, WORKFLOWS, UX, COMPLIANCE_UNIVERSE, DECISIONS, DEMO_SCRIPT, plan/
prototype/     index.html — clickable concept prototype (reference for UX, not production code)
```

## Commands (from `Compliance/`)

```bash
uv sync --project backend
uv run --project backend pytest -q
uv run --project backend ruff check backend && uv run --project backend ruff format --check backend
uv run --directory backend mypy app
uv run --project backend lint-imports --config backend/.importlinter
uv run --project backend python -m app.demo.seed --reset
uv run --project backend uvicorn app.main:app --reload --port 8091 --app-dir backend
npm --prefix frontend install && npm --prefix frontend run dev      # :5191, proxies /api → :8091
npm --prefix frontend run build && npm --prefix frontend run typecheck && npm --prefix frontend run lint
uv run --project backend python scripts/ui_check.py --label Txx --pages /route1 /route2 [--e2e spec.ts]
```
**Headless sessions:** start servers / Playwright ONLY via `scripts/ui_check.py` (API 8191, UI
5291). Background `&`, `cd x && y` chains, env-var prefixes and `Start-Process` are denied in
unattended runs. Then Read the PNGs it saved.

## Hard rules

- **Tenant isolation is sacred.** No request, job, query, file access, cache key, vector search
  or export without a `TenantContext`. Every repository extends `TenantRepository` and registers
  in `tests/isolation/`. Ops/staff access to tenant data only through break-glass (ADR-017).
- **Regulatory content is data** (packs), never constants in code: rates, thresholds, due rules,
  penalties, forms. Every obligation keeps `source_url`, `verified_on`, `review` status.
  Never invent a legal fact: if unsure, mark `verify: true` and add it to the pack's REVIEW.md.
- **AI drafts, humans decide.** No code path lets AI file, pay, approve or close. Every AI output
  is an `AIAction` (skill `explainability`) and AI drafts always enter the `document` workflow.
- **App works with zero API keys** (mock LLM + deterministic engines).
- **Never send unredacted PII to an LLM** (`contexts/ai/redaction.py`).
- **SoD and OTP step-up are enforced in the backend**, never only in the UI.
- Every state change writes the hash-chained `AuditLog`.
- LLM outputs that drive logic are structured (pydantic schema, one repair retry, deterministic fallback).
- Frontend: colours/spacing/radii only from `styles/tokens.css`; both themes checked for every
  screen; AI content always visibly marked until approved; Indian number/date formats.
- Base-path aware (`ANUPAL_BASE_PATH`, Vite `base`). Money in paise (int). Store UTC, show IST.
- Type everything; ruff + mypy clean; no `any` in TS without a comment.
- Tests: every service unit-tested; every router has API tests with the mock provider.
- Windows-friendly: `pathlib`, UTF-8 explicit, scripts as `.ps1` and `.sh`.
- Prototype conventions carried into the product where relevant: `data-*` attributes for event
  handlers (never inline string args), `toast(msg, type)`-style notifications.

## Model guidance for subagents
`code-reviewer` before closing any opus-tagged task; `qa-verifier` for UI tasks;
`compliance-auditor` for content-pack tasks (T08, T09) and for audit/workflow features.
