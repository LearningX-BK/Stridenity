# Stridenity product monorepo

Stridenity Solutions Private Limited — products live in top-level folders:

| Folder | Product | Instructions |
|---|---|---|
| `Compliance/` | **ANUPAL** — AI compliance OS for Indian MSMEs (multi-tenant SaaS) | `Compliance/CLAUDE.md` |

Rules for every session:
- Work inside ONE product folder. For compliance work: `cd Compliance` first (the shell keeps the
  cwd), then read and follow `Compliance/CLAUDE.md` — it overrides anything generic.
- Slash commands for the compliance build live in `Compliance/.claude/commands/`. If `/next-task`
  is not available (session started at the repo root), read
  `Compliance/.claude/commands/next-task.md` and follow it exactly.
- Do not modify other product folders.
