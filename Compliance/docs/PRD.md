# ANUPAL — Product Requirements (v1)

> **Working name:** ANUPAL (from *anupālan*, अनुपालन — "compliance"). A Stridenity Solutions
> Private Limited product. The name lives in one place (`backend/app/core/config.py: APP_NAME`,
> `frontend/src/config.ts`) so it can be changed without a refactor.
>
> **One-line pitch:** An AI compliance operating system for Indian MSMEs in compliance-heavy
> sectors — it works out *what applies to you*, tells you *what to feed it*, drafts the
> paperwork, routes it through *your* maker-checker-approver chain, and keeps an
> inspection-ready evidence trail.

Sections: §1 Problem · §2 Users & roles · §3 Principles (auditor's view) · §4 Scope v1 ·
§5 Functional requirements · §6 AI capabilities · §7 Demo data · §8 Non-functional ·
§9 Out of scope / later · §10 Success metrics · §11 Open questions

---

## 1. Problem

An Indian MSME factory, hospital, builder or electrical contractor faces 150–400 recurring
compliance obligations across central labour codes, state rules, environment, fire, electrical
safety, tax and corporate law — plus licence conditions (Consent to Operate, AERB, drug licence)
that each create their own obligations. Today this lives in a consultant's Excel, a WhatsApp
group and a cupboard of files. The failure modes an auditor sees every time:

1. **Applicability is guessed.** Nobody has mapped *which* laws apply to *which* unit as
   headcount, contract labour, equipment and activities change (crossing 10/20/50 workers,
   installing a boiler or X-ray, starting a construction project).
2. **Licence conditions are ignored.** A CTO has 30–80 conditions; a typical MSME tracks the
   expiry date and nothing else.
3. **No maker-checker.** The person who files is the person who checks; there is no evidence
   that the authorised signatory approved.
4. **Evidence is missing or unlinkable** — challans without the ECR, returns without
   acknowledgements, training without attendance sheets.
5. **Contractors are the blind spot** — principal-employer liability for contract workers' PF/ESI
   and wages.
6. **Regulatory change** (labour codes in force from 21 Nov 2025, DPDP Rules, Income-tax Act
   2025, Boilers Act 2025, Jan Vishwas decriminalisation) is not translated into "what changes
   for *my* unit".
7. **Inspection panic** — when the Inspector-cum-Facilitator visits, nobody can produce the pack.

## 2. Users & roles

| Role | Who in an MSME | Can do |
|---|---|---|
| **Owner / Director** | Promoter, MD | Sees everything; final approver for high-risk items; signs board compliance certificate |
| **Compliance Head** | Compliance officer, CA/CS in-house, HR-admin head | Configures applicability, owners, approval matrix; approves; runs audits |
| **Approver** | Plant head, Medical Superintendent, Project Manager | Approves items for their unit/function |
| **Checker** | Accounts head, HR manager, EHS manager | Reviews maker's work, returns or forwards |
| **Maker** | HR executive, accountant, EHS officer, biomedical engineer, site supervisor | Feeds data, prepares, uploads evidence |
| **Site user** | Supervisor, nurse in-charge, safety steward | Mobile: checklists, photos, incident/near-miss, training attendance |
| **Contractor** | Labour contractor, sub-contractor | Portal: uploads PF/ESI challans, wage sheets, licences for *their* workers only |
| **External auditor / Consultant** | CA firm, compliance consultant, NABH assessor | Read-only (scoped, time-boxed) access; can raise observations |
| **Stridenity admin** | Platform staff | Tenant provisioning, content packs, support (no tenant data by default — break-glass with audit) |

Segregation of duties (SoD) is enforced by the system: for any one obligation instance,
maker ≠ checker ≠ approver unless the tenant explicitly enables "small-team mode" (≤ 5 users),
which is then shown on every report as a control weakness.

## 3. Principles — how an auditor would want it built

1. **Applicability is explicit and explained.** Every obligation on a unit's register shows
   *why it applies* ("Applies because: Maharashtra · 46 employees ≥ 20 · factory with power")
   and every exclusion shows *why not*, with an approved justification when a user overrides.
2. **Obligation ≠ task.** The *obligation* (law, section, authority, frequency, evidence) is
   content; the *instance* (period, due date, owner, status, evidence) is work. Never mix.
3. **Evidence or it didn't happen.** An instance cannot close without the evidence the obligation
   demands (e.g. challan + ECR + bank debit for PF). Evidence is hashed, versioned and immutable.
4. **Every approval is attributable** — who, when, from what device, with what comment, against
   which version of the document. Immutable, hash-chained audit trail.
5. **AI drafts, humans decide.** AI never files, pays, or closes anything. Every AI output is an
   explained, versioned draft that enters the same approval workflow as human work.
6. **Content is cited and versioned.** Every obligation cites the law/rule/notification, carries
   `effective_from/to`, a `source_url`, `verified_on` and an SME review status. Unreviewed
   content is visibly labelled "Draft — pending SME review".
7. **Guide, don't just remind.** For each obligation the app says *what data is needed, from
   whom, in what format*, provides the template, and validates what was fed before it reaches
   the checker.
8. **Small-business ergonomics.** Mobile first for site users, Hindi/Marathi (later Odia, Gujarati,
   Tamil), WhatsApp reminders, works on a ₹10k Android phone on 4G, offline capture.
9. **Region-agnostic core.** India is the first *jurisdiction pack*; nothing in the core assumes
   India (currency, calendar, ID formats, authorities are pack data).

## 4. Scope v1

**Jurisdictions:** India — Central + **Maharashtra** fully; then Gujarat → Andhra Pradesh → Tamil Nadu → Odisha
(ADR-020); pack structure ready for any state.
**Sectors (packs):** Manufacturing (factory), Healthcare (clinic / nursing home / small hospital /
diagnostic centre — clinics without beds are a first-class profile), Construction (building & other construction work, RERA projects), Electrical
(contractors & installations). Cross-sector: labour & social security, tax & corporate,
environment, fire & building safety, POSH, data protection (DPDP).
**Tenancy & operation:** managed multi-tenant SaaS hosted by Stridenity on a cloud provider. A tenant =
a customer business group with ≥ 1 legal entity and ≥ 1 unit; each tenant's data is isolated
(pooled with row-level security by default; own schema or own database for tenants that need it).
Stridenity operates the platform through an operator console (§5.11).

## 5. Functional requirements

### 5.1 Onboarding & applicability (the first 15 minutes must impress)
- **FR-1** Guided onboarding wizard per legal entity → units: legal form (Pvt Ltd/LLP/
  partnership/proprietorship), CIN/LLPIN, GSTIN, PAN, Udyam number & category, state & district,
  sector(s) & activities, headcount (permanent / fixed-term / contract / apprentices; women;
  night-shift women), wage bands, premises (owned/leased, floors, built-up area, height),
  equipment & hazards (boiler, pressure vessels, DG set, lifts, hazardous chemicals, X-ray/CT,
  ultrasound, autoclave), waste streams (hazardous, bio-medical, e-waste, plastic packaging),
  licences already held. Each question has help text explaining *why it is asked*.
- **FR-2** Smart prefill: GSTIN/CIN/Udyam lookup (adapter interface; mock in v1), upload of
  existing licences → AI extraction (§6.3) pre-answers questions.
- **FR-3** **Applicability engine** evaluates every obligation in the enabled packs against the
  profile and produces the **Compliance Register** per unit: applicable / not applicable /
  needs-input, each with the rule trace in plain language.
- **FR-4** Overrides: mark applicable→NA or NA→applicable with justification + attachment; goes
  to Compliance Head approval; logged; shown in audit reports.
- **FR-5** Re-evaluation on profile change (e.g. headcount crosses 20 → EPF becomes applicable)
  with a **"What changed" diff** that must be acknowledged. Threshold proximity alerts
  ("you are at 18 employees — EPF applies from 20").

### 5.2 Compliance register & calendar
- **FR-6** Register views: by unit, law/category, authority, owner, risk; filters; export Excel.
- **FR-7** Calendar engine generates instances from obligation frequency rules: monthly,
  quarterly, half-yearly, annual (FY or calendar), event-driven (on joining, on accident, on
  change in occupier, N days before licence expiry), one-time (registration), continuous
  (display/notice, register maintenance — verified by periodic self-check).
- **FR-8** Due-date rules: fixed day, last working day, "N days after period end", "within N days
  of event", holiday shift (configurable per authority: before/after/none), and government
  extensions (a regulatory-change item can move a due date for all tenants after approval).
- **FR-9** Owner assignment by default role per obligation category, overridable per unit;
  delegation during leave with date range.
- **FR-10** Reminders: T-15/T-7/T-3/T-1/T0 (configurable), overdue daily, escalation to the
  next level at T+1 and Owner at T+7; channels in-app, email, WhatsApp (provider interface),
  SMS fallback; daily/weekly digest.

### 5.3 Workflow & internal approval
- **FR-11** Configurable workflow templates (see `docs/WORKFLOWS.md`): *Standard* (Maker →
  Checker → Approver → File → Close), *Fast* (Maker → Approver), *High-risk* (Maker → Checker →
  Approver → Owner), *Event* (Reporter → Investigator → Approver, for accidents/incidents),
  *Override/NA* (Requester → Compliance Head), *Document* (Drafter → Reviewer → Approver →
  Publish) for policies/SOPs/AI drafts.
- **FR-12** **Approval matrix**: rules choose the template by risk rating, category, unit,
  amount (e.g. penalty-bearing payments > ₹1 lakh need Owner), and AI involvement (AI drafts
  always need a human reviewer).
- **FR-13** Actions at each step: approve, return with comments (mandatory reason), reassign,
  request info, attach, comment with @mentions. Rejection loops back to the maker with the
  comment thread preserved.
- **FR-14** SoD enforcement + "four-eyes" on sensitive data edits (profile thresholds, overrides).
- **FR-15** SLA per step; breach → escalation; delay reason code required when filing late
  (with interest/late-fee computation where the pack defines it).
- **FR-16** Approvals inbox (web + mobile), bulk approve for low-risk items with a mandatory
  sampling view (show 1 in N items in full before bulk approve).
- **FR-17** Digital sign-off: OTP-confirmed approval in v1; Aadhaar eSign / DSC adapter later.

### 5.4 Guided data intake ("what needs to be fed")
- **FR-18** Each obligation defines an **input schema**: fields, data sources (payroll, HR
  master, attendance, maintenance log, lab report, CBWTF manifest), owner of the data, format,
  validation rules. The obligation workspace shows a checklist: *Data needed → Template →
  Upload/enter → Validation result → Ready for checker*.
- **FR-19** Downloadable Excel templates per input schema; upload → validate (types, ranges,
  cross-checks e.g. PF wages ≤ gross, ESI eligibility ≤ ₹21,000) → error report in plain words.
- **FR-20** Computation helpers defined in packs (PF 12%/12% with EPS split and wage ceiling,
  ESI 0.75%/3.25%, LWF, PT slabs, bonus, gratuity, BOCW cess 1% of cost) — rates are pack data
  with effective dates, never code constants.
- **FR-21** Recurring feeds: connect a monthly payroll export once; mapping is remembered.

### 5.5 Evidence vault & licences
- **FR-22** Evidence items: file + metadata (type, period, issuing authority, reference no.,
  amount, validity), SHA-256, version history, uploader, linked instances; WORM semantics (new
  version, never overwrite); retention per pack rule (e.g. 8 years tax, 5 years BMW records).
- **FR-23** **Licences & registrations register** with validity; renewal obligations created
  automatically N days before expiry (lead time per licence type: CTO 120 days, fire 60, drug
  licence 90, AERB 90…).
- **FR-24** **Licence conditions → obligations**: AI extracts conditions from an uploaded
  CTO/authorisation/licence (§6.3), the Compliance Head reviews each proposed obligation
  (accept/edit/reject), accepted ones join the register with source = that licence, page, clause.
- **FR-25** Evidence verification: AI checks a challan/acknowledgement against the instance
  (period, amount, establishment code, UAN count) and flags mismatches before checker review.

### 5.6 Audit, inspection & CAPA
- **FR-26** Internal audit plans (annual/quarterly), auditor assignment, scope = units × categories.
- **FR-27** Checklists generated from the unit's applicable obligations (+ pack audit points
  per obligation: "verify Form F filled for every USG in sample"), sampling guidance, test steps.
