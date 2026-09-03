#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "build-src")
path = root / "app/src/main/AndroidManifest.xml"
text = path.read_text(encoding="utf-8")
old = '<receiver android:name=".notifications.ReminderRestoreReceiver" android:exported="false">'
new = '<receiver android:name=".notifications.ReminderRestoreReceiver" android:exported="true">'
if new in text:
    print("BOOT_RECEIVER_EXPORT_FIX=PASS changed=0")
elif text.count(old) == 1:
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("BOOT_RECEIVER_EXPORT_FIX=PASS changed=1")
else:
    raise SystemExit("Expected ReminderRestoreReceiver exported=false declaration not found exactly once")
