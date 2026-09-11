#!/usr/bin/env bash
set -euo pipefail
OUT=out-d9-receiver-forensics
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
for p in Path('out-d9-receiver-forensics/input').rglob('AndroidManifest.xml'):
 r=p.parent
 if (r/'.project').is_file() and (r/'smali').is_dir(): c.append(r)
if len(c)!=1: raise SystemExit(c)
print(c[0])
PY
)"
export PROJECT_ROOT
python3 - <<'PY' > "$OUT/DYNAMIC_RECEIVER_FORENSICS.txt"
from pathlib import Path
import os,re
root=Path(os.environ['PROJECT_ROOT'])
legacy2='->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;)Landroid/content/Intent;'
legacy4='->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;Ljava/lang/String;Landroid/os/Handler;)Landroid/content/Intent;'
flag3='->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;I)Landroid/content/Intent;'
flag5='->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;Ljava/lang/String;Landroid/os/Handler;I)Landroid/content/Intent;'
needles=[legacy2,legacy4,flag3,flag5]

def method_bounds(lines, idx):
    a=idx
    while a>=0 and not lines[a].startswith('.method '): a-=1
    b=idx
    while b<len(lines) and not lines[b].startswith('.end method'): b+=1
    return max(a,0), min(b,len(lines)-1)

def actions_from_block(block):
    out=[]
    for l in block:
        m=re.search(r'const-string(?:/jumbo)?\s+[^,]+,\s+"([^"]+)"',l)
        if m: out.append(m.group(1))
    return out

calls=[]
for p in root.rglob('*.smali'):
    s=p.read_text(encoding='utf-8',errors='replace')
    if 'registerReceiver' not in s: continue
    lines=s.splitlines()
    for i,l in enumerate(lines):
        which=next((n for n in needles if n in l),None)
        if not which: continue
        a,b=method_bounds(lines,i)
        block=lines[a:b+1]
        calls.append((p.relative_to(root),i+1,lines[a],which,actions_from_block(block),block))

print('ROOT',root)
print('TOTAL_REGISTER_RECEIVER_CALLS',len(calls))
print('LEGACY_2ARG',sum(c[3]==legacy2 for c in calls))
print('LEGACY_4ARG',sum(c[3]==legacy4 for c in calls))
print('FLAGGED_3ARG',sum(c[3]==flag3 for c in calls))
print('FLAGGED_5ARG',sum(c[3]==flag5 for c in calls))
print('\n'+'='*110+'\nALL RECEIVER CALL SITES\n'+'='*110)
for rel,line,method,which,actions,block in calls:
    print('\nFILE',rel,'LINE',line)
    print('METHOD',method)
    print('OVERLOAD', 'LEGACY_2ARG' if which==legacy2 else 'LEGACY_4ARG' if which==legacy4 else 'FLAGGED_3ARG' if which==flag3 else 'FLAGGED_5ARG')
    print('CONST_STRING_ACTION_CANDIDATES',actions)
    for j,x in enumerate(block,1): print(f'{j:05d}: {x}')

print('\n'+'='*110+'\nSTARTUP APPLICATION METHODS AND CALL GRAPH SEEDS\n'+'='*110)
seeds=[
 ('smali_classes2/com/ticktick/task/TickTickApplication.smali',['onCreate()V','registerActivities()V','settingsIntentFilter()Landroid/content/IntentFilter;']),
 ('smali_classes2/com/ticktick/task/TickTickApplicationBase.smali',['onCreate()V','registerGlobalBroadcastReceiver()V','attachBaseContext(Landroid/content/Context;)V'])]
for rel,sigs in seeds:
 p=root/rel
 if not p.exists(): continue
 s=p.read_text(encoding='utf-8',errors='replace')
 for sig in sigs:
  name=sig.split('(')[0]
  pat=re.compile(r'(^\.method[^\n]*\b'+re.escape(name)+r'\([^\n]*\n.*?^\.end method)',re.M|re.S)
  m=pat.search(s)
  print('\nFILE',rel,'METHOD',sig)
  print(m.group(1) if m else 'NOT FOUND')

print('\n'+'='*110+'\nMETHODS WHOSE NAMES SUGGEST RECEIVER REGISTRATION\n'+'='*110)
for p in root.rglob('*.smali'):
 s=p.read_text(encoding='utf-8',errors='replace')
 if 'registerReceiver' not in s and 'IntentFilter' not in s: continue
 lines=s.splitlines()
 for i,l in enumerate(lines):
  if l.startswith('.method ') and re.search(r'(register|Receiver|IntentFilter|Broadcast)',l,re.I):
   b=i+1
   while b<len(lines) and not lines[b].startswith('.end method'): b+=1
   block=lines[i:min(b+1,len(lines))]
   if any('registerReceiver' in x or 'IntentFilter' in x for x in block):
    print('\nFILE',p.relative_to(root),'LINE',i+1,l)
    for x in block: print(x)

print('\n'+'='*110+'\nSDK AND MANIFEST METADATA\n'+'='*110)
for name in ['apktool.yml','apktool.json']:
 p=root/name
 if p.exists(): print('\n---',name,'---\n',p.read_text(encoding='utf-8',errors='replace')[:30000])
manifest=(root/'AndroidManifest.xml').read_text(encoding='utf-8',errors='replace')
for i,l in enumerate(manifest.splitlines(),1):
 if '<uses-sdk' in l or '<uses-permission' in l or '<application ' in l:
  print(f'{i:05d}: {l}')

print('\n'+'='*110+'\nANDROIDX CONTEXTCOMPAT RECEIVER SUPPORT\n'+'='*110)
for p in root.rglob('*.smali'):
 s=p.read_text(encoding='utf-8',errors='replace')
 if 'ContextCompat;->registerReceiver' in s:
  print('FILE',p.relative_to(root))
  for i,l in enumerate(s.splitlines(),1):
   if 'ContextCompat;->registerReceiver' in l: print(i,l)
PY

echo 'receiver_forensics=PASS' > "$OUT/STATUS.txt"
echo 'physical_d8_samsung_android16=FAIL' >> "$OUT/STATUS.txt"
echo 'final_go=false' >> "$OUT/STATUS.txt"
echo 'PASS: DIRECTIVE 9 dynamic receiver forensics complete'