- **FR-28** Observations: condition, criteria (law cite), cause, effect, risk rating (H/M/L),
  evidence, recommendation, management response, target date → **CAPA** with owner,
  verification of effectiveness, closure approval.
- **FR-29** Regulatory inspection log: inspector, authority, date, documents produced, findings;
  **notice management** (show-cause, improvement notice) with statutory reply deadlines,
  AI-drafted reply (§6.2) through Document workflow.
- **FR-30** **Inspection-ready pack**: one click per unit/authority → zipped, indexed PDF bundle of
  registers, licences, latest returns, challans, training records for the last N months.

### 5.7 Contractor compliance
- **FR-31** Contractor master (licence under OSH Code, PF/ESI codes, scope, workforce at site).
- **FR-32** Contractor portal: monthly upload of wage sheet, PF/ESI challans + ECR, attendance;
  automatic reconciliation (headcount at gate vs. ECR members); exceptions block contractor bill
  approval (status flag exported to accounts).

### 5.8 Regulatory change management
- **FR-33** Change items (new law, amendment, notification, due-date extension, rate change)
  authored by Stridenity content team; AI-assisted summarisation from source text (§6.4).
- **FR-34** Impact analysis per tenant: which units/obligations are affected, before/after.
- **FR-35** Tenant Compliance Head reviews and **adopts** (workflow); adoption updates the
  register; a change log is kept per tenant.

