# ANUPAL build plan

35 tasks, each sized for a few short Claude Code sessions (step budget 2 per session by default)
and to leave `main` green. **Run order = order in `tasks.json`.** Status lives in `tasks.json`
(`python scripts/tasks.py status`), hand-offs in `PROGRESS.md`. **Model**: `opus` only where
design/logic is hardest (T02, T06, T07, T10, T11, T30, T32b); everything else `sonnet`.

Heading format (parsed by `python scripts/tasks.py sync` — keep it exact):
`### Txx · Title — model · deps: T01, T02`

Every task: Goal · Deliverables · Acceptance (all must pass, run for real) · Skills.
Paths are relative to `Compliance/`.

---

## Phase A — Foundations

### T00 · Repo scaffold & tooling — sonnet · deps: —
**Goal** Working skeleton of both halves, one command to run.
**Deliverables** `backend/` uv project (Python 3.12 via `.python-version`, `requires-python =
">=3.11,<3.13"`), FastAPI `app.main` with `/api/health` (returns app name, version, db ok),
pydantic-settings config (`APP_NAME="ANUPAL"`, env prefix `ANUPAL_`), JSON logging, ruff + mypy
(strict on `app/`) + pytest config, `backend/app/contexts/` package skeleton per ARCHITECTURE §2
with import-linter contract (contexts import each other only via `contexts/<x>/api.py`);
`frontend/` Vite React TS strict, Tailwind wired to `src/styles/tokens.css` (copy from
docs/UX.md §1), ESLint, Prettier, Vitest, Playwright config, `/api` proxy → 8091, dev port 5191;
`scripts/dev.ps1` + `scripts/dev.sh`; `scripts/bootstrap.ps1` (installs uv via winget if missing,
creates `.env` from `.env.example` with a generated Fernet key, UTF-8 **without BOM**);
`/.github/workflows/compliance-ci.yml` at **repo root** with `paths: ["Compliance/**"]` and
`working-directory: Compliance` (backend lint/types/tests; frontend typecheck/lint/test/build);
`README.md` quickstart.
**Acceptance** `uv run --project backend pytest -q` passes; ruff, mypy, import-linter clean;
`npm --prefix frontend run build|typecheck|lint` pass; dev servers serve a page showing "API: ok"
from `/api/health` (verified by HTTP request); `.env` has no BOM; CI YAML parses.
**Skills** verification

### T01 · Headless UI check & test fixtures — sonnet · deps: T00
**Goal** The one command headless sessions use to see the UI (TRIAX lesson: headless sessions
cannot start background servers).
**Deliverables** `scripts/ui_check.py`: builds a scratch SQLite DB (`data/ui-check.db`), runs
migrations + `python -m app.demo.seed --tenant ui-check --scale 0.2` (stub seed now; real data in
T28), starts API :8191 and UI :5291 (Vite with env pointing to 8191), logs in as the demo admin,
screenshots each `--pages` route in light + dark at 1440×900 and 390×844 into
`docs/screens/<label>/`, records console errors and axe serious/critical violations into
`report.md`, optional `--e2e <spec>` runs Playwright specs, **always** kills what it started
(also on Ctrl-C/exceptions), works on Windows and Linux, handles a preinstalled Chromium
(`PLAYWRIGHT_BROWSERS_PATH`) in cloud sessions. `backend/tests/conftest.py` fixtures: `db`,
`tenant_ctx`, `client` (mock LLM), `two_tenants` (for isolation tests).
**Acceptance** `uv run --project backend python scripts/ui_check.py --label T01 --pages /` exits
0, writes 4 PNGs + report.md with "API: ok" visible (Read one PNG to confirm); no server
process left running (check ports free afterwards); pytest passes.
**Skills** verification

