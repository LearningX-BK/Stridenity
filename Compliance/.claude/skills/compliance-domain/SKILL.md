---
name: compliance-domain
description: ANUPAL's compliance domain model and auditor rules — obligation vs instance, register, applicability traces, evidence standards, licences and conditions, events, contractors, audit/CAPA vocabulary, Indian context. Use for any backend or UI work touching obligations, register, calendar, evidence, intake, audit or reports.
---

# Compliance domain

## Vocabulary (use these names in code, API and UI)
| Term | Meaning |
|---|---|
| **Pack** | Versioned bundle of content for a jurisdiction or sector (`IN/central`, `IN-MH/maharashtra`, `IN/healthcare`) |
| **Obligation** | Content: a duty under a law (key `IN.SS.EPF.ECR`) — law cite, authority, frequency, due rule, applies rule, risk, inputs, evidence slots, penalty, audit points |
| **Profile facts** | Answers about a unit (employees, equipment, activities) — versioned, with source |
| **Register entry** | Obligation × unit with applicability status + trace + owners |
| **Instance** | One period of work for a register entry (Sep-2026 PF) with due date, state, evidence |
| **Evidence slot** | A required piece of proof for an instance (challan, ack, bank proof) |
| **Licence** | Registration/licence/consent/authorisation with validity; drives renewals; has **conditions** |
| **Event** | Something that creates instances (joiner, exit, accident, breach, machine added, notice received) |
| **Override** | Human change to applicability (with justification + approval) |
| **Observation / CAPA** | Audit finding (condition, criteria, cause, effect, risk, recommendation) / corrective & preventive action |

## Auditor rules the code must enforce
1. Applicability is explained: every entry stores a trace; `needs_input` when a fact is unknown.
2. Overrides need justification + approval (`override` workflow) and show on reports.
3. An instance closes only when all **required** evidence slots are filled (and verification has
   no open high mismatch). FILED without evidence counts as non-compliant in the health score.
4. Late filing requires a delay reason; late fee/interest computed only from pack formulas.
5. Renewals: open at `expiry − lead_days`; stay `APPLIED_AWAITING_GRANT` until the new licence is
   uploaded; licence register shows the gap.
6. Continuous duties are tested by periodic self-check instances with dated photo/register evidence.
7. Principal employer: contractor submissions are reconciled monthly; exceptions block bill release.
8. Everything is attributable (actor, on-behalf-of, time, IP/device) and in the hash-chained log.
9. Content provenance: show law cite, source link, `verified_on` and review badge
   ("Draft — pending SME review") wherever an obligation is shown.
10. Penalty exposure is an *estimate* from pack data; label it so.

## Health score (v1, explainable)
`score = 100 × (0.45·on_time_rate + 0.25·evidence_completeness + 0.20·(1 − open_high_risk_ratio)
+ 0.10·(1 − overdue_ratio))` over the last 12 months of instances in scope; show the four factors.
Weights are tenant-configurable later; keep the formula in one function with a unit test.

## Indian context
FY = Apr–Mar; calendar-year duties exist (POSH report, BMW Form IV covers calendar year).
Currency ₹ in paise; Indian digit grouping. Time zone Asia/Kolkata. Holidays: national + state
(content data). Laws changed recently — labour codes in force 21-Nov-2025 (Factories Act, CLRA,
BOCW absorbed), Income-tax Act 2025 from 1-Apr-2026, Boilers Act 2025, DPDP Rules 2025
(full compliance 13-May-2027). See `docs/COMPLIANCE_UNIVERSE.md`.

## Roles (PRD §2)
owner, compliance_head, approver, checker, maker (with function: hr, accounts, ehs, cs, admin,
clinical, pharmacy, biomed, pm), site_user, contractor, external_auditor, viewer; ops_* (platform).
