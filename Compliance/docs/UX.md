# UX & design system — "calm control"

The user is an HR executive or EHS officer at a 150-person plant, not a compliance geek. Every
screen answers three questions in this order: **What is due? What do I need to do? Is it
approved and evidenced?** Intelligence (applicability, AI drafts, verification) stays in the
background and surfaces as short, explainable suggestions.

## 1. Brand (from the Stridenity identity — `brand/stridenity-visiting-card.jpg`)
The mark is a gradient of coral → magenta → plum, with a cyan/blue counter-stroke; the wordmark
is a dark slate. Use the gradient **only** for the logo, the product mark and one hero accent
per screen; the working UI is neutral so status colours carry meaning.

`frontend/src/styles/tokens.css` (the only file with hex values):
```css
:root {
  --brand-coral:#EC5A3E; --brand-magenta:#D9285C; --brand-plum:#923C7C;
  --brand-blue:#2E8FD8;  --brand-cyan:#2AA9C2;   --brand-ink:#32353C;
  --brand-gradient: linear-gradient(135deg,#EC5A3E 0%,#D9285C 45%,#923C7C 100%);
  /* light theme surfaces */
  --bg:#F6F5F2; --surface:#FFFFFF; --surface-2:#F0EEEA; --border:#E2DED7;
  --text:#22252B; --text-2:#5A5F68; --text-3:#8A8F98;
  --accent:#C0285A; --accent-ink:#FFFFFF; --focus:#2E8FD8;
  /* status (never brand colours) */
  --ok:#1F8A5B; --ok-bg:#E3F3EA; --warn:#B7791F; --warn-bg:#FBF0DC;
  --risk:#C2362B; --risk-bg:#FBE4E1; --info:#2B6CB0; --info-bg:#E2EDF8;
  --ai:#6B4FBF; --ai-bg:#EEE9FA;   /* AI-generated content is always violet-marked */
  --radius-s:6px; --radius-m:10px; --radius-l:16px;
  --font-sans:"Plus Jakarta Sans",system-ui,sans-serif; --font-mono:"JetBrains Mono",monospace;
}
[data-theme="dark"] { --bg:#121317; --surface:#1A1C21; --surface-2:#22252B; --border:#2F333B;
  --text:#ECEDEF; --text-2:#A9AEB7; --text-3:#7B808A; --accent:#F0627F; --accent-ink:#121317;
  --ok:#4CC38A; --ok-bg:#16301F; --warn:#E3A948; --warn-bg:#33270F; --risk:#F0786C;
  --risk-bg:#3A1C19; --info:#6CA8E8; --info-bg:#172638; --ai:#A894F0; --ai-bg:#241D3B; }
```
Type: Plus Jakarta Sans (UI), JetBrains Mono (IDs, amounts, dates in tables). Numbers are
tabular. Indian formatting: ₹1,23,456; dates `15 Oct 2026`; IST.

## 2. Information architecture
```
Home (my day)  ·  Register  ·  Calendar  ·  Inbox (approvals)  ·  Evidence & licences
Audits & CAPA  ·  Contractors  ·  Reg. updates  ·  Reports  ·  Copilot (⌘K / floating)
Settings: Organisation & units · Profile facts · People & roles · Workflows & approval matrix ·
          Reminders · Packs · AI & privacy · Audit log
Operator console (/ops, Stridenity staff only): Tenants · Plans · Packs rollout · Health · Support sessions
```
Mobile (site users, contractors): Today · Checklists · Capture (photo/evidence) · Requests.

## 3. Key screens (prototype in `prototype/index.html` shows each)
1. **Onboarding wizard** — 6 short steps, right-hand live panel: "Obligations found: 54" updating
   as answers change; each question has *Why we ask*. Ends with the Register review.
2. **Register** — grouped by category; each row: obligation, frequency, next due, owner, risk,
   status chip; expand → "Applies because …" trace, law cite, source, review badge.
3. **Home** — health score ring, KPIs (due 7 days, overdue, awaiting my approval, evidence gaps),
   timeline of next 30 days, risk heatmap (unit × category), threshold alerts, reg-update cards.
4. **Obligation workspace** (the most important screen) — left: stepper *Feed → Prepare →
   Review → Approve → File → Evidence*; centre: the current step (input checklist with
   templates & validation, or AI draft editor, or approval panel); right: timeline (who did what),
   evidence slots, law & penalty, "Why does this apply?".
5. **Inbox** — approvals with SLA countdown, risk, AI-involvement badge; approve with OTP;
   return requires a reason; bulk approve low-risk only after sampling.
6. **Evidence & licences** — vault table + licence register with validity bars; upload → AI
   extraction review (fields + proposed obligations from conditions, accept/edit/reject each).
7. **Audits** — plan, checklist, observation form (condition/criteria/cause/effect), CAPA board.
8. **Contractors** — month grid per contractor (wage sheet / PF / ESI / reconciliation ✓✗).
9. **Reg. updates** — change cards with impact on *your* units; Adopt.

## 4. Interaction rules
- One primary action per screen region; secondary actions in a "More" menu.
- AI content is always marked (violet left rule + "AI draft" chip) until a human approves it;
  every AI card has **Why?** (drawer: sources, rationale, model, prompt version) and Accept / Edit / Reject.
- Status chips use text + icon + colour (never colour alone).
- Empty states teach: "No evidence yet — this obligation needs: challan, ECR, bank proof."
- Destructive or irreversible actions (approve with OTP, file, close) show what will be recorded.
- Tables: sticky header, column chooser, density toggle; on mobile collapse to cards.
- Language switch (EN/हिंदी/मराठी) for site-user screens and generated notices.
- WCAG 2.1 AA, keyboard complete, focus ring `--focus`, 44 px touch targets.