### T02 · Tenancy core & control-plane registry — opus · deps: T00
**Goal** Multi-tenant isolation from day one (ADR-007, ADR-017).
**Deliverables** `contexts/tenancy/`: `Tenant` registry model (slug, name, tier
pooled|schema|dedicated, db_route, region, plan, status, kms_key_ref, flags), `TenantContext`
dataclass, resolver (subdomain / `X-Tenant` header in dev / token claim), FastAPI middleware +
dependency that rejects requests without a context; `db/session.py` routing a session to the
tenant's engine/schema; repository base class `TenantRepository` that always filters
`tenant_id` and stamps it on insert; Alembic migration adding Postgres RLS policies (no-op on
SQLite) and `SET LOCAL app.tenant_id` per transaction on Postgres; per-tenant data-key
envelope encryption helper (`core/crypto.py`: local Fernet master key now, KMS adapter
interface); job payloads carry tenant id; `ops` CLI: `python -m app.ops tenant create|list|suspend`.
Cross-tenant test harness `tests/isolation/` that every later repository registers into.
**Acceptance** tests: request without tenant → 400/401; repository cannot read other tenant's
rows (SQLite); in CI Postgres job, RLS blocks a raw `SELECT` across tenants with the app role;
schema tier routes to `t_<id>` schema (Postgres job); encryption round-trip with per-tenant keys
and key A cannot decrypt tenant B data; `ops tenant create` works. ADR-007 implementation notes
added to ARCHITECTURE §7 if anything changed.
**Skills** tenancy, verification

### T03 · Identity, RBAC & audit log — sonnet · deps: T02
**Goal** Users, roles and an immutable trail.
**Deliverables** `contexts/identity/`: User (global), Membership (user × tenant × roles × unit
scope), roles from PRD §2 + `ops_*` family, permission map (`can(user, action, resource)`),
password (argon2) + OTP login (OTP sender interface: console/mock in dev), JWT access + rotating
refresh cookie, OTP step-up endpoint for approvals, delegations (date range, role/unit scope),
tenant switcher for multi-tenant users; `platform/audit.py` hash-chained `AuditLog` +
`python -m app.ops audit verify --tenant x`; login page in frontend (minimal; shell styles
arrive in T04).
**Acceptance** API tests for login (password, OTP), refresh rotation, step-up required for an
endpoint marked `requires_otp`, role denial, unit scope denial, delegation acting-on-behalf
recorded; audit chain verifier detects a tampered row (test); identity repositories registered
in the isolation suite and pass.
**Skills** tenancy, verification

### T04 · App shell & design system — sonnet · deps: T03
**Goal** Every later feature ships its screen into a finished shell (ADR-012).
**Deliverables** Shell (sidebar per UX §2, top bar with tenant/unit switcher, search/⌘K slot,
theme toggle light/dark/system, language switch placeholder, user menu), routing for every IA
entry with empty states, primitives (Button, Input, Select, Combobox, Checkbox, Tabs, Dialog,
Drawer, Tooltip, Toast, Badge/StatusChip, Card, Table with sticky header + mobile card mode,
Stepper, EmptyState, Skeleton, KPI tile, ProgressRing), `AIChip` + `WhyDrawer` + `ConfidenceChip`
(skill explainability), Stridenity logo component (gradient mark SVG + wordmark), Plus Jakarta
Sans / JetBrains Mono self-hosted, `formatINR`, `formatDate` (IST), generated TS API client from
OpenAPI (`npm run gen:api`).
**Acceptance** ui_check on `/ /register /calendar /inbox /evidence /audits /settings` passes with
0 console errors and 0 serious axe violations; qa-verifier pass on the PNGs (both themes,
mobile); no hex outside tokens.css (grep); typecheck/lint/build pass.
**Skills** stridenity-ui, explainability, verification

### T05 · Organisation, units & profile facts — sonnet · deps: T03
**Goal** The facts applicability runs on.
**Deliverables** `contexts/org/`: LegalEntity (form, CIN/LLPIN, PAN, GSTIN, Udyam), Unit (state,
district, address, sectors, activities), Department, Person (lightweight HR master: name, role,
unit, phone, email), Contractor; `ProfileFactValue` versioned per unit (valid_from, set_by,
source manual|import|extraction) with the fact catalogue loaded from content (facts list in
`content/seed/obligations.seed.json` until packs exist); derived facts (`total_workers`);
threshold proximity service; GSTIN/CIN/Udyam lookup **adapter interface** with mock; CRUD APIs.
**Acceptance** API tests for CRUD + fact history ("value as of date"); derived fact test;
proximity test (18 employees → EPF at 20 alert); isolation suite includes org repositories.
**Skills** compliance-domain, tenancy

