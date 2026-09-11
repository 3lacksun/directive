#!/usr/bin/env bash
set -euo pipefail

OUT=out-d8-targeted
rm -rf "$OUT" && mkdir -p "$OUT/input"
python3 - <<'PY' > /tmp/directive_source.env
import json, shlex
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
for p in Path('out-d8-targeted/input').rglob('AndroidManifest.xml'):
 r=p.parent
 if (r/'.project').is_file() and (r/'smali').is_dir(): c.append(r)
if len(c)!=1: raise SystemExit(c)
print(c[0])
PY
)"
export PROJECT_ROOT
python3 - <<'PY' > "$OUT/TARGETED_STARTUP_FORENSICS.txt"
from pathlib import Path
import os,re
root=Path(os.environ['PROJECT_ROOT'])

def method(path, signature):
 p=root/path
 s=p.read_text(encoding='utf-8', errors='replace')
 m=re.search(r'(^\.method[^\n]*'+signature+r'\n.*?^\.end method)',s,re.M|re.S)
 print('\n'+'='*90+'\nFILE',path,'METHOD',signature+'\n'+'='*90)
 print(m.group(1) if m else 'NOT FOUND')

def around(path, needle, before=100, after=180):
 p=root/path; lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
 print('\n'+'='*90+'\nFILE',path,'NEEDLE',needle+'\n'+'='*90)
 for i,l in enumerate(lines):
  if needle in l:
   lo=max(0,i-before); hi=min(len(lines),i+after+1)
   print(f'--- around line {i+1} ---')
   for j in range(lo,hi): print(f'{j+1:05d}: {lines[j]}')

method(Path('smali_classes2/e7/a.smali'), r'm\(\)Z')
method(Path('smali_classes4/yf/t.smali'), r'a\(Landroid/content/Context;Lyf/s;Z\)V')
around(Path('smali_classes4/yf/t.smali'),'HomeAlia_',140,260)
around(Path('smali_classes4/yf/t.smali'),'System;->exit',200,100)

# App icon configuration enum/class and every direct caller of yf/t.a(Context,s,Z)
for p in root.rglob('yf/s.smali'):
 print('\n'+'='*90+'\nFULL FILE',str(p.relative_to(root))+'\n'+'='*90)
 print(p.read_text(encoding='utf-8',errors='replace'))

needle='Lyf/t;->a(Landroid/content/Context;Lyf/s;Z)V'
print('\n'+'='*90+'\nCALLERS OF yf/t.a(Context,s,Z)\n'+'='*90)
for p in root.rglob('*.smali'):
 s=p.read_text(encoding='utf-8',errors='replace')
 if needle not in s: continue
 lines=s.splitlines(); current=''
 for i,l in enumerate(lines):
  if l.startswith('.method '): current=l
  if needle in l:
   print('\nFILE',p.relative_to(root),'LINE',i+1,current)
   for j in range(max(0,i-80),min(len(lines),i+81)): print(f'{j+1:05d}: {lines[j]}')

# AppConfigAccessor app icon getter/setter and callers
for p in root.rglob('AppConfigAccessor.smali'):
 for sig in [r'getAppIcon\(\)Lyf/s;', r'setAppIcon\(Lyf/s;\)V']:
  s=p.read_text(encoding='utf-8',errors='replace')
  m=re.search(r'(^\.method[^\n]*'+sig+r'\n.*?^\.end method)',s,re.M|re.S)
  print('\n'+'='*90+'\nFILE',p.relative_to(root),'METHOD',sig+'\n'+'='*90)
  print(m.group(1) if m else 'NOT FOUND')

# DB init fatal path
method(Path('smali_classes2/com/ticktick/task/TickTickApplicationBase.smali'), r'initDb\(\)V')

# Crash callback installation and abort behavior
for rel in [Path('smali_classes4/com/ticktick/task/utils/ActivityThreadCallback.smali'), Path('smali_classes4/com/ticktick/task/utils/CrashLogHandler.smali')]:
 p=root/rel
 if p.exists():
  print('\n'+'='*90+'\nFULL FILE',rel,'\n'+'='*90)
  print(p.read_text(encoding='utf-8',errors='replace'))

# Manifest exact application/activity/aliases after baseline source
manifest=(root/'AndroidManifest.xml').read_text(encoding='utf-8',errors='replace')
print('\n'+'='*90+'\nMANIFEST RELEVANT LINES\n'+'='*90)
for i,l in enumerate(manifest.splitlines(),1):
 if any(n in l for n in ['<application','MeTaskActivity','HomeAlia_','android:name="com.ticktick.task.TickTickApplication"']): print(f'{i:05d}: {l}')
PY

echo "Targeted startup forensics complete: $OUT/TARGETED_STARTUP_FORENSICS.txt"
