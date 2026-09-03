#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "build-src")
path = root / "app/src/androidTest/kotlin/com/example/directive/DirectiveRebootReminderInstrumentedTest.kt"
text = path.read_text(encoding="utf-8")
old = '''                value\n            }\n            assertEquals(ReminderState.SCHEDULED, restored.state)'''
new = '''                value!!\n            }\n            assertEquals(ReminderState.SCHEDULED, restored.state)'''
if new in text:
    print("REBOOT_TEST_NULLABILITY_FIX=PASS changed=0")
elif text.count(old) == 1:
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("REBOOT_TEST_NULLABILITY_FIX=PASS changed=1")
else:
    raise SystemExit("Expected reboot test nullable return block not found exactly once")
