#!/usr/bin/env bash
set -euo pipefail

BASE=support/directive11_startup_surface_runtime_capture_build.sh
GEN=/tmp/directive11_build_v2.sh
test -s "$BASE"

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text(encoding='utf-8')
old='PROJECT_ROOT="$(sed -n \'s/^PROJECT_ROOT=//p\' out-v11/evidence/PROJECT_ROOT.txt)"'
new='PROJECT_ROOT="$(sed -n \'s/^PROJECT_ROOT=//p\' out-v11/evidence/PROJECT_ROOT.txt | sed \'s#^out-v8/#out-v11/#\')"'
if src.count(old) != 1:
    raise SystemExit(f'expected exactly one stale D11 PROJECT_ROOT gate, found {src.count(old)}')
src=src.replace(old,new,1)
Path(sys.argv[2]).write_text(src,encoding='utf-8')
PY
chmod +x "$GEN"
bash "$GEN"
