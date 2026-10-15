---
description: Pick up the next ANUPAL build task (or resume the in-progress one) and drive it to done with checkpoints
argument-hint: "[task id, e.g. T07] [steps=N  (default 2; steps=all to finish in one go)]"
---

You are continuing the ANUPAL build (Stridenity Compliance). Follow `Compliance/CLAUDE.md` >
Build protocol exactly. Work from the `Compliance/` folder (`cd Compliance` if you are at the
monorepo root).

0. **Builder lock (ADR-014)** — side = `cloud` if env `CLAUDE_CODE_REMOTE` is `true`, else `local`.
   `git pull --rebase`, then `python scripts/tasks.py claim <side>`. If it exits 3 (BUSY): change
   nothing, print exactly `TASK_BUSY <holder>` and stop. Otherwise commit
   `chore: builder lock (<side>)` and push (skip if nothing changed). In cloud sessions work
   directly on `main` unless the user's prompt says to use a branch/PR.

1. **Sync & orient**
   - If `git pull` fails because of local changes: commit them as
     `wip: recovered uncommitted work` first, then pull.
   - Arguments: `$ARGUMENTS`. A `Txx` token picks that task (verify its deps are done); otherwise
     `python scripts/tasks.py next`. `steps=N` sets this session's **step budget** (default 2);
     `steps=all` removes it.
   - Read that task's section in `docs/plan/TASKS.md`, its hand-off notes in
     `docs/plan/PROGRESS.md`, and the skills it lists (`.claude/skills/<name>/SKILL.md`).
   - Read only the doc sections the task touches. Skim existing code it builds on (Explore
     subagent only if that is more than ~10 files).
   - In a fresh cloud container install deps first if missing (`uv sync --project backend`,
     `npm --prefix frontend ci`), and copy `.env.example` → `.env` if absent.
   - If `git status` is dirty or the task is already `in_progress`: you are resuming. Work out
     what is already done from the hand-off note + code + tests before writing anything.

2. **Plan briefly** — a 5–10 line checklist (sub-steps that each end in a working state) in the
   task's PROGRESS.md section. `python scripts/tasks.py start <id>` (skip if in_progress), commit
   `chore(<id>): start`, push.

3. **Build** sub-step by sub-step. After each: targeted tests/lint, tick the checklist, one-line
   hand-off note, commit `wip(<id>): <sub-step>`, push. Follow the skills' contracts; do not
   invent parallel patterns.
   **Step budget**: after the budgeted number of checklist sub-steps (planning counts as one),
   stop even if unfinished: make sure the hand-off note says exactly what comes next, refresh the
   lock (`python scripts/tasks.py claim <side>`), commit, push, print one line
   `TASK_CONTINUE <id>`. Verify (4) and Close (5) together count as one sub-step.

4. **Verify** — run every Acceptance item for real. Opus-tagged tasks (and tasks whose Acceptance
   names it): `code-reviewer` subagent ONCE on the code diff (`git diff <start>..HEAD -- '*.py'
   '*.ts' '*.tsx'`, excluding data/YAML/fixtures); content tasks: `compliance-auditor` once; UI
   tasks: `qa-verifier`. Fix high/medium; low → BACKLOG.md. Then `/verify`.

5. **Close** — `python scripts/tasks.py done <id>`; final hand-off line (what was built, where,
   what the next task must know); commit `feat(<id>): <title>`; push. If no further session will
   follow in this run (e.g. `steps=all` interactive), `python scripts/tasks.py release <side>`,
   commit, push. Print exactly one line: `TASK_COMPLETE <id>`.

If blocked on something only the user can decide (credentials, a product or legal decision):
do the preparatory work, `python scripts/tasks.py block <id> "<reason>"`, release the lock,
commit, push, print `TASK_BLOCKED <id>: <reason>`. Never start another task in the same session.
