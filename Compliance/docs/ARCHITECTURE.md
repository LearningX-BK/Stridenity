# ANUPAL — Architecture

ANUPAL is a **managed multi-tenant SaaS operated by Stridenity** on a cloud provider; each
tenant's data is isolated (pooled + RLS by default; schema or dedicated DB per tenant on demand).

§1 Shape · §2 Bounded contexts · §3 Data model · §4 Rules, calendar & workflow engines ·
§5 AI layer · §6 Storage & documents · §7 Security & tenancy · §8 Deployment · §9 API conventions

## 1. Shape: a microservice-ready modular monolith (ADR-002)

```
                    ┌──────────────────────── web (React PWA) ────────────────────────┐
                    │  app shell · onboarding · register · calendar · inbox · workspace │
                    │  evidence · audits · contractors · reg-changes · admin · reports  │
                    └───────────────────────────────┬──────────────────────────────────┘
                                                    │ /api/v1 (JSON, OpenAPI)
┌─────────────────────────────── api process (FastAPI) ───────────────────────────────────┐
│ identity │ org │ content │ applicability │ calendar │ workflow │ evidence │ intake │ audit │
│ contractor │ regchange │ ai (gateway, actions, rag) │ notify │ reporting │ admin          │
│        each context = package with its own tables, service API, events (outbox)          │
└──────────────┬─────────────────────────────┬────────────────────────────┬───────────────┘
               │ SQLAlchemy                  │ outbox → job queue          │ S3 API
        ┌──────▼──────┐               ┌──────▼──────────────┐       ┌─────▼──────┐
        │ SQLite (dev) │               │ worker process       │       │ local FS   │
        │ Postgres 16  │               │ scheduler (calendar, │       │ / MinIO /  │
        │ (prod)       │               │ reminders, escalate),│       │ S3 / OCI   │
        └─────────────┘               │ AI jobs, extraction, │       └────────────┘
                                      │ notifications, PDFs  │
                                      └──────────────────────┘
```
Two deployable processes from one codebase (`api`, `worker`). Contexts talk through **service
interfaces and domain events** (transactional outbox table → in-process dispatcher; Redis/
RabbitMQ only if scale requires — ADR-005). Any context can be lifted into its own service
later because: it owns its tables (no cross-context joins in repositories; read models via
events), its public API is a Python protocol mirrored by REST, and events are versioned JSON.
First candidates to extract when load demands: `ai` (GPU/LLM latency), `notify`, `evidence`.

## 2. Bounded contexts (backend/app/contexts/<name>/)

| Context | Owns | Key services |
|---|---|---|
| `identity` | users, roles, memberships, sessions, OTP, delegations | auth (password + OTP), RBAC check `can(user, action, resource)`, unit scoping |
| `org` | tenants, legal entities, units, departments, people (lightweight HR master), contractors, profile facts (versioned) | profile CRUD, fact history, threshold proximity |
| `content` | packs, pack versions, obligations, input schemas, templates, licence types, holidays, authorities | pack loader/validator, search, diff |
| `applicability` | register entries per unit (obligation × unit), overrides, evaluations | evaluate(unit) → entries + traces; re-evaluate on profile/pack change; diff |
| `calendar` | instances, due rules, recurrence, holiday calendars, extensions | generate(horizon), shift rules, extensions apply |
| `workflow` | templates, approval matrix, workflow runs, steps, actions, SLA timers | start(instance), act(step, action), escalate, SoD guard |
| `evidence` | evidence items, versions, slots, licences register, retention | upload (hash, scan hook), link, verify, renewal triggers |
| `intake` | data requests, uploads, column mappings, validation results, computations | template xlsx, parse, map, validate, compute |
| `audit` | audit plans, engagements, checklists, observations, CAPA, inspections, notices | plan, checklist-from-register, sampling, CAPA lifecycle, inspection pack |
| `contractor` | contractor periods, submissions, reconciliations | portal submissions, gate vs ECR recon |
| `regchange` | change items, impacts, adoptions | impact(tenant), adopt |
| `ai` | AIActions, prompts registry, embeddings index, provider configs, budgets | gateway, record_action, rag.search, drafts, extraction |
| `notify` | notifications, channels, templates, digests, delivery log | email, WhatsApp (provider iface), SMS, in-app |
| `reporting` | report runs, scheduled reports | MIS, board certificate, audit report, exports |
| `platform` | audit log (hash chain), jobs, outbox, settings | append_audit, enqueue, dispatch |
| `tenancy` (control plane) | tenant registry, tiers & routes, plans/entitlements, usage meters, feature flags, pack rollouts, break-glass sessions | resolve(tenant), provision, migrate, meter, flag, rollout, export/restore |