---

## Phase B — Compliance core

### T06 · Content packs: schema, loader, versioning — opus · deps: T05
**Goal** Regulatory content as validated, versioned data (ADR-003, ADR-016).
**Deliverables** YAML pack format per skill `compliance-packs` (`content/packs/IN/<pack>/pack.yaml`
+ `obligations/*.yaml`, `facts.yaml`, `templates/*.md.j2`, `holidays/*.yaml`); JSON Schema +
pydantic models; validator CLI `python -m app.content validate content/packs` (unknown facts,
bad rules, bad due rules, missing source_url, duplicate keys, effective-date overlaps);
loader into `content` tables with pack versions and diff (`python -m app.content diff IN/central
0.1.0 0.2.0`); importer that converts `content/seed/obligations.seed.json` into initial packs
(central, maharashtra, manufacturing, healthcare, construction, electrical) **keeping
`review: sme_pending` and `verify` flags**; content API (list/search/get obligation, packs).
**Acceptance** validator passes on imported packs and fails with a clear message on 5 broken
fixtures (one per error class); load → diff → reload idempotent; 82 seed obligations present;
API tests.
**Skills** compliance-packs, compliance-domain

### T07 · Applicability engine, register & overrides — opus · deps: T06
**Goal** "What applies to this unit, and why" (FR-3..5).
**Deliverables** `contexts/applicability/rules.py` pure evaluator with traces and `needs_input`
(ARCHITECTURE §4.1); `evaluate(unit)` → RegisterEntry rows; plain-language explanation
generator ("Applies because …", "Would stop applying if …"); re-evaluation on fact or pack
change producing a **diff** that must be acknowledged; overrides (applicable↔NA) with
justification → `override` workflow hook (stub until T11, records request); TS port
`frontend/src/lib/rules.ts` with **shared JSON test vectors** run by pytest and Vitest; APIs:
register list/filter/export xlsx, entry detail with trace, diff, acknowledge.
**Acceptance** shared vectors (≥ 40 cases incl. nested any/all/not, unknown fact) pass in both
languages; for the 3 demo profiles in `content/seed/` the register counts are stable snapshot
tests; crossing 20 employees adds EPF + bonus + GRC in the diff (test); evaluation of 400
obligations × 10 units < 500 ms (slow test prints time).
**Skills** compliance-domain, compliance-packs

### T08 · Central pack content — verified — sonnet · deps: T06
**Goal** Trustworthy central content: labour codes, social security, tax & corporate, POSH, DPDP.
**Deliverables** For every central obligation: verify against official sources (WebFetch
allow-listed government sites; record `source_url`, `verified_on`, cite section/rule); fix dates,
thresholds and form numbers (Income-tax Act 2025 numbering, labour-code central rules); add
`input_schema`, `evidence_slots`, `audit_points`, penalty text; mark `review: ai_verified` (SME
still to review → `sme_reviewed`); write `content/packs/IN/central/REVIEW.md` listing every
uncertain item with the question for the SME. Rates (PF/ESI/ceilings) as `rates.yaml` with
effective dates.
**Acceptance** validator passes; every central obligation has source_url + verified_on; REVIEW.md
lists all items still `verify: true` with reasons; compliance-auditor agent review once, high
findings fixed.
**Skills** compliance-packs, compliance-domain

### T09 · Maharashtra & sector packs — verified — sonnet · deps: T08
**Goal** Same quality for Maharashtra (PT, LWF, S&E, fire Form B, lifts, MPCB, RERA,
electrical licensing, legal metrology, nursing homes) and the four sector packs; MH + national
holiday calendars for 2026–2027.
**Deliverables / Acceptance** as T08 for these packs; holiday YAML validated; REVIEW.md per pack.
**Skills** compliance-packs, compliance-domain

