# Architecture & product decisions (ADRs)

Format: **ADR-NNN · Title** — Status · Context → Decision → Consequences. New ADRs are appended;
superseded ones stay with a pointer.

**ADR-001 · Python FastAPI + React/Vite/TypeScript** — Accepted.
Context: AI-heavy product, same team built TRIAX on this stack with a proven Claude Code build
kit; HMS uses Java/Spring but compliance has no shared runtime with it.
Decision: Python 3.12 + FastAPI + SQLAlchemy 2.0 (sync sessions) + Pydantic v2; React 18 + Vite +
TS strict + Tailwind + Radix primitives + TanStack Query.
Consequences: reuse of TRIAX patterns (LLM gateway, AIAction, ui_check, build loop). If HMS
integration is needed later it is via REST/webhooks.

**ADR-002 · Modular monolith with service boundaries, not microservices on day 1** — Accepted.
Context: user asked for microservices "if needed". MSME SaaS v1 load is small; microservices
multiply deployment, consistency and debugging cost and slow an AI-driven build.
Decision: one codebase, two processes (api, worker); bounded contexts own their tables and talk
via service interfaces + outbox events (ARCHITECTURE §1–2). Lint rule (import-linter) forbids
cross-context imports except `contexts/<x>/api.py`.
Consequences: extraction to a service is mechanical when justified (ai, notify, evidence first).

**ADR-003 · Regulatory content is data (packs), never code** — Accepted.
Obligations, rules, due rules, rates, formulas, templates, penalties live in versioned YAML packs
(`content/packs/<jurisdiction>/<pack>/`), validated by a schema and loaded into the DB.
Consequences: Stridenity content team can update without deploys; every change is diffable and
adoptable per tenant; core stays region-agnostic (GCC later = new packs).

**ADR-004 · JSON rule language for applicability** — Accepted.
Small declarative `all/any/not + leaf(fact, op, value)` evaluated by a pure function with
traces, instead of a general rules engine (Drools, json-logic libs). Explainability and
`needs_input` semantics are first-class; unit-testable; same evaluator ported to TS for the
onboarding preview.

**ADR-005 · DB-backed jobs and outbox; no Redis/Celery in v1** — Accepted.
Volumes are small; one fewer moving part on Windows demos and single-VM installs. Interface
allows swapping to Redis/RQ or a broker later.

**ADR-006 · SQLite for dev/demo, PostgreSQL 16 for production; tests on both in CI** — Accepted.
Portable SQLAlchemy; dialect specifics only in `db/dialect.py`; WAL + busy_timeout on SQLite;
CI runs the backend suite on SQLite and a Postgres service container.

**ADR-007 · Managed multi-tenant SaaS with tiered isolation** — Accepted (revised 2026-10-16).
Context: ANUPAL is a SaaS operated by Stridenity on a cloud provider; every tenant's data must be
isolated, and some tenants (hospitals, larger groups) will demand stronger isolation.
Decision — one codebase, three isolation tiers chosen per tenant at provisioning:
- **Pooled (default)**: shared Postgres schema; `tenant_id` on every row; repository base enforces
  `TenantContext`; **Postgres RLS** (`SET app.tenant_id` per transaction) as a second wall;
  per-tenant data-encryption key (envelope encryption via provider KMS) for evidence objects and
  sensitive columns; object keys under `tenants/<tenant_id>/`.
- **Schema-isolated**: own Postgres schema (`t_<id>`), same code, `search_path` set per request.
- **Dedicated**: own database (and optionally own bucket/KMS key); same app fleet, routed by the
  tenant registry.
A **tenant registry** (control-plane DB) maps tenant → tier, DSN/schema, region, KMS key, plan,
status. Migrations run per schema/DB by an operator job. Cross-tenant tests run against all tiers.
Consultant/CA-firm partners are users with memberships in many tenants — never shared data.
Consequences: isolation is a provisioning choice, not a fork; the pooled tier keeps cost low for
MSMEs; dedicated tier answers procurement questionnaires.

**ADR-008 · AI drafts, humans decide; every AI output is an AIAction** — Accepted.
No AI path can file, pay, close or approve. AI outputs carry provenance and enter the
`document` workflow. Mock provider is the default so the product demos with zero keys.

**ADR-009 · Workflow templates are snapshotted into runs** — Accepted.
Editing a template/approval matrix never changes in-flight runs; the run stores its template.

**ADR-010 · Hash-chained, append-only audit log** — Accepted.
Tamper evidence for auditors; verifier CLI; exported with the inspection pack.

