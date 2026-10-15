# ANUPAL build runbook: Claude Code in PowerShell + cloud, multi-session, looped

Claude Code builds the product from this kit: 35 tasks (`docs/plan/TASKS.md`) run in short,
checkpointed sessions that survive the 5-hour usage window. Work can move between your Windows
machine (PowerShell) and Claude Code cloud sessions (web/mobile app) because every step is
committed and pushed to `LearningX-BK/Stridenity` → `Compliance/`. Only one builder runs at a
time, enforced by a lock (ADR-014).

```
 local PowerShell loop ──┐                                    ┌── cloud session (claude.ai/code,
 (build-loop.ps1)        │  claim lock → /next-task steps=2 → │   mobile app, or scheduled task)
                         ▼  commit wip → push → TASK_CONTINUE ▼
               GitHub: LearningX-BK/Stridenity  main  /Compliance   (single source of truth)
```

## Quick start from the Claude mobile app (no PC needed)

1. Claude app → Code → new session → repository **LearningX-BK/Stridenity**, branch `main`.
2. First session only, send the plan-review prompt from §1 below, but replace its last line with
   `4. Then run /next-task T00 steps=2. Work directly on main and push every checkpoint.`
3. Every later session, send: `/next-task steps=2`
   (if slash commands are not accepted: `cd Compliance, read Compliance/CLAUDE.md and follow
   Compliance/.claude/commands/next-task.md with steps=2, working directly on main`).
4. Reply ends with `TASK_CONTINUE Txx` → start a new session with the same prompt.
   `TASK_COMPLETE Txx` → same prompt again picks the next task. `TASK_BUSY local` → the PC loop is
   running; stop it first.
5. Back on the PC later: `git pull` in `C:\GenAIGenerated\Stridenity\Compliance` (after running
   `scripts\setup-git-sync.ps1` once).

---

## 0 · One-time setup (Windows)

```powershell
winget install Git.Git ; winget install astral-sh.uv ; winget install OpenJS.NodeJS.LTS
npm install -g @anthropic-ai/claude-code      # or the native installer; then: claude  (log in once)
# bind the local folder to GitHub (sparse checkout rooted at C:\GenAIGenerated\Stridenity)
powershell -ExecutionPolicy Bypass -File C:\GenAIGenerated\Stridenity\Compliance\scripts\setup-git-sync.ps1
cd C:\GenAIGenerated\Stridenity\Compliance
python scripts/tasks.py status                 # 0/35 done
```
For unattended overnight runs, keep the PC awake: `powercfg /change standby-timeout-ac 0`.
Hooks run through Git Bash (`bash`), which Git for Windows installs.

## 1 · Session 1 — interactive plan review + T00 (Opus)

```powershell
cd C:\GenAIGenerated\Stridenity\Compliance
claude --model opus
```
Paste:
```
You are the lead engineer building ANUPAL, Stridenity's multi-tenant AI compliance SaaS.
The folder already has the full spec and build system — do not re-plan from scratch.
1. Read CLAUDE.md, docs/PRD.md, docs/ARCHITECTURE.md, docs/DECISIONS.md, docs/WORKFLOWS.md,
   docs/plan/TASKS.md and the skills in .claude/skills/. Skim prototype/index.html for UX intent.
2. Review the plan as a principal engineer and as a statutory auditor: gaps, risky assumptions,
   wrong task order, acceptance criteria that can't be verified, Windows pitfalls, tenant-isolation
   holes. At most 8 findings, each with a fix. Ask me at most 4 questions only I can decide.
3. After I answer, apply agreed changes (ADRs in docs/DECISIONS.md; new scope as new tasks in
   TASKS.md then `python scripts/tasks.py sync`), commit "docs: plan review", push.
4. Then run /next-task T00 steps=all.
```

## 2 · Unattended loop (recommended), PowerShell