## 3. Core data model (abridged; all tables have `id` (UUIDv7), `tenant_id`, `created_at`, `created_by`, `updated_at`, `version`)

```
Tenant 1─* LegalEntity 1─* Unit 1─* ProfileFactValue (fact_key, value, valid_from, set_by, source)
Unit *─* Pack (enabled packs: jurisdiction + sector)
Pack 1─* PackVersion 1─* Obligation (key "IN.SS.EPF.ECR", title, category, law{act,section,rule},
        authority, jurisdiction, frequency, due_rule(JSON), applies(JSON rule), risk, penalty{text,formula},
        input_schema(JSON), evidence_slots(JSON), owner_role, workflow_hint, ai_templates[],
        audit_points[], source_url, verified_on, review_status, effective_from, effective_to)
RegisterEntry (unit, obligation_key, pack_version, status applicable|not_applicable|needs_input,
        trace(JSON), override{by, reason, approved_by}, owner_user, checker_user, approver_user)
Instance (register_entry, period_start, period_end, due_at, state, risk, owner, filed_at,
        delay_reason, late_fee, closed_at)
WorkflowRun (instance|document|override|capa, template_snapshot JSON, current_step) 1─* StepAction
        (step_no, actor, on_behalf_of, action, comment, otp_verified, at, ip, device)
EvidenceItem (sha256, storage_key, mime, size, type, ref_no, amount, period, issued_by,
        valid_from, valid_to, extracted JSON, version_of) *─* Instance (slot)
Licence (unit, licence_type, number, valid_from, valid_to, conditions[] → proposed obligations)
DataRequest (instance, input_key, provider_user, due_at, status) ; Upload ; Mapping ; ValidationResult
Document (kind policy|notice|reply|working|certificate, title, lang, body(markdown), version,
        status, ai_action_id?) ; DocumentVersion (diff)
AuditPlan 1─* Engagement 1─* ChecklistItem ; Observation 1─1 Capa
Inspection ; RegulatoryNotice (reply_due_at, document_id)
Contractor ; ContractorPeriod ; Reconciliation
ChangeItem ; ChangeImpact (tenant, unit, obligation, before, after) ; Adoption
AIAction (capability, mode, provider, model, prompt_id@ver, input_summary(redacted), evidence[],
        rationale, confidence, usage, cost, latency, status, verdict, edited_diff)
AuditLog (seq, tenant, actor, action, entity, entity_id, before_hash, after_hash, prev_hash, hash)
```
Money as integer paise; dates as `date`; timestamps UTC; display in tenant TZ (Asia/Kolkata).

## 4. Engines

### 4.1 Rules (applicability) — `contexts/applicability/rules.py`
JSON rule language (same as `content/seed/obligations.seed.json`): `{"all":[…]}`, `{"any":[…]}`,
`{"not":{…}}`, leaf `{"fact","op","value"}` with ops `eq ne gt gte lt lte in contains
not_contains exists`. Pure function `evaluate(rule, facts) -> (bool, Trace)`; a trace records
each leaf with fact label, actual value and result, so the UI can render *"Applies because
employees = 46 ≥ 20"* and *"Would stop applying if employees < 20"*. Unknown fact → result
`needs_input` (never silently false). Derived facts (e.g. `total_workers`) computed in
`org.facts.derive()`. Rules are validated at pack load (unknown fact keys/ops fail the build).