**ADR-011 · Sync DB sessions; async only at the edges** — Accepted (from TRIAX).
Plain `def` routes for DB work; AI/HTTP calls async; DB from async code only via
`asyncio.to_thread` with a short-lived session; never hold a session across an LLM await.

**ADR-012 · UI shell early** — Accepted (TRIAX lesson).
App shell + design system land in Phase A so every later feature task ships its screen and is
verified visually with `scripts/ui_check.py`.

**ADR-013 · Monorepo subfolder `Compliance/`** — Accepted.
The GitHub repo `LearningX-BK/Stridenity` is Stridenity's product monorepo; this product lives
in `Compliance/`. The local folder `C:\GenAIGenerated\Stridenity\Compliance` is bound to it via
a sparse checkout rooted at `C:\GenAIGenerated\Stridenity` (`scripts/setup-git-sync.ps1`), so
sibling local folders (e.g. HMS) are not touched. Root-level `CLAUDE.md` + `.claude/` route
cloud sessions into `Compliance/`.

**ADR-014 · One builder at a time, enforced by a lock in tasks.json** — Accepted.
Local loop and cloud sessions both claim `builder` in `docs/plan/tasks.json` before working; a
fresh claim (< 3 h) by the other side makes a session exit with `TASK_BUSY`. Prevents the
merge mess of two agents on one task.

**ADR-015 · India data residency by default** — Accepted.
Prod deploy targets an Indian region; object storage and DB in-region; LLM calls are the only
cross-border flow and are redacted; tenants can disable external LLMs (ollama/mock).

**ADR-016 · Content review gate** — Accepted.
`review_status` on obligations: `sme_pending` → `sme_reviewed` → `published`. Unreviewed
obligations are usable (marked "Draft") in demo/pilot tenants only; production tenants get only
`published` items unless the tenant explicitly opts in.

**ADR-017 · Control plane vs data plane; Stridenity operator console** — Accepted.
Control plane (`platform/` + `contexts/tenancy/`): tenant registry, plans & entitlements, usage
metering (users, units, AI tokens, storage), feature flags, pack rollout (canary tenants first),
provisioning/deprovisioning jobs, per-tenant backup/export/restore, health. Data plane: the
tenant-scoped contexts. Operator console at `/ops` for Stridenity staff (separate role family
`ops_*`, MFA mandatory). Support access to tenant data is **break-glass**: ticket reference +
tenant admin approval (or emergency override with owner notification), time-boxed (default 4 h),
every read logged to the tenant's audit log, which the tenant can see.

**ADR-018 · Cloud-agnostic container deployment** — Accepted.
Images: `api`, `worker`, `web`. Targets: single VM Docker Compose (pilot), then managed
Kubernetes/containers (OKE, EKS, AKS) with managed Postgres, object storage and KMS of the chosen
provider, behind a provider load balancer + WAF. Provider specifics only in `deploy/<provider>/`
(Terraform later). India region default (ADR-015); a region per tenant is a registry field so
GCC tenants can be hosted in-region later.

**ADR-019 · OCI as the first hosting provider** — Accepted (2026-10-16).
Production and pilots run on Oracle Cloud Infrastructure, India region (Mumbai primary,
Hyderabad for DR/backups): OKE (or a VM with Docker Compose for the pilot), OCI Database with
PostgreSQL, Object Storage, OCI Vault for per-tenant keys, Load Balancer + WAF. Provider
specifics stay in `deploy/oci/`; the app keeps S3-compatible storage and KMS interfaces so AWS or
Azure remain possible (ADR-018).

**ADR-020 · State rollout order** — Accepted (2026-10-16).
Maharashtra → Gujarat → Andhra Pradesh → Tamil Nadu → Odisha. Each state is a new jurisdiction
pack (PT, LWF, Shops & Establishments, fire, lifts, SPCB practice, state labour-code rules,
holidays) built by its own task, never by changing the core.

**ADR-021 · Pricing model deferred; entitlements stay generic** — Accepted (2026-10-16).
Commercial model is not decided (likely per company/tenant). The plans/entitlements model in the
control plane must not hard-code a unit of pricing: plans hold limits (units, users, AI tokens,
storage, modules) and metering records all of them, so per-company, per-unit or per-employee
pricing can be configured later without code changes.

**ADR-022 · Healthcare pilot covers clinics and nursing homes** — Accepted (2026-10-16).
First pilots: small healthcare (clinics, nursing homes, small hospitals) and a small
manufacturer. The healthcare pack must work for a 0-bed clinic (BMW, PC-PNDT, AERB, drug licence,
Shops & Establishments, fire where applicable) as well as a nursing home; onboarding offers a
"clinic" quick profile that asks ≤ 12 questions.