### 5.9 Dashboards & reports
- **FR-36** Home: compliance health score (on-time %, evidence completeness, open
  high-risk items, overdue), next 30 days, my approvals, risk heatmap (unit × category),
  penalty exposure estimate (from pack penalty data; labelled as an estimate).
- **FR-37** Reports: monthly MIS, **board compliance certificate** (quarterly, signed by
  Compliance Head + Director, with exceptions list), audit report, overdue & exceptions,
  contractor status, licence expiry, AI usage & acceptance. Excel + PDF.
- **FR-38** External auditor portal: scoped, time-boxed, read-only + observation raising.

### 5.10 Administration
- Users, roles, units, delegation; workflow & approval-matrix designer (form-based in v1, not a
  drag-drop canvas); reminder schedule; channels; content pack enablement per tenant; LLM
  provider & budget; data retention; audit-log viewer; export of all tenant data (DPDP).

### 5.11 SaaS operations (Stridenity operator console)
- **FR-39** Tenant lifecycle: provision (isolation tier, region, plan, packs, first admin invite),
  trial → active → suspended → offboarded (data export, then crypto-shred of tenant key).
- **FR-40** Plans & entitlements (units, users, AI tokens/month, storage, modules), usage
  metering per tenant, billing export (CSV) — payment gateway integration later.