### 4.2 Calendar — `contexts/calendar/rules.py`
`due_rule` types: `monthly_day{day, exceptions}`, `month_end`, `dates{["MM-DD"]}`,
`annual{month,day}`, `quarterly_offset{days_after_quarter}`, `event_within{event, days,
working_days}`, `before_expiry{licence, days}`, `monthly_selfcheck`, `one_time`, `fixed{date}`.
Generation horizon: rolling 13 months; idempotent (unique key: register_entry + period).
Holiday shift per authority (`next_working_day` | `previous_working_day` | `none`) using
national + state holiday calendars (content data). Government extensions are `ChangeItem`s of
kind `due_date_extension` that rewrite `due_at` on matching instances after adoption.

### 4.3 Workflow — `contexts/workflow/engine.py`
Template = ordered steps (see `docs/WORKFLOWS.md`). Engine is a pure state machine
`transition(run, action, actor) -> (run', events)` + persistence; guards: role/scope, SoD,
OTP for approver steps, required fields (return needs reason). Template **snapshot** copied
into each run (later template edits never mutate in-flight runs). SLA timers via scheduled
jobs → escalation events → notify.

### 4.4 Scheduler/jobs — `platform/jobs.py`
DB-backed job table (`run_at`, `kind`, `payload`, `attempts`, `locked_until`) polled by the
worker; idempotent handlers; nightly: calendar roll-forward, renewal triggers, threshold
proximity, digests; every 15 min: reminders/escalations. No Celery/Redis in v1.

## 5. AI layer — `contexts/ai/` (skills `llm-gateway`, `explainability`)
- **Gateway**: providers `mock` (default, deterministic), `anthropic`, `openai`, `azure_openai`,
  `gemini`, `ollama` (on-prem). Capability routing (`draft.*`, `extract.*`, `summarise.*`,
  `classify.*`, `copilot.answer`) with fallback chains; per-tenant budget; tenant switch
  `external_llm_allowed=false` forces ollama/mock.
- **Redaction** of PII (names, Aadhaar, PAN, UAN, phone, email, patient identifiers) before any
  call; re-hydration after.
- **RAG**: chunks of obligation texts, law excerpts in packs, tenant's approved documents;
  embeddings behind `VectorIndex` (numpy cosine on SQLite; pgvector on Postgres); TF-IDF
  fallback for tests/offline. Citations are obligation keys + source URLs + document anchors.
- **Extraction**: PDF text (pypdf) → if scanned, OCR adapter (Tesseract optional / LLM vision) →
  structured output schema per document type (CTO, BMW authorisation, challan, ack, licence) with
  page anchors; each condition → proposed obligation (draft) for human review.
- **Drafting**: templates (Jinja2 Markdown) with deterministic sections + LLM narrative slots;
  output → `Document` with AIAction; rendering to PDF (WeasyPrint) / DOCX (python-docx).

## 6. Storage & documents
`StorageBackend` interface: `LocalFS` (dev, `data/objects/`), `S3Compatible` (MinIO/AWS/OCI).
Keys `tenant/<id>/<yyyy>/<sha256>`; dedup by hash; server-side encryption; signed URLs (5 min).
Upload pipeline: size/type allow-list → hash → AV-scan hook (no-op in dev, ClamAV adapter) →
store → text extraction job. Retention per evidence type (pack data); legal hold flag.

## 7. Multi-tenancy, security & isolation (ADR-007, ADR-017)

### 7.1 Planes
```
          Stridenity operator console (/ops)          Tenant users (web/PWA, contractor portal)
                        │                                              │
            ┌───────────▼───────────┐                      ┌───────────▼────────────┐
            │ CONTROL PLANE          │  tenant resolve      │ DATA PLANE (api, worker)│
            │ tenant registry, plans,│◄─────────────────────│ TenantContext per req.  │
            │ metering, flags, pack  │  (cached, signed)    │ → DSN/schema + KMS key  │
            │ rollout, provisioning, │                      └───────┬────────┬────────┘
            │ backups, health        │                pooled schema │ t_<id> │ dedicated DB
            └────────────────────────┘                (RLS)         │ schema │ per tenant
```
- **Tenant resolution**: subdomain (`<slug>.anupal.app`) or token claim → registry lookup →
  `TenantContext{tenant_id, tier, db_route, kms_key, region, plan, flags}`. A request never runs
  without one (middleware rejects); background jobs carry it in the payload.
