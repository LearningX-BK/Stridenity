#!/usr/bin/env python3
"""Task tracker for the ANUPAL build. Single source of truth: docs/plan/tasks.json.

Usage:
  python scripts/tasks.py next            # next runnable task (in_progress first, then first pending with deps done)
  python scripts/tasks.py next --json     # same, machine-readable (used by build-loop.ps1 / .sh)
  python scripts/tasks.py status          # table of all tasks + builder lock
  python scripts/tasks.py start T05 | done T05 | block T05 "reason" | reset T05
  python scripts/tasks.py sync            # add tasks newly written in TASKS.md (keeps existing statuses)
  python scripts/tasks.py claim local|cloud [--force]   # take the builder lock (one builder at a time, ADR-014)
  python scripts/tasks.py release local|cloud
  python scripts/tasks.py lock --json     # show the lock

The lock is advisory but checked by /next-task and the build loops: a claim by the OTHER side
younger than LOCK_HOURS makes `claim` exit 3 (print BUSY). Re-claiming by the same side refreshes it.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "docs" / "plan" / "tasks.json"
TASKS_MD = ROOT / "docs" / "plan" / "TASKS.md"
VALID = {"pending", "in_progress", "done", "blocked"}
LOCK_HOURS = 3
HEAD = re.compile(r"^### (T\d+[a-z]?) · (.+?) — (opus|sonnet|haiku) · deps: (.+)$")


def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp() -> str:
    return now().strftime("%Y-%m-%dT%H:%MZ")


def load() -> dict:
    return json.loads(FILE.read_text(encoding="utf-8"))


def save(data: dict) -> None:
    FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def find(data: dict, tid: str) -> dict:
    for t in data["tasks"]:
        if t["id"].lower() == tid.lower():
            return t
    sys.exit(f"unknown task {tid}")


def next_task(data: dict) -> dict | None:
    done = {t["id"] for t in data["tasks"] if t["status"] == "done"}
    for t in data["tasks"]:
        if t["status"] == "in_progress":
            return t
    for t in data["tasks"]:
        if t["status"] == "pending" and all(d in done for d in t["deps"]):
            return t
    return None


def parse_md() -> list[dict]:
    out = []
    for line in TASKS_MD.read_text(encoding="utf-8").splitlines():
        m = HEAD.match(line.strip())
        if m:
            deps = [] if m.group(4).strip() in {"—", "-", ""} else [d.strip() for d in m.group(4).split(",")]
            out.append({"id": m.group(1), "title": m.group(2).strip(), "model": m.group(3),
                        "deps": deps, "status": "pending", "note": ""})
    return out


def lock_state(data: dict) -> dict:
    b = data.get("builder") or {}
    fresh = False
    if b.get("by") and b.get("at"):
        at = datetime.strptime(b["at"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
        fresh = now() - at < timedelta(hours=LOCK_HOURS)
    return {**b, "fresh": fresh}


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd, *rest = argv
    if cmd == "sync":
        md = parse_md()
        data = load() if FILE.exists() else {"version": 1, "builder": {}, "tasks": []}
        have = {t["id"]: t for t in data["tasks"]}
        merged = []
        for t in md:
            if t["id"] in have:
                old = have[t["id"]]
                t["status"], t["note"] = old["status"], old.get("note", "")
            merged.append(t)
        extra = [t for t in data["tasks"] if t["id"] not in {m["id"] for m in md}]
        data["tasks"] = merged + extra
        save(data)
        print(f"synced: {len(md)} tasks from TASKS.md ({len(md) - len(have.keys() & {m['id'] for m in md})} new)")
        return 0
    data = load()
    if cmd == "next":
        t = next_task(data)
        blocked = [x["id"] for x in data["tasks"] if x["status"] == "blocked"]
        remaining = [x["id"] for x in data["tasks"] if x["status"] != "done"]
        if "--json" in rest:
            print(json.dumps({"task": t, "blocked": blocked, "remaining": len(remaining), "lock": lock_state(data)}))
        elif t:
            print(f"{t['id']} [{t['status']}] {t['title']}  (model: {t['model']}, deps: {', '.join(t['deps']) or '-'})")
        elif remaining:
            print(f"No runnable task. Blocked: {blocked or 'none'}; remaining: {remaining}")
        else:
            print("ALL TASKS DONE")
        return 0
    if cmd == "status":
        for t in data["tasks"]:
            mark = {"done": "[x]", "in_progress": "[~]", "blocked": "[!]", "pending": "[ ]"}[t["status"]]
            note = f"  -- {t['note']}" if t.get("note") else ""
            print(f"{mark} {t['id']} {t['title']} ({t['model']}){note}")
        n = sum(t["status"] == "done" for t in data["tasks"])
        lk = lock_state(data)
        print(f"\n{n}/{len(data['tasks'])} done · builder lock: "
              f"{(lk.get('by') or 'none') + (' (fresh, since ' + lk['at'] + ')' if lk['fresh'] else ' (stale/free)')}")
        return 0
    if cmd == "lock":
        print(json.dumps(lock_state(data)))
        return 0
    if cmd in {"claim", "release"}:
        if not rest or rest[0] not in {"local", "cloud"}:
            sys.exit(f"{cmd} needs local|cloud")
        who = rest[0]
        lk = lock_state(data)
        if cmd == "claim":
            if lk["fresh"] and lk.get("by") != who and "--force" not in rest:
                print(f"BUSY: builder lock held by {lk['by']} since {lk['at']} (expires after {LOCK_HOURS}h). "
                      f"Finish/stop the other builder, or `claim {who} --force`.")
                return 3
            data["builder"] = {"by": who, "at": stamp()}
        else:
            if lk.get("by") == who:
                data["builder"] = {}
        save(data)
        print(f"lock -> {data['builder'] or 'free'}")
        return 0
    if cmd in {"start", "done", "block", "reset"}:
        if not rest:
            sys.exit(f"{cmd} needs a task id")
        t = find(data, rest[0])
        new = {"start": "in_progress", "done": "done", "block": "blocked", "reset": "pending"}[cmd]
        if cmd == "start":
            done = {x["id"] for x in data["tasks"] if x["status"] == "done"}
            missing = [d for d in t["deps"] if d not in done]
            if missing:
                sys.exit(f"cannot start {t['id']}: deps not done: {missing}")
        t["status"] = new
        if cmd == "block":
            t["note"] = f"{stamp()} blocked: {' '.join(rest[1:]) or 'no reason given'}"
        elif cmd == "done":
            t["note"] = f"done {stamp()}"
        elif cmd == "start":
            t["note"] = f"started {stamp()}"
        else:
            t["note"] = ""
        assert t["status"] in VALID
        save(data)
        print(f"{t['id']} -> {t['status']}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
