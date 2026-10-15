# ANUPAL — AI compliance OS for Indian MSMEs

*A Stridenity Solutions product.* ANUPAL (from *anupālan*, "compliance") is a managed
multi-tenant SaaS. For each unit of a business it works out which compliance obligations apply,
tells people what data to feed, drafts the paperwork with AI, routes everything through
maker → checker → approver, and keeps an evidence trail that is ready for inspection. It covers
manufacturing, healthcare, construction and electrical, for India (Central + Maharashtra) first.

> Status: **specification + build kit + concept prototype.** Claude Code builds the product
> task by task. See `RUNBOOK.md` and `python scripts/tasks.py status`.

| Start here | |
|---|---|
| `prototype/index.html` | Clickable concept prototype (open in a browser, no server needed) |
| `docs/PRD.md` | Product requirements, written from an auditor's point of view |
| `docs/COMPLIANCE_UNIVERSE.md` | Regulatory map: 82 obligations, applicability thresholds, evidence standards |
| `docs/WORKFLOWS.md` | Instance lifecycle, approval templates, approval matrix, SoD, guided intake, AI drafting |
| `docs/ARCHITECTURE.md` · `docs/DECISIONS.md` | Modular monolith ready for microservices, tenancy tiers, control plane, ADRs |
| `docs/UX.md` | Stridenity design system and key screens |
| `docs/plan/TASKS.md` | 35-task build plan with acceptance criteria |
| `RUNBOOK.md` | How to run the build: PowerShell loop, cloud sessions, sync, pause/resume |
| `CLAUDE.md` · `.claude/` | Claude Code protocol, commands, hooks, skills, agents |
| `content/seed/` | v0 obligation library (pending SME review) and its generator |
