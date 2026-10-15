"""Stop hook: don't let a session end with uncommitted work (that is what a token cut-off loses).

If the tree is dirty and we have not already nudged in this stop cycle, exit 2 so Claude gets the
message and makes a wip checkpoint commit + hand-off note first. Never loops (stop_hook_active).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
if (ROOT / "Compliance" / "docs" / "plan" / "tasks.json").exists():  # session started at monorepo root
    ROOT = ROOT / "Compliance"

try:
    payload = json.loads(sys.stdin.read() or "{}")
except json.JSONDecodeError:
    payload = {}

if payload.get("stop_hook_active"):
    sys.exit(0)

try:
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=ROOT, capture_output=True,
                           text=True, timeout=15).stdout.strip()
except Exception:  # noqa: BLE001
    sys.exit(0)

if dirty:
    sys.stderr.write(
        "Uncommitted changes exist. Before stopping: append a hand-off line for the current task "
        "in docs/plan/PROGRESS.md (done / next / gotchas), then `git add -A && git commit -m "
        "\"wip(Txx): <what>\"` and `git push`. If the work is broken, say so in the hand-off line.\n"
    )
    sys.exit(2)
sys.exit(0)
