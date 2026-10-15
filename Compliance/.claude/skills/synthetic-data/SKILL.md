---
name: synthetic-data
description: How ANUPAL generates believable, reproducible demo tenants (manufacturer, hospital, builder/electrical contractor) with planted compliance stories and ground truth. Use for backend/app/demo, ui_check seed data and docs/DEMO_SCRIPT.md.
---

# Demo data

## Principles
1. **Reproducible**: one `random.Random(seed)` passed everywhere; anchor date `--anchor-date`
   (default 2026-10-15), never `datetime.now()`. Same seed → identical rows and file hashes.
2. **Believable to an auditor**: realistic Indian names (mix of Marathi, Hindi, other regions),
   designations, wage bands above MH minimum wages, plausible PF/ESI codes in the right *format*
   but obviously fake (`MHBAN0000000000`-style with a DEMO marker), UAN-like numbers that fail
   Verhoeff where a real ID would pass. Never real company names, real people or real licence numbers.
3. **Labelled**: every demo tenant name ends with nothing misleading, has `is_demo=true`, and the
   UI shows a "Demo data" ribbon.
4. **Story-bearing** — the planted stories of PRD §7 must each be visible within two clicks:
   (a) headcount crossing 20 → EPF diff; (b) CTO expiring in ~100 days with 3 overdue conditions;
   (c) contractor ESI headcount ≠ gate attendance; (d) PC-PNDT Form F gaps → observation → CAPA;
   (e) AI-drafted reply to an improvement notice awaiting approval; (f) sample regulatory change
   (due-date extension) pending adoption.
5. **History**: 13 months of instances with a realistic mix — ~88% on time, ~7% late with delay
   reasons, ~3% open overdue, ~2% NA with approved justification; evidence ~92% complete.
6. **Documents**: generate sample PDFs (reportlab) for licences, CTO with numbered conditions,
   challans, acknowledgements — each stamped "SPECIMEN — DEMO DATA".

## Layout
`backend/app/demo/` — `catalog.py` (names, designations, contractors), `tenants.py` (3 profiles —
facts mirror `content/seed/` demo profiles), `history.py` (instances/workflow runs/evidence),
`docs.py` (PDF generators), `stories.py` (one function per planted story, each with a test),
`seed.py` CLI: `python -m app.demo.seed --reset [--tenant all|mfg|hospital|infra] [--scale 1.0]`.

## Checks before closing a demo task
Print a 10-row sample of instances and 5 workflow timelines into the hand-off; read them as an
auditor would; fix anything implausible (approval before preparation, evidence dated after close,
weekend filing on a portal holiday, etc.).