### T10 · Calendar engine & instances — opus · deps: T07
**Goal** Every applicable obligation becomes dated work (FR-7..10).
**Deliverables** `contexts/calendar/`: due-rule evaluator for all rule types (ARCHITECTURE §4.2),
holiday shift policies per authority, rolling 13-month idempotent generation, event-driven
instances API (`POST /events {type: employee_joined, …}`), renewal instances from licence
validity, `monthly_selfcheck` instances, government extension application, owner/checker/
approver defaults from register entry; calendar API (range, filters, ICS export per user).
**Acceptance** property tests: generation idempotent, no duplicates, every instance due within its
period window; holiday shift tests (15 Aug, Diwali, Sundays); FY vs calendar-year annuals; event
within N working days; extension moves only matching open instances; one tenant-year generation
< 5 s (slow test).
**Skills** compliance-domain

### T11 · Workflow & approval engine — opus · deps: T10
**Goal** Internal approval process that would satisfy an auditor (FR-11..17, docs/WORKFLOWS.md).
**Deliverables** `contexts/workflow/`: templates (seed defaults), approval matrix evaluator with
preview, pure transition function + persistence, template snapshot per run (ADR-009), SoD guard,
small-team mode flag, OTP step-up for approver steps, delegation, return-with-reason, request
info, reassign, comments with @mentions, SLA timers + escalation events, instance state machine
integration (incl. NA_REQUESTED, delay reason, APPLIED_AWAITING_GRANT), override workflow wired
to T07, inbox API (mine, team, overdue, SLA).
**Acceptance** table-driven tests for every template path incl. return loops; SoD violations
rejected (maker approving own item; approver who edited evidence); delegation recorded on
behalf; OTP required; template edit doesn't affect in-flight run; escalation fires at T+1/T+3/T+7
with a fake clock; every transition writes AuditLog; code-reviewer pass.
**Skills** workflow-engine, compliance-domain

### T12 · Jobs, reminders & notifications — sonnet · deps: T11
**Goal** Nothing is missed (FR-10).
**Deliverables** `platform/jobs.py` DB-backed queue with tenant fairness, `worker` entrypoint
(`python -m app.worker`), nightly/15-min schedules, `contexts/notify/`: in-app notifications,
email (SMTP; console in dev), WhatsApp + SMS provider interface (mock + one real adapter skeleton,
e.g. Gupshup/Twilio, disabled by default), templates (EN/HI/MR), digests, delivery log,
per-user channel preferences, quiet hours.
**Acceptance** fake-clock tests: T-7 reminder once only; overdue escalation chain; digest groups
by user; worker survives a failing job (retry with backoff, dead-letter); notifications API.
**Skills** workflow-engine, tenancy

### T13 · Evidence vault & licences register — sonnet · deps: T10
**Goal** Evidence or it didn't happen (FR-22, FR-23).
**Deliverables** `contexts/evidence/`: StorageBackend (LocalFS, S3-compatible via boto3 with MinIO
test), per-tenant prefix + envelope encryption, upload pipeline (allow-list, size cap, SHA-256,
AV hook, text extraction job via pypdf), versions (WORM), evidence slots per obligation and
auto-close check, retention + legal hold, signed download URLs; Licence register with validity →
renewal instance trigger (T10 hook), lead times from pack.
**Acceptance** upload/download round trip both backends; duplicate hash dedup; cannot overwrite a
version; instance cannot close with a missing required slot; licence expiring in 100 days
creates a CTO renewal instance due at expiry−120 → immediately open; isolation tests for files.
**Skills** compliance-domain, tenancy

### T14 · LLM gateway, redaction & AIAction — sonnet · deps: T02
**Goal** Port the proven TRIAX AI plumbing.
**Deliverables** per skills `llm-gateway` and `explainability`: providers mock/anthropic/openai/
azure_openai/gemini/ollama, capability routing + fallback, structured output, prompt registry
(`contexts/ai/prompts/<id>/v1.md`), Indian PII redaction (Aadhaar, PAN, UAN, IP no., GSTIN,
phone, email, names from tenant people list, patient identifiers), AIAction recorder + API +
feedback, per-tenant budget and `external_llm_allowed` switch, pricing.yaml.
**Acceptance** httpx MockTransport tests per provider (shape, parse, 429 retry, 500 fallback,
malformed JSON repair); redaction tests (≥ 20 Indian identifiers); mock deterministic; budget
exceeded → error; external disabled → ollama/mock only.
**Skills** llm-gateway, explainability

