# Workflows, approvals & guided intake

How work moves. The engine is generic (skill `workflow-engine`); templates and the approval
matrix are **tenant data**, seeded from defaults below.

## 1. Obligation instance lifecycle (the spine)

```
            ┌──────────── return (reason required) ────────────┐
            ▼                                                   │
 SCHEDULED → OPEN → IN_PREPARATION → IN_REVIEW → PENDING_APPROVAL → APPROVED → FILED → CLOSED
   (T-15)   (owner   (maker feeds     (checker)     (approver[s])     (ready to   (ack    (evidence
            notified) data, drafts,                                    execute)    uploaded) complete,
                      uploads)                                                              auto-check)
                │                                                                  
                ├──► NA_REQUESTED ──(Compliance Head approves)──► NOT_APPLICABLE (for this period)
                └──► OVERDUE (computed flag, not a state: due_at < now and state < FILED)
```
- `FILED → CLOSED` is automatic when every required evidence slot is filled and evidence checks
  pass; otherwise the instance stays FILED with "evidence incomplete" (counts against score).
- Late filing: moving to FILED after `due_at` requires a **delay reason code** (portal down,
  data from contractor late, cash constraint, missed, other+text) and records late fee/interest
  if the pack defines a formula.
- Renewal instances have an extra state `APPLIED_AWAITING_GRANT` between FILED and CLOSED; the
  licence register shows "applied — deemed valid?" only if the pack says the law allows it.

## 2. Workflow templates (defaults)

| Template | Steps | Used for |
|---|---|---|
| `standard` | Maker → Checker → Approver | Most recurring returns/payments |
| `fast` | Maker → Approver | Low-risk, continuous self-checks, display notices |
| `high_risk` | Maker → Checker → Approver → Owner/Director | Risk H: licences, GST 3B, PNDT, CTO, boilers |
| `event` | Reporter → Investigator → Approver (SLA in hours) | Accidents, breaches, notices received |
| `override` | Requester → Compliance Head (→ Owner if risk H) | Applicability overrides, NA for a period, due-date change |
| `document` | Drafter (human or AI) → Reviewer → Approver → Publish | Policies, SOPs, notice replies, AI drafts, board certificate |
| `capa` | Owner plans → Implements → Auditor verifies effectiveness → Compliance Head closes | Audit observations |
| `contractor_month` | Contractor uploads → Maker reconciles → Checker → (bill release flag) | Contract labour |

Each step: `role` (+ optional unit scope), `sla_hours`, `min_approvers` (e.g. 2-of-3 for
Owner step in a partnership), `can_delegate`, `requires_otp` (approver steps default true),
`allowed_actions` (approve, return, reassign, request_info, comment).

## 3. Approval matrix (rules → template)

Evaluated top-down, first match wins; tenant-editable with a preview "which obligations route
where".

```yaml
- when: { ai_generated: true }              then: document          # AI never skips a human
- when: { risk: H }                         then: high_risk
- when: { kind: payment, amount_gt: 100000 } then: high_risk
- when: { category: [healthcare], risk: M } then: standard, approver_role: medical_superintendent
- when: { frequency: continuous }           then: fast
- default:                                  then: standard
```

**Segregation of duties** (enforced in the engine, not the UI): one user may hold only one step
in an instance's chain; the approver cannot have edited the evidence; overrides cannot be
approved by the requester. "Small-team mode" relaxes this for tenants ≤ 5 users and flags every
affected item in reports.

**Delegation**: user → delegate for a date range, scoped to roles/units; actions are recorded as
"by B on behalf of A".

**Escalation ladder** (defaults): reminder T-15/T-7/T-3/T-1/T0 to owner → T+1 to checker &
approver → T+3 Compliance Head → T+7 Owner/Director + appears on board certificate exceptions.

## 4. Guided intake — "what needs to be fed"

Every obligation has an **input schema** (pack data). The obligation workspace renders it as a
checklist the maker works down:

```
1. Data needed            2. Get it                  3. Feed it            4. Validate          5. Hand over
───────────────           ─────────────              ───────────           ───────────          ────────────
Payroll for Sep 2026  →   from: Accounts (Ravi)  →   upload Excel /    →   rules: PF wage ≤  →  "Ready for
UAN list              →   template ⬇ (xlsx)          map columns once      gross; ESI ≤ ₹21k;    checker" with
Excluded allowances   →   due from contributor:      (remembered)          50% wage rule;        computed
                          T-5 (auto-request)                               headcount ±5% vs      working +
                                                                           last month            exceptions
```

Input schema fields: `key`, `label`, `type` (number/date/file/table/choice), `source`
(payroll, HR master, attendance, maintenance log, lab, CBWTF, contractor, manual),
`provider_role` (who supplies it — gets an auto data-request with its own due date),
`template` (xlsx columns), `validations` (expressions), `computations` (pack formulas).

Data requests are mini-tasks: "Accounts: please upload Sep payroll by 10 Oct" — the provider
sees only that request, uploads, and the maker is notified.

## 5. AI content generation inside the workflow

```
Maker clicks "Draft with AI" on an obligation (or Compliance Head on a policy)
  → engine assembles: obligation (law, form structure), tenant/unit facts, fed data,
    prior approved versions, template (pack)          [deterministic]
  → LLM drafts sections / fills narrative              [AIAction: prompt@ver, model, citations]
  → Draft document v1 (status DRAFT, badge "AI draft") with "Missing inputs" list
  → maker edits (diff tracked) → submits → document workflow (Reviewer → Approver)
  → on approval: PDF/DOCX rendered, hashed, stored as evidence; AIAction gets verdict
    (accepted / edited / rejected) for quality metrics
```
Generated content types (v1): PF/ESI/bonus/cess workings, registers from payroll, bilingual
display notices (EN/HI/MR), POSH policy + notice + annual report, safety policy, BMW Form IV
worksheet & training module, Form V worksheet, CTO condition compliance report, drill report,
toolbox talks, incident/breach intimations, inspection-notice replies, privacy notice &
retention schedule (DPDP), board compliance certificate narrative, audit observations.

**Never generated as final**: anything that is filed or paid — AI produces the *working* and the
*draft*; the human files on the portal and uploads the acknowledgement.

## 6. Audit & CAPA flow

```
Audit plan (annual) → engagement (unit × categories × period) → checklist generated from the
unit's applicable obligations + pack audit points → fieldwork (sample instances, test evidence,
site photos) → observation (condition / criteria / cause / effect / risk / recommendation)
→ management response → CAPA (capa workflow) → verification of effectiveness → closure
→ audit report (PDF) with ratings; repeat observations flagged.
```

## 7. Regulatory change adoption

```
Stridenity content team: change item (source PDF) → AI summary + proposed pack diff → SME
review → publish pack vX.Y
Tenant: impact preview (units, obligations, due dates affected) → Compliance Head adopts
(override workflow) → register updated, change log entry, owners notified
```
