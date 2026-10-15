---
description: Emergency checkpoint — save state now (use when the usage limit is close or before closing the terminal)
---

Stop feature work immediately and secure the session's progress:

1. In `docs/plan/PROGRESS.md`, under the current task, append a hand-off entry with: timestamp,
   model, what is done, what is half-done (file + function names), the exact next step, and any
   failing test or known breakage.
2. If the current sub-step is broken, leave it but say so plainly in that entry.
3. `git add -A && git commit -m "wip(<id>): handoff checkpoint"` and `git push`.
4. Print `HANDOFF_SAVED <id>`.