### T15 · Guided intake & computations — sonnet · deps: T13
**Goal** "What needs to be fed" made concrete (FR-18..21).
**Deliverables** `contexts/intake/`: input schemas from packs, xlsx template generator, upload
parser (header-row detection), column-mapping memory per tenant+schema, validations
(expression language shared with packs), computation library driven by pack `rates.yaml`
(PF incl. EPS/EDLI split & ceiling, ESI, MH PT slabs, MLWF, bonus, gratuity, BOCW cess), data
requests to provider users with their own due dates and reminders; instance "readiness" status.
**Acceptance** golden tests: PF/ESI for a 40-row payroll fixture match hand-computed values;
50%-wage-rule add-back test; validation report in plain words; mapping remembered on 2nd upload;
data request notifies provider and completes on upload.
**Skills** compliance-domain, compliance-packs

### T16 · AI content generation & document workflow — sonnet · deps: T14, T11
**Goal** Auto-generated compliance content that still goes through approval (FR-11 document, §6.2).
**Deliverables** `contexts/ai/drafting/`: template-driven drafts (Jinja2 deterministic sections +
LLM narrative slots) for the `ai_templates` named in packs (at least: pf_working, esi_working,
posh_policy, posh_notice, posh_annual_report, display_notices_bilingual, bmw_form_iv,
form_v_draft, cto_conditions report, drill_report, toolbox_talk, incident_intimation,
breach_intimation, privacy_notice, retention_schedule, board certificate narrative,
notice reply); "missing inputs" list; `Document` + versions with diffs; document workflow;
render PDF (WeasyPrint, with Windows fallback to HTML→PDF via Playwright if WeasyPrint libs are
missing) and DOCX (python-docx); approved render stored as evidence.
**Acceptance** every template renders with the mock provider for each demo tenant (snapshot
tests); AIAction on every draft; edit diff stored; approval of an AI draft without a human
reviewer impossible (test); PDF and DOCX open (python-docx reload, pypdf page count).
**Skills** llm-gateway, explainability, workflow-engine

### T17 · AI extraction & evidence verification — sonnet · deps: T14, T13
**Goal** Licence conditions → obligations; challans checked before the checker sees them (FR-24, FR-25).
**Deliverables** extraction schemas (CTO/consent, BMW authorisation, AERB licence, drug licence,
factory licence, PF/ESI/GST/TDS challans, acknowledgements); pipeline text → (OCR adapter if
scanned) → structured output with page anchors; proposed obligations review API (accept/edit/
reject each → register entries with source=licence); verifier rules (period, amount, codes,
headcount) + LLM fallback; mock provider returns realistic extractions for demo PDFs (generate
3 sample PDFs in `backend/tests/fixtures/docs/` with reportlab).
**Acceptance** extraction of the sample CTO yields ≥ 10 conditions with anchors (mock); accepting
3 creates 3 register entries citing the licence; challan mismatch (amount, period) flagged; all as
AIActions.
**Skills** llm-gateway, explainability, compliance-domain

