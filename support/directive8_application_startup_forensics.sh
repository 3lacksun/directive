#!/usr/bin/env bash
set -euo pipefail
OUT=out-d8-app-startup
rm -rf "$OUT" && mkdir -p "$OUT/input"
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
for p in Path('out-d8-app-startup/input').rglob('AndroidManifest.xml'):
 r=p.parent
 if (r/'.project').is_file() and (r/'smali').is_dir(): c.append(r)
if len(c)!=1: raise SystemExit(c)
print(c[0])
PY
)"
export PROJECT_ROOT
python3 - <<'PY' > "$OUT/APPLICATION_STARTUP_FORENSICS.txt"
from pathlib import Path
import os,re,json
root=Path(os.environ['PROJECT_ROOT'])

def emit_method(rel,sig):
 p=root/rel; s=p.read_text(encoding='utf-8',errors='replace')
 m=re.search(r'(^\.method[^\n]*'+sig+r'\n.*?^\.end method)',s,re.M|re.S)
 print('\n'+'='*100+'\nFILE',rel,'METHOD',sig+'\n'+'='*100)
 print(m.group(1) if m else 'NOT FOUND')

emit_method(Path('smali_classes2/com/ticktick/task/TickTickApplicationBase.smali'),r'onCreate\(\)V')
emit_method(Path('smali_classes2/com/ticktick/task/TickTickApplicationBase.smali'),r'attachBaseContext\(Landroid/content/Context;\)V')
emit_method(Path('smali_classes2/com/ticktick/task/TickTickApplication.smali'),r'onCreate\(\)V')
emit_method(Path('smali_classes2/com/ticktick/task/TickTickApplication.smali'),r'initFirebaseApp\(\)V')
emit_method(Path('smali_classes2/com/ticktick/task/TickTickApplication.smali'),r'registerActivities\(\)V')

print('\n'+'='*100+'\nALL registerReceiver CALLS IN com/ticktick/task SMALI\n'+'='*100)
needles=['->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;)Landroid/content/Intent;',
         '->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;I)Landroid/content/Intent;',
         '->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;Ljava/lang/String;Landroid/os/Handler;)Landroid/content/Intent;',
         '->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;Ljava/lang/String;Landroid/os/Handler;I)Landroid/content/Intent;']
for p in root.rglob('*.smali'):
 rel=str(p.relative_to(root))
 if 'com/ticktick/task' not in rel: continue
 s=p.read_text(encoding='utf-8',errors='replace')
 if not any(n in s for n in needles): continue
 lines=s.splitlines(); current=''
 for i,l in enumerate(lines):
  if l.startswith('.method '): current=l
  if any(n in l for n in needles):
   print('\nFILE',rel,'LINE',i+1,current)
   for j in range(max(0,i-35),min(len(lines),i+36)): print(f'{j+1:05d}: {lines[j]}')

print('\n'+'='*100+'\nALL CALLERS OF Le7/a;->m()Z\n'+'='*100)
needle='Le7/a;->m()Z'
for p in root.rglob('*.smali'):
 s=p.read_text(encoding='utf-8',errors='replace')
 if needle not in s: continue
 lines=s.splitlines(); current=''
 for i,l in enumerate(lines):
  if l.startswith('.method '): current=l
  if needle in l:
   print('\nFILE',p.relative_to(root),'LINE',i+1,current)
   for j in range(max(0,i-25),min(len(lines),i+35)): print(f'{j+1:05d}: {lines[j]}')

print('\n'+'='*100+'\nSOURCE SDK METADATA\n'+'='*100)
for name in ['apktool.json','apktool.yml']:
 p=root/name
 if p.exists():
  print('\n---',name,'---')
  print(p.read_text(encoding='utf-8',errors='replace')[:30000])
manifest=(root/'AndroidManifest.xml').read_text(encoding='utf-8',errors='replace')
print('\n--- manifest uses-sdk / permissions / app flags ---')
for i,l in enumerate(manifest.splitlines(),1):
 if '<uses-sdk' in l or '<uses-permission' in l or '<application ' in l:
  print(f'{i:05d}: {l}')

print('\n'+'='*100+'\nUNCAUGHT EXCEPTION HANDLER INSTALLATION SITES\n'+'='*100)
for needle in ['setDefaultUncaughtExceptionHandler','CrashLogHandler;-><init>','ActivityThreadCallback;->']:
 print('\nNEEDLE',needle)
 for p in root.rglob('*.smali'):
  s=p.read_text(encoding='utf-8',errors='replace')
  if needle not in s: continue
  lines=s.splitlines(); current=''
  for i,l in enumerate(lines):
   if l.startswith('.method '): current=l
   if needle in l:
    print('FILE',p.relative_to(root),'LINE',i+1,current)
    for j in range(max(0,i-25),min(len(lines),i+30)): print(f'{j+1:05d}: {lines[j]}')
PY

echo "Application startup forensics complete"
