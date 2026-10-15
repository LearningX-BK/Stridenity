# Build progress & hand-off log

Status of every task: `python scripts/tasks.py status` (source of truth: `tasks.json`).
This file is the narrative: each session appends to the current task's section. Keep entries
short and concrete. The next session may be a different model, machine, or a cloud session, and
it depends on them.

Template for a task section:
```
## Txx — <title>
Checklist:
- [ ] sub-step …
- <YYYY-MM-DD HH:MM> [model, local|cloud] done: …; next: …; gotcha: …
```

---

## Environment notes
- Local: Windows + PowerShell, folder `C:\GenAIGenerated\Stridenity\Compliance`; git root is the
  parent folder (sparse checkout, `scripts/setup-git-sync.ps1`).
- Remote: https://github.com/LearningX-BK/Stridenity (branch `main`), product folder `Compliance/`.
- Cloud sessions start at the repo root: `cd Compliance` first. One builder at a time (lock in tasks.json).
- Ports: dev API 8091 / UI 5191; ui_check API 8191 / UI 5291.

## Kit notes (2026-10-16, planning session)
- Spec, kit and prototype generated; no product code yet. Seed content in `content/seed/` is
  pending SME review (43 items flagged `verify`); T06 imports it, T08/T09 verify it.
- Open product questions are in docs/PRD.md §11. Answer them in session 1 (RUNBOOK §1).

---

<!-- sessions append below this line -->
