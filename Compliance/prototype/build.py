#!/usr/bin/env python3
"""Builds prototype/index.html (standalone, open in any browser) from src/app.html + content/seed.
    python prototype/build.py [--fragment OUT]   # --fragment also writes a body-only copy for publishing
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
src = (HERE / "src/app.html").read_text(encoding="utf-8")
seed = json.loads((ROOT / "content/seed/obligations.seed.json").read_text(encoding="utf-8"))
prof = json.loads((ROOT / "content/seed/demo_profiles.json").read_text(encoding="utf-8"))
body = src.replace("/*__SEED__*/null", json.dumps(seed, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")) \
          .replace("/*__PROFILES__*/null", json.dumps(prof, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        + body.replace("</style>\n", "</style>\n</head>\n<body>\n", 1) + "\n</body>\n</html>\n")
(HERE / "index.html").write_text(full, encoding="utf-8")
if "--fragment" in sys.argv:
    Path(sys.argv[sys.argv.index("--fragment") + 1]).write_text(body, encoding="utf-8")
print("built", len(full) // 1024, "KB")