```powershell
.\scripts\build-loop.ps1                    # per-task model (opus for T02,T06,T07,T10,T11,T30,T32b)
.\scripts\build-loop.ps1 -Model sonnet      # everything on Sonnet (saves usage)
.\scripts\build-loop.ps1 -Once              # just the next task
.\scripts\build-loop.ps1 -StopAt T05        # stop after T05 completes
.\scripts\build-loop.ps1 -Steps 3           # bigger sessions (default 2 sub-steps)
.\scripts\build-loop.ps1 -PauseAfter task   # ask "continue?" after each task (or: session)
New-Item PAUSE                              # from a 2nd window: stop cleanly after this session
.\scripts\build-loop.ps1 -ForceLock         # take over the lock from a cloud session you stopped
.\scripts\build-loop.ps1 -SkipPermissions   # fully unattended (bypasses permission prompts; your call)
```
How it loops: each iteration = `git pull` → claim lock → a fresh headless `claude -p
"/next-task steps=2"` → the session does 2 sub-steps, commits/pushes, prints `TASK_CONTINUE` →
next iteration. When the 5-hour limit hits, it reads "resets 6:30pm", sleeps (wall-clock, survives
laptop sleep) and resumes from the last checkpoint. At exit it releases the lock.
Logs: `.build-logs\`. Linux/macOS: `scripts/build-loop.sh` (same behaviour).

## 3 · Interactive local sessions (watch/steer)

```powershell
claude --model sonnet        # opus for opus-tagged tasks
```
`/status` · `/next-task` · `/next-task T07 steps=all` · near the limit: `/handoff`.

## 4 · Cloud sessions (claude.ai/code or the Claude mobile app) on `LearningX-BK/Stridenity`

Stop the local loop first (or let it finish: it releases the lock). Start a session on the repo and
send ONE prompt per session:
```
/next-task steps=2
```
(If slash commands are not accepted: `cd Compliance, read Compliance/CLAUDE.md, then follow
Compliance/.claude/commands/next-task.md with steps=2. Work directly on main and push each
checkpoint to main.`)
When the reply ends with `TASK_CONTINUE <id>`, start a new session with the same prompt. A reply
`TASK_BUSY local` means your PC loop is still running.
Back on the PC: `git pull` (the loop does it automatically).

## 5 · Cloud loop without your PC — scheduled task (optional)

A scheduled cloud task can fire every hour; each firing is a fresh cloud session that runs one
`/next-task steps=2` chunk and exits, so the build keeps moving while your PC is off. Prompt for the task:
```
Repository LearningX-BK/Stridenity. cd Compliance and follow Compliance/CLAUDE.md. Run the
procedure in Compliance/.claude/commands/next-task.md with steps=2, working directly on main and
pushing every checkpoint. If the builder lock is held by "local", print TASK_BUSY and stop.
If all tasks are done or the next task is blocked, report that and stop.
```
Pause it while you run the PowerShell loop (the lock prevents clashes anyway). Ask Claude to set
it up ("create the hourly ANUPAL build task") when you want it.

## 6 · Sync rules (local ⇄ cloud)

1. One builder at a time. The lock lives in `docs/plan/tasks.json` → `builder`; it goes stale after 3 h.
2. Everything is on `main`; no long-lived branches. Never force-push.
3. Before local work after cloud work: `git pull` (the loop does it). Before cloud work after local
   work: make sure the loop has stopped and pushed (`git status` clean, `git log origin/main` up to date).
4. Local-only files stay local: `.env`, `data/`, `.build-logs/`, `PAUSE` (git-ignored).

## 7 · Targeted prompts for later

- Redo a task: `python scripts/tasks.py reset T13` then `/next-task T13`.
- Add scope without touching finished work: `Add a new task T33 to docs/plan/TASKS.md for <X>
  (same heading format), run python scripts/tasks.py sync, commit and push.`
- Content review: `Use the compliance-auditor agent on content/packs/IN-MH and fix high findings.`
- UI review: `Use the qa-verifier agent on /register and /inbox and fix what it finds.`
- Demo rehearsal: `Walk docs/DEMO_SCRIPT.md with scripts/ui_check.py --e2e demo.spec.ts and fix failures.`
- New state pack: `Create content/packs/IN-OD/odisha following the compliance-packs skill, verified, with REVIEW.md.`

## 8 · Troubleshooting

| Symptom | Fix |
|---|---|
| Loop says "No working Python" | `winget install astral-sh.uv`; the loop prefers `uv run python` |
| `TASK_BUSY cloud` but no cloud session is running | `.\scripts\build-loop.ps1 -ForceLock` |
| A session burned the window on one task | Lower `-Steps 1`, or `-Model sonnet`; check the task's hand-off note isn't asking it to re-read everything |
| Headless session can't start servers | Use `scripts/ui_check.py` only (by design) |
| Push rejected (non-fast-forward) | `git pull` then re-run; never force |
| PC slept during limit wait | The loop uses wall-clock ticks; it resumes on wake |
