#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "build-src")
path = root / "app/src/main/kotlin/com/example/directive/feature/calendar/CalendarScreen.kt"
text = path.read_text(encoding="utf-8")

replacements = {
    "val gridHeight=(end-start)*minuteHeight": "val gridHeight=minuteHeight*(end-start).toFloat()",
    "val y=((minute-start).coerceAtLeast(0))*minuteHeight": "val y=minuteHeight*((minute-start).coerceAtLeast(0)).toFloat()",
    "val y=(visibleStart-start)*minuteHeight": "val y=minuteHeight*(visibleStart-start).toFloat()",
    "val naturalHeight=(visibleEnd-visibleStart)*minuteHeight": "val naturalHeight=minuteHeight*(visibleEnd-visibleStart).toFloat()",
    "if(cardHeight>=70.dp)": "if(cardHeight.value>=70f)",
}

changed = 0
for old, new in replacements.items():
    if new in text:
        continue
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one occurrence of {old!r}, found {count}")
    text = text.replace(old, new, 1)
    changed += 1

path.write_text(text, encoding="utf-8")
print(f"CALENDAR_COMPILE_FIX=PASS changed={changed}")
