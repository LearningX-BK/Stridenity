#!/usr/bin/env bash
# ANUPAL build loop for Linux/macOS (same protocol as build-loop.ps1).
#   scripts/build-loop.sh                 # run until done, per-task model
#   MODEL=sonnet STEPS=3 ONCE=1 scripts/build-loop.sh
#   touch PAUSE                           # stop cleanly before the next session
# Waits out usage limits (parses "resets 6:30pm"), resumes from checkpoints.
set -uo pipefail
cd "$(dirname "$0")/.."
MODEL="${MODEL:-auto}"; FALLBACK="${FALLBACK:-sonnet}"; STEPS="${STEPS:-2}"; ONCE="${ONCE:-0}"
WAIT_DEFAULT_MIN="${WAIT_DEFAULT_MIN:-30}"; MAX_NOPROG=2; noprog=0
PY=python3; command -v python3 >/dev/null || PY=python
mkdir -p .build-logs
done_count() { $PY -c "import json;print(sum(t['status']=='done' for t in json.load(open('docs/plan/tasks.json',encoding='utf-8'))['tasks']))"; }
limit_wait() { # seconds to wait if output looks like a usage limit, else -1
  grep -qiE 'session limit|weekly limit|usage limit|hit your|limit reached|rate limit|resets at|overloaded|429' "$1" || { echo -1; return; }
  local t; t=$(grep -oiE 'resets? (at )?[0-9]{1,2}(:[0-9]{2})? ?(am|pm)' "$1" | head -1 | sed -E 's/resets? (at )?//I')
  if [ -n "$t" ]; then local s; s=$(( $(date -d "$t" +%s 2>/dev/null || echo 0) )); local n; n=$(date +%s)
    [ "$s" -gt 0 ] && { [ "$s" -lt "$n" ] && s=$((s+86400)); echo $((s-n+120)); return; }; fi
  echo $((WAIT_DEFAULT_MIN*60))
}
while true; do
  [ -f PAUSE ] && { rm -f PAUSE; echo "PAUSE found - stopping."; break; }
  git pull --rebase --autostash -q
  state=$($PY scripts/tasks.py next --json)
  id=$(echo "$state" | $PY -c "import sys,json;t=json.load(sys.stdin)['task'];print(t['id'] if t else '')")
  [ -z "$id" ] && { $PY scripts/tasks.py next; break; }
  tmodel=$(echo "$state" | $PY -c "import sys,json;print(json.load(sys.stdin)['task']['model'])")
  use=$([ "$MODEL" = auto ] && echo "$tmodel" || echo "$MODEL")
  $PY scripts/tasks.py claim local || { echo "Lock held by another builder - stopping."; break; }
  git add docs/plan/tasks.json && git commit -qm "chore: builder lock (local)" && git push -q
  log=".build-logs/$(date +%Y%m%d-%H%M%S)-$id.log"; before=$(done_count); head0=$(git rev-parse HEAD)
  echo "=== $id [model: $use] ==="
  args=(-p "/next-task steps=$STEPS" --model "$use" --output-format text --permission-mode acceptEdits)
  [ "$FALLBACK" != "$use" ] && args+=(--fallback-model "$FALLBACK")
  claude "${args[@]}" 2>&1 | tee "$log"
  after=$(done_count); head1=$(git rev-parse HEAD)
  if grep -q "TASK_COMPLETE $id" "$log" || [ "$after" -gt "$before" ]; then noprog=0; [ "$ONCE" = 1 ] && break; continue; fi
  grep -qE "TASK_BLOCKED|TASK_BUSY" "$log" && { echo "Blocked/busy - see PROGRESS.md"; break; }
  if grep -q "TASK_CONTINUE $id" "$log" && ! grep -qiE 'session limit|hit your|usage limit' "$log"; then noprog=0; continue; fi
  w=$(limit_wait "$log")
  if [ "$w" -gt 0 ]; then echo "Usage limit - waiting $((w/60)) min"; end=$(( $(date +%s) + w ))
    while [ "$(date +%s)" -lt "$end" ]; do sleep 60; done; continue; fi
  if [ "$head1" != "$head0" ]; then noprog=0; continue; fi
  noprog=$((noprog+1)); echo "No progress ($noprog/$MAX_NOPROG). Log: $log"; [ $noprog -ge $MAX_NOPROG ] && break
done
git pull --rebase --autostash -q; $PY scripts/tasks.py release local >/dev/null
git add docs/plan/tasks.json && git commit -qm "chore: release builder lock (local)" && git push -q
$PY scripts/tasks.py status
