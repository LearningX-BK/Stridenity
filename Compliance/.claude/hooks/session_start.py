"""SessionStart hook: orient every session (local or cloud) on where the build is.

stdout is added to Claude's context. In Claude Code cloud sessions (CLAUDE_CODE_REMOTE=true) it
also installs dependencies once so tests can run.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
if (ROOT / "Compliance" / "docs" / "plan" / "tasks.json").exists():  # session started at monorepo root
    ROOT = ROOT / "Compliance"


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 600) -> str:
    try:
        out = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True,
                             timeout=timeout, encoding="utf-8", errors="replace")
        return (out.stdout + out.stderr).strip()
    except Exception as exc:  # noqa: BLE001 - hook must never crash the session
        return f"(failed: {' '.join(cmd)}: {exc})"


def cloud_setup() -> list[str]:
    msgs: list[str] = []
    if os.environ.get("CLAUDE_CODE_REMOTE", "").lower() != "true":
        return msgs
    if (ROOT / "backend" / "pyproject.toml").exists() and not (ROOT / "backend" / ".venv").exists():
        if not shutil.which("uv"):
            run([sys.executable, "-m", "pip", "install", "-q", "uv"])
        msgs.append("cloud: backend deps -> " + run(["uv", "sync", "--project", "backend"])[-200:])
    if (ROOT / "frontend" / "package.json").exists() and not (ROOT / "frontend" / "node_modules").exists():
        msgs.append("cloud: frontend deps (npm ci: never rewrites the lockfile) -> " + run(["npm", "--prefix", "frontend", "ci", "--no-audit", "--no-fund"])[-200:])
    if not (ROOT / ".env").exists() and (ROOT / ".env.example").exists():
        shutil.copy(ROOT / ".env.example", ROOT / ".env")
        msgs.append("cloud: created .env from .env.example (mock LLM provider)")
    return msgs


def main() -> None:
    lines = ["== ANUPAL build context =="]
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    dirty = run(["git", "status", "--porcelain", "--", "."])
    lines.append(f"branch: {branch}; uncommitted changes: {'YES - previous session may have been cut off, inspect before continuing' if dirty else 'no'}")
    try:
        data = json.loads((ROOT / "docs/plan/tasks.json").read_text(encoding="utf-8"))
        tasks = data["tasks"]
        done = sum(t["status"] == "done" for t in tasks)
        current = next((t for t in tasks if t["status"] == "in_progress"), None)
        blocked = [t["id"] for t in tasks if t["status"] == "blocked"]
        b = data.get("builder") or {}
        lines.append(f"builder lock: {b.get('by', 'none')} {b.get('at', '')} (check with `python scripts/tasks.py lock`)")
        lines.append(f"tasks: {done}/{len(tasks)} done; in progress: {current['id'] + ' ' + current['title'] if current else 'none'}; blocked: {blocked or 'none'}")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"tasks.json unreadable: {exc}")
    progress = ROOT / "docs/plan/PROGRESS.md"
    if progress.exists():
        tail = progress.read_text(encoding="utf-8").splitlines()[-12:]
        lines.append("last hand-off lines:\n  " + "\n  ".join(tail))
    lines.extend(cloud_setup())
    lines.append(f"Product folder: {ROOT}. Run commands from there. Protocol: Compliance/CLAUDE.md > Build protocol. Use /next-task to continue.")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
