#!/usr/bin/env bash
set -euo pipefail
OUT=out-d8-source-slice
rm -rf "$OUT" && mkdir -p "$OUT/input" "$OUT/slice"
python3 - <<'PY' > /tmp/directive_source.env
import json,shlex
j=json.load(open('DIRECTIVE2_SOURCE.json'))
print('SOURCE_URL='+shlex.quote(j['url']))
print('SOURCE_SHA256='+shlex.quote(j['sha256']))
PY
source /tmp/directive_source.env
curl -fL --retry 5 --retry-delay 2 "$SOURCE_URL" -o "$OUT/source.zip"
echo "$SOURCE_SHA256  $OUT/source.zip" | sha256sum -c -
unzip -q "$OUT/source.zip" -d "$OUT/input"
PROJECT_ROOT="$(python3 - <<'PY'
from pathlib import Path
c=[]
for p in Path('out-d8-source-slice/input').rglob('AndroidManifest.xml'):
 r=p.parent
 if (r/'.project').is_file() and (r/'smali').is_dir(): c.append(r)
if len(c)!=1: raise SystemExit(c)
print(c[0])
PY
)"
copy_one() {
  rel="$1"
  test -s "$PROJECT_ROOT/$rel"
  mkdir -p "$OUT/slice/$(dirname "$rel")"
  cp "$PROJECT_ROOT/$rel" "$OUT/slice/$rel"
}
copy_one AndroidManifest.xml
copy_one apktool.json
copy_one smali_classes2/com/ticktick/task/TickTickApplication.smali
copy_one smali_classes2/com/ticktick/task/TickTickApplicationBase.smali
copy_one smali_classes2/e7/a.smali
copy_one smali_classes4/yf/t.smali
copy_one smali_classes4/yf/s.smali
copy_one smali_classes4/com/ticktick/task/utils/ActivityThreadCallback.smali
copy_one smali_classes4/com/ticktick/task/utils/CrashLogHandler.smali
copy_one smali_classes3/com/ticktick/task/helper/IntentParamsBuilder.smali
copy_one smali_classes4/com/ticktick/task/send/c.smali
# Include every class directly named from Application onCreate/base onCreate when present.
for rel in \
  smali_classes2/com/ticktick/task/helper/SettingsPreferencesHelper.smali \
  smali_classes2/com/ticktick/task/helper/UriBuilder.smali \
  smali_classes2/com/ticktick/task/manager/LockManager.smali \
  smali_classes2/com/ticktick/task/utils/DataTracker.smali \
  smali_classes2/com/ticktick/task/helper/HabitSyncHelper.smali \
  smali_classes2/com/ticktick/task/helper/course/CourseSyncHelper.smali \
  smali_classes2/com/ticktick/task/manager/ActivityLifecycleManager.smali; do
  if [ -s "$PROJECT_ROOT/$rel" ]; then copy_one "$rel"; fi
done
find "$OUT/slice" -type f -print | sort > "$OUT/slice/SOURCE_SLICE_FILES.txt"
sha256sum $(find "$OUT/slice" -type f -print | sort) > "$OUT/slice/SOURCE_SLICE_SHA256.txt"
echo "$PROJECT_ROOT" > "$OUT/slice/PROJECT_ROOT.txt"
