---
name: compliance-packs
description: How to author, verify, validate and version ANUPAL content packs (YAML obligations, facts, rules, due rules, rates, templates, holidays) and the SME review discipline. Use for content/packs, the content context, applicability rules and regulatory changes.
---

# Content packs

## Layout
```
content/packs/<jurisdiction>/<pack>/
  pack.yaml            # key, name, jurisdiction (IN | IN-MH), sectors, version (semver), depends_on
  facts.yaml           # fact definitions this pack adds (key, label, type, options, why_we_ask)
  obligations/<category>.yaml
  rates.yaml           # e.g. pf.employer_rate with effective_from/to and source
  templates/<id>.md.j2 # AI/deterministic draft templates
  holidays/<year>.yaml # only in jurisdiction packs
  REVIEW.md            # open SME questions — one line per uncertain item
```

## Obligation (YAML)
```yaml
- key: IN.SS.EPF.ECR
  title: EPF monthly ECR & contribution payment
  category: social_security
  law: { act: "Code on Social Security, 2020", provision: "EPF Scheme para 38", note: "" }
  authority: EPFO
  frequency: monthly
  due_rule: { type: monthly_day, day: 15, holiday_shift: none }
  applies: { all: [ { fact: employees, op: gte, value: 20 } ] }
  risk: H
  owner_role: maker:hr
  workflow_hint: standard
  inputs:
    - { key: payroll, label: "Monthly payroll", type: table, source: payroll, provider_role: maker:accounts,
        template: [emp_code, name, uan, gross, basic_da, excluded_allowances, days_paid],
        validations: ["basic_da <= gross", "uan matches ^\\d{12}$"] }
  computations: [ pf_contribution ]           # implemented once in intake, parameterised by rates.yaml
  evidence_slots:
    - { key: ecr, label: "ECR file", required: true }
    - { key: challan, label: "TRRN challan", required: true }
    - { key: bank_proof, label: "Bank debit proof", required: true }
  penalty: { text: "Interest and damages on delayed remittance", formula: null }
  audit_points: ["Recompute PF for 2 sampled months applying the 50% wage rule"]
  ai_templates: [pf_working]
  source_url: https://www.epfindia.gov.in
  verified_on: 2026-10-20
  review: ai_verified          # sme_pending | ai_verified | sme_reviewed | published
  verify: false                # true = a specific fact still unconfirmed → must be in REVIEW.md
  effective_from: 2025-11-21
  effective_to: null
```
Rule ops: `eq ne gt gte lt lte in contains not_contains exists`, combinators `all any not`.
Due rule types: see ARCHITECTURE §4.2.

## Verification discipline (non-negotiable)
1. Never state a date, threshold, rate, form number or section from memory alone. Fetch the
   official source (allow-listed government sites in `.claude/settings.json`), or a reputable
   secondary source if the official one is unreachable — and say which in `law.note`.
2. If still unsure: keep the best value, set `verify: true`, add a REVIEW.md line:
   `IN.X.Y — question for SME — what the sources say — link`.
3. Record `source_url` (deep link where possible) and `verified_on` (today).
4. Superseded law: set `effective_to` on the old obligation and create the new one; never edit
   history in place (published versions are immutable).
5. Rates/thresholds that change by notification live in `rates.yaml`/facts, not in rules text.

## Versioning
Semver per pack. Patch = text/source fixes; minor = new obligations or rule changes; major =
structural/schema change. `python -m app.content diff <pack> <from> <to>` must be readable by a
human reviewer; the diff is what tenants see in regulatory-change impact.

## Validator must reject
Unknown fact keys or ops; due_rule type unknown or missing params; missing source_url (except
`review: sme_pending` seed imports); duplicate keys across packs; overlapping effective ranges for
one key; `verify: true` without a REVIEW.md entry; template referencing unknown inputs.