- **FR-41** Content-pack rollout: publish to canary tenants, then all; rollback; per-tenant pinning.
- **FR-42** Feature flags per tenant/plan; announcement banners.
- **FR-43** Support break-glass: time-boxed, approved, reason-coded access, logged into the
  tenant's own audit log and visible to the tenant admin.
- **FR-44** Health: per-tenant error rate, latency, job lag, storage, AI spend; backups and
  restore (PITR for dedicated tier, logical export/import for pooled).

## 6. AI capabilities (all as explained AIActions — see skill `explainability`)

| # | Capability | Input | Output | Human gate |
|---|---|---|---|---|
| 6.1 | **Compliance copilot** (Q&A) | Question + tenant context | Answer with citations to pack obligations / law text; "not legal advice" footer | None (advisory) |
| 6.2 | **Content generation** | Obligation + fed data + template | Draft register/return worksheet, policy (POSH, safety, BMW, DPDP privacy notice), SOP, training content, display notice (EN/HI/MR), notice reply, board certificate narrative | Document workflow |
| 6.3 | **Document extraction** | Licence / CTO / challan / acknowledgement / inspection report | Fields + conditions + proposed obligations with page/clause anchors | Compliance Head review per item |
| 6.4 | **Regulatory change summariser** | Notification text/PDF | Plain summary, affected obligations, proposed pack diff | Stridenity SME review |
| 6.5 | **Evidence verifier** | Evidence + instance expectations | Match/mismatch findings with confidence | Checker sees findings |
| 6.6 | **Audit assistant** | Unit register + history | Risk-based audit plan, checklist, observation drafting in criteria/condition/cause/effect form | Auditor edits |
| 6.7 | **Applicability explainer** | Rule trace | Plain-language "why it applies / what would change it" | None |
| 6.8 | **Intake helper** | Uploaded spreadsheet | Column mapping proposal + validation explanation | Maker confirms mapping |

Rules: deterministic first (rules engine, computations, templates); LLM for language,
extraction and summarisation; mock provider makes everything demoable offline; PII redacted
before any LLM call; tenant-level switch to disable external LLMs (on-prem/Ollama option).
Default model routing: Claude for extraction/drafting, small/cheap model for classification.

## 7. Demo data (synthetic, clearly labelled "Demo")

