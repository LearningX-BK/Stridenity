#!/usr/bin/env bash
# Hook launcher: run a hook script with the first Python that actually works.
# (On Windows, bare `python` may be the Microsoft Store alias that only prints "Python was not found".)
# Usage: bash run.sh <script.py>   - stdin and the script's exit code pass through unchanged.
script="$(dirname "$0")/$1"
for cand in "python" "python3" "py -3" "uv run --no-project --quiet python"; do
  if $cand -c "print(42)" 2>/dev/null | grep -q 42; then
    exec $cand "$script"
  fi
done
echo "hook: no working Python found (tried python, python3, py, uv)" >&2
exit 0