### T18 · Compliance copilot (RAG) — sonnet · deps: T14, T09
**Goal** Ask anything, get cited answers (§6.1).
**Deliverables** chunking + embeddings (`VectorIndex`: numpy/SQLite, pgvector on Postgres; TF-IDF
fallback) over pack obligations/law excerpts and tenant-approved documents; copilot API with
tenant context (units, register) and citations; refusal style for legal advice ("consult your
CA/advocate"); suggested actions (open obligation, create instance) — never auto-executes.
**Acceptance** 15 golden questions (e.g. "Does ESI apply to our Ambernath unit?", "When is BMW
Form IV due?") answered with correct citations using mock + TF-IDF; tenant A documents never
retrieved for tenant B (isolation test).
**Skills** llm-gateway, explainability, tenancy

---

## Phase C — Product screens

### T19 · Onboarding wizard & register review UI — sonnet · deps: T07, T04
**Goal** The first 15 minutes (FR-1..5, UX §3.1–3.2).
**Deliverables** wizard (entity → units → workforce → premises & equipment → activities & waste →
licences held) with *Why we ask* per question, live obligation count via TS evaluator,
licence-upload hook (T17 later fills it), register page (group by category, filters, expand →
trace, cite, review badge, owner assignment, override request), diff acknowledgement page.
**Acceptance** e2e: complete wizard for the manufacturing demo profile → register shows the
expected count; change employees 19→21 → diff shows EPF; ui_check both themes + mobile; qa-verifier.
**Skills** stridenity-ui, compliance-domain

### T20 · Home, calendar & inbox UI — sonnet · deps: T12, T19
**Goal** "What is due" at a glance (FR-36, FR-16).
**Deliverables** Home (health score + factors, KPIs, 30-day timeline, unit × category heatmap,
threshold alerts, reg-update cards), Calendar (month/agenda, filters, ICS), Inbox (approvals with
SLA, OTP approve dialog, return-with-reason, sampling-gated bulk approve), notifications panel.
**Acceptance** e2e approve with OTP and return with reason; health score formula unit-tested and
explained in UI; ui_check + qa-verifier.
**Skills** stridenity-ui, workflow-engine

### T21 · Obligation workspace — sonnet · deps: T15, T16, T20
**Goal** The most important screen (UX §3.4).
**Deliverables** stepper Feed → Prepare → Review → Approve → File → Evidence; input checklist with
template download, upload, mapping, validation results, data requests; AI draft editor (markdown
with tracked changes, AIChip, Why drawer, missing-inputs panel); approval panel; file step
(portal link, reference number, ack upload, delay reason when late); evidence slots; timeline.
**Acceptance** e2e: PF instance from payroll upload to closed with evidence; POSH annual report
AI draft → edit → review → approve → PDF stored; late filing demands delay reason; ui_check + qa-verifier.
**Skills** stridenity-ui, explainability, workflow-engine

### T22 · Evidence & licences UI with extraction review — sonnet · deps: T17, T21
**Deliverables** vault table + filters + preview; licence register with validity bars; upload →
extraction review screen (fields, conditions list → accept/edit/reject → register).
**Acceptance** e2e on the sample CTO: 3 conditions accepted appear in register; ui_check + qa-verifier.
**Skills** stridenity-ui, explainability

### T23 · Audits, inspections, notices & CAPA — sonnet · deps: T21
**Deliverables** backend + UI: audit plans, engagements, checklist from register + audit points,
sampling helper, observation form (condition/criteria/cause/effect/risk), AI observation drafting,
CAPA board with capa workflow, inspection log, regulatory notices with reply deadline + AI reply
draft via document workflow, inspection-ready pack (zip of indexed PDF + evidence) per unit.
**Acceptance** API + e2e: observation → CAPA → verified → closed; notice reply approved; inspection
pack zip contains index.pdf + files (test); ui_check + qa-verifier.
**Skills** compliance-domain, workflow-engine, stridenity-ui

### T24 · Contractor compliance portal — sonnet · deps: T21
**Deliverables** contractor users (scoped), monthly submissions (wage sheet, ECR, challans,
attendance), gate attendance import, reconciliation (headcount, wages ≥ minimum, PF/ESI amounts),
exceptions → bill-release flag + export; month grid UI; mobile-friendly upload.
**Acceptance** recon test catches the planted ESI headcount mismatch; contractor A cannot see
contractor B (test); ui_check + qa-verifier.
**Skills** compliance-domain, tenancy, stridenity-ui

### T25 · Regulatory change management — sonnet · deps: T21
**Deliverables** change items (ops-authored, AI summary from pasted text/PDF), pack diff proposal,
tenant impact analysis, adoption via override workflow, change log per tenant, Reg. updates UI;
due-date extension kind applied to instances on adoption.
**Acceptance** sample extension moves due dates only after adoption; impact lists affected units;
ui_check + qa-verifier.
**Skills** compliance-packs, workflow-engine

### T26 · Reports & external auditor portal — sonnet · deps: T23, T24, T25
**Deliverables** monthly MIS, quarterly **board compliance certificate** (exceptions list,
document workflow, sign-off by Compliance Head + Director with OTP), audit report, overdue &
exceptions, licence expiry, contractor status, AI usage & acceptance; Excel + PDF; scheduled
email; external auditor role with time-boxed scoped read + observation raising.
**Acceptance** each report renders for each demo tenant (tests check key numbers); auditor access
expires (fake clock); ui_check + qa-verifier.
**Skills** compliance-domain, stridenity-ui

### T27 · Operator console (/ops) & SaaS operations — sonnet · deps: T26
**Goal** Stridenity runs the SaaS (FR-39..44, ADR-017).
**Deliverables** `/ops` app area (ops roles only): tenants list/detail, provision wizard (tier,
region, plan, packs, admin invite), suspend/reactivate/offboard (export → crypto-shred key),
plans & entitlements, usage meters (users, units, AI tokens, storage) + billing CSV, feature
flags, pack rollout (canary → all, rollback, pinning), health per tenant (errors, latency, job
lag), break-glass support sessions (reason, approval, 4 h expiry, logged into tenant audit log and
visible to tenant admin), announcement banner.
**Acceptance** e2e: provision tenant → admin invite → login; break-glass without approval denied;
with approval works and expires; tenant admin sees the access log; entitlement limit enforced
(e.g. units); ui_check + qa-verifier.
**Skills** tenancy, stridenity-ui

---

## Phase D — Demo, hardening, ship

### T28 · Demo tenants & planted stories — sonnet · deps: T27
**Deliverables** `python -m app.demo.seed --reset` creating the 3 PRD §7 tenants (pooled tier) with
people, units, facts, licences (some expiring), 13 months of instances with realistic statuses,
evidence PDFs (generated), contractors, audits, notices, AI actions, a sample reg change, and the
6 planted stories; `docs/DEMO_SCRIPT.md` (15-minute walkthrough) verified by a Playwright spec.
**Acceptance** seed deterministic (same seed → same counts/hashes); each planted story has a test;
`demo.spec.ts` walks the script green via ui_check `--e2e`.
**Skills** synthetic-data, compliance-domain

### T29 · Languages & site-user PWA — sonnet · deps: T28
**Deliverables** i18n framework (EN, HI, MR) for site-user/contractor screens and generated
notices; PWA manifest + service worker; offline capture queue for checklists/photos with sync;
low-bandwidth mode.
**Acceptance** e2e offline capture syncs after reconnect; HI/MR notices render (fonts); Lighthouse
PWA installable check; ui_check mobile.
**Skills** stridenity-ui

### T30 · Security, isolation & DPDP hardening — opus · deps: T29
**Deliverables** full cross-tenant suite across all tiers on Postgres (repos, APIs, files, search,
jobs, exports); rate limits; security headers/CSP; upload hardening; secrets audit; dependency
audit; ASVS L2 checklist; `docs/SECURITY.md` (threat model, DPDP processor obligations, breach
runbook, data residency, retention/deletion, break-glass policy).
**Acceptance** isolation suite green in CI Postgres job; no high findings from `pip-audit` /
`npm audit --omit=dev` (or documented); code-reviewer security pass; SECURITY.md complete.
**Skills** tenancy, verification

### T31 · Packaging & deployment — sonnet · deps: T30
**Deliverables** Dockerfiles (api/worker, web with nginx), `docker-compose.yml` (web, api, worker,
postgres, minio), prod settings, migrations job, `deploy/oci/README.md` + `deploy/aws/README.md`
(managed Postgres, object storage, KMS, LB/WAF, India region), `docs/DEPLOY.md`, Windows
native run guide for demos, `scripts/make_release.py` (sanitised zip, scans for secrets and
internal references).
**Acceptance** `docker compose up` healthy and demo seed works (if Docker available; otherwise
build-only check documented); release zip passes its own scan.
**Skills** verification

### T32a · Final quality gate & performance — sonnet · deps: T31
Full `/verify`, perf targets from PRD §8 measured and recorded.
**Skills** verification

### T32b · Code & security review — opus · deps: T32a
code-reviewer over each context (one slice per session), fix high/medium, backlog the rest.
**Skills** verification, tenancy

### T32c · UI/accessibility pass & demo rehearsal — sonnet · deps: T32b
qa-verifier across all pages both themes + mobile; DEMO_SCRIPT rehearsal; final summary in PROGRESS.md.
**Skills** stridenity-ui, verification