- **Pooled tier**: `tenant_id` filter in repository base **and** Postgres RLS policies
  (`USING (tenant_id = current_setting('app.tenant_id')::uuid)`), set with `SET LOCAL` per
  transaction. The app DB role cannot bypass RLS; migrations use a separate owner role.
- **Schema / dedicated tiers**: engine/schema chosen from the registry; same migrations applied
  per target by `ops migrate --all` (tracked per tenant in the registry).
- **Object storage**: `tenants/<tenant_id>/…` prefix (pooled) or own bucket (dedicated);
  envelope encryption with a per-tenant data key wrapped by provider KMS; signed URLs only.
- **Caches, search & vectors** are keyed by tenant; vector index per tenant (pgvector table with
  RLS, or per-schema).
- **Noisy neighbours**: per-tenant rate limits, AI token budgets, job-queue fairness
  (round-robin by tenant), storage quotas — all plan entitlements.
- **Tests**: a cross-tenant suite creates two tenants per tier and asserts every repository,
  API list/get, file download, search and job handler cannot cross; runs in CI on Postgres.

### 7.2 Identity & access
Email/phone + password (argon2) or OTP; JWT access (15 min) + rotating refresh (httpOnly
cookie); OTP step-up for approver actions; optional SSO (OIDC) per tenant later. Users can belong
to several tenants (consultants) — the active tenant is explicit in the token. AuthZ: role
permissions + unit scope + record-level (contractor sees own submissions; external auditor
time-boxed). Ops roles (`ops_admin`, `ops_support`, `ops_content`) are a separate family with
MFA mandatory and **no tenant data access** except break-glass (ADR-017).

### 7.3 Operating the SaaS (control plane features)
Provision tenant (tier, region, plan, packs, admin invite) · suspend / reactivate / offboard
(export then crypto-shred key) · plan & entitlements (units, users, AI tokens, storage,
features) · usage metering → billing export · feature flags · content-pack rollout (canary
tenants → all, with rollback) · per-tenant backup & point-in-time restore (dedicated) / logical
export-import (pooled) · health & SLO dashboard (error rate, latency, job lag per tenant) ·
announcement banners · break-glass support sessions with tenant-visible log.

### 7.4 Other controls
Hash-chained audit log per tenant (verifier CLI); secrets encrypted (Fernet locally; KMS in
cloud; `ANUPAL_SECRET_KEY`); OWASP ASVS L2; WAF at the edge; AV-scan hook on uploads; DPDP:
data residency, tenant data export/delete, processor role, breach runbook (`docs/SECURITY.md`, T28).

## 8. Deployment (ADR-018)
- **Dev/demo (Windows or Linux)**: SQLite (pooled tier only, RLS emulated by the repository
  filter) + LocalFS + mock LLM; `scripts/dev.ps1` / `dev.sh`. Ports: **API 8091, UI 5191**
  (dev); **API 8191, UI 5291** (`scripts/ui_check.py`) — avoids TRIAX (8077/5177).
- **Pilot**: one VM, Docker Compose — `web` (nginx + SPA), `api`, `worker`, `postgres`, `minio`.
- **Production SaaS**: provider-managed containers/Kubernetes (OKE/EKS/AKS), managed Postgres
  (HA, PITR), object storage, KMS, load balancer + WAF, India region; observability via
  OpenTelemetry → provider monitoring. Provider specifics only in `deploy/<provider>/`.
- CI: GitHub Actions at repo root, path-filtered to `Compliance/**` — backend on SQLite **and**
  Postgres (RLS + cross-tenant suite); frontend typecheck/lint/test/build; images built on tags.

## 9. API conventions
`/api/v1/<context>/...`; tenant from token; cursor pagination (`?cursor=&limit=`); filtering
via query params; errors RFC 7807 problem+json; idempotency key header for POSTs that create
instances/evidence; OpenAPI → generated TS client (`frontend/src/lib/api/`); every AI endpoint
returns `{result, action}` (AIActionSummary).