Three demo tenants, each exercising a sector pack, all fictional:
1. **Sahyadri Precision Components Pvt Ltd** — auto-component manufacturer, MIDC Ambernath (MH);
   146 employees + 38 contract workers via 2 contractors; boiler, 2 air receivers, DG set,
   hazardous waste (spent oil, ETP sludge), CTO with 42 conditions, weighing scales.
2. **Kalyan Care Multispeciality Hospital** — 60-bed hospital, Kalyan (MH); X-ray + CT, 2 USG
   machines, in-house pharmacy, NDPS stock, BMW via CBWTF, lift, fire NOC, NABH entry-level aspirant.
2b. **Shubham Family Clinic & Diagnostics** — single-doctor clinic with day-care, Dombivli (MH);
   9 staff, 1 USG machine, small pharmacy, BMW via CBWTF, no beds (pilot profile for clinics).
3. **Konkan Infra & Electricals LLP** — builder + electrical contractor; one MahaRERA project,
   240 construction workers (mostly via contractors), electrical contractor licence, 11 kV
   substation at site.

Planted stories (for demos and tests): (a) headcount crosses 20 at a unit → EPF becomes
applicable, register diff; (b) CTO expiring in 100 days with 3 conditions overdue; (c) a
contractor's ESI challan headcount ≠ gate attendance; (d) PCPNDT Form F incomplete in sample →
audit observation → CAPA; (e) AI-drafted reply to an Inspector-cum-Facilitator improvement
notice going through approval; (f) a regulatory change (sample) shifts a due date and is adopted.

## 8. Non-functional

- **Tenant isolation:** no request or job runs without a TenantContext; RLS in pooled tier; per-tenant
  encryption keys; automated cross-tenant test suite on every build (all tiers).
- **Security:** OWASP ASVS L2; encryption in transit
  (TLS) and at rest (DB + object storage); secrets encrypted; MFA (OTP) for approvers; RBAC +
  unit scoping; rate limits; malware scan hook on uploads; signed download URLs.
- **DPDP Act 2023 / DPDP Rules 2025:** Stridenity is a data processor for tenant employee/patient
  data and a fiduciary for user accounts — privacy notice, consent for marketing, breach
  runbook, retention & deletion, India data residency (Mumbai/Hyderabad region) by default.
- **Audit trail:** append-only, hash-chained, exportable; clock from server (UTC stored, IST shown).
- **Performance:** register of 400 obligations × 10 units renders < 1.5 s; calendar generation
  for a tenant-year < 5 s; p95 API < 300 ms for reads.
- **Availability:** 99.5% (v1); daily backups, 30-day PITR in prod.
- **Accessibility:** WCAG 2.1 AA; usable at 360 px wide; low-bandwidth mode (no heavy charts).
- **i18n:** EN in v1 UI; HI/MR for generated notices and site-user screens; all strings externalised.
- **Portability:** SQLite for dev/demo, PostgreSQL 16 for production; S3-compatible object store
  (MinIO locally); runs as Docker Compose on one VM (OCI/AWS Mumbai) or Windows for demos.

## 9. Out of scope for v1 (backlog)

Direct e-filing to government portals (EPFO, ESIC, GST, MCA, MPCB XGN) — v1 prepares and
records, humans file; payroll engine; full EHS suite (incident investigation beyond the Event
workflow); NABH/JCI accreditation full module (v1 = checklist pack); other countries (GCC is the
next region — pack structure supports it); native mobile apps (PWA in v1); drag-drop workflow
canvas; e-sign/DSC.

## 10. Success metrics (pilot)

Onboarding to first register < 30 min; ≥ 95% on-time filing in pilot month 3; evidence
completeness ≥ 90%; AI draft acceptance (accepted or lightly edited) ≥ 70%; inspection pack
generated < 2 min; zero SoD violations in approved items.

## 11. Decisions taken (2026-10-16) and open questions

| Topic | Decision |
|---|---|
| Product name | **ANUPAL** for now; kept in one config place so it can change later |
| State rollout | Maharashtra → Gujarat → Andhra Pradesh → Tamil Nadu → Odisha (ADR-020) |
| First pilots | **Both**: small healthcare (clinics, nursing homes, small hospitals) and a small manufacturer |
| Hosting | **OCI** India region (Mumbai, DR Hyderabad) to start (ADR-019); design stays provider-agnostic |
| Commercial model | **Deferred.** Likely per company (tenant). Plans/entitlements stay generic so any model fits later |

Still open: commercial model and price points; partner (CA/consultant) channel; SME reviewer for content.
