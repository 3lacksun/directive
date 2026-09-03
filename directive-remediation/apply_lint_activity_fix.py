#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "build-src")
path = root / "app/src/main/kotlin/com/example/directive/ui/DirectiveApp.kt"
text = path.read_text(encoding="utf-8")

if "val activity = LocalActivity.current" in text:
    print("LOCAL_ACTIVITY_LINT_FIX=PASS changed=0")
    raise SystemExit(0)

old_line = "val activity = LocalContext.current as? Activity"
if text.count(old_line) != 1:
    raise SystemExit(f"Expected exactly one LocalContext-to-Activity cast, found {text.count(old_line)}")

text = text.replace("import androidx.compose.ui.platform.LocalContext\n", "")
text = text.replace("import android.app.Activity\n", "")
anchor = "import androidx.compose.foundation.layout.*\n"
if "import androidx.activity.compose.LocalActivity\n" not in text:
    if text.count(anchor) != 1:
        raise SystemExit("Expected layout wildcard import anchor exactly once")
    text = text.replace(anchor, anchor + "import androidx.activity.compose.LocalActivity\n", 1)
text = text.replace(old_line, "val activity = LocalActivity.current", 1)
path.write_text(text, encoding="utf-8")
print("LOCAL_ACTIVITY_LINT_FIX=PASS changed=1")
