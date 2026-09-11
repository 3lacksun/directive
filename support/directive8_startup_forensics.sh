#!/usr/bin/env bash
set -euo pipefail

mkdir -p out-d8-forensics
python3 - <<'PY' > /tmp/directive_source.env
import json, shlex
j=json.load(open('DIRECTIVE2_SOURCE.json'))
print('SOURCE_URL='+shlex.quote(j['url']))
print('SOURCE_SHA256='+shlex.quote(j['sha256']))
PY
source /tmp/directive_source.env
curl -fL --retry 5 --retry-delay 2 "$SOURCE_URL" -o out-d8-forensics/source.zip
echo "$SOURCE_SHA256  out-d8-forensics/source.zip" | sha256sum -c -
rm -rf out-d8-forensics/input && mkdir -p out-d8-forensics/input
unzip -q out-d8-forensics/source.zip -d out-d8-forensics/input
PROJECT_ROOT="$(python3 - <<'PY'
from pathlib import Path
c=[]
for p in Path('out-d8-forensics/input').rglob('AndroidManifest.xml'):
    r=p.parent
    if (r/'.project').is_file() and (r/'res').is_dir() and (r/'smali').is_dir(): c.append(r)
if len(c)!=1: raise SystemExit(c)
print(c[0])
PY
)"
export PROJECT_ROOT
python3 - <<'PY' | tee out-d8-forensics/STARTUP_FORENSICS.txt
from pathlib import Path
import os,re,xml.etree.ElementTree as ET
root=Path(os.environ['PROJECT_ROOT'])
print('PROJECT_ROOT',root)
print('\n=== MANIFEST STARTUP COMPONENTS ===')
manifest=(root/'AndroidManifest.xml').read_text(encoding='utf-8',errors='replace')
for pat in [r'<application\b[^>]*>',r'<provider\b[^>]*>',r'<activity\b[^>]*MeTaskActivity[^>]*>',r'<activity-alias\b[^>]*HomeAlia_default[^>]*>']:
    for m in re.finditer(pat,manifest,re.S):
        print(' '.join(m.group(0).split()))

print('\n=== TICKTICK APPLICATION CLASS ===')
apps=list(root.rglob('TickTickApplication.smali'))
for p in apps:
    print('FILE',p.relative_to(root))
    s=p.read_text(encoding='utf-8',errors='replace')
    for method in ['<clinit>()V','attachBaseContext(Landroid/content/Context;)V','onCreate()V']:
        m=re.search(r'\.method[^\n]* '+re.escape(method)+r'\n(.*?)\.end method',s,re.S)
        if m:
            print('\nMETHOD',method)
            print(m.group(1)[:30000])

print('\n=== MAIN ACTIVITY STARTUP METHODS ===')
acts=list(root.rglob('MeTaskActivity.smali'))
for p in acts:
    print('FILE',p.relative_to(root))
    s=p.read_text(encoding='utf-8',errors='replace')
    for method_rx in [r'onCreate\(Landroid/os/Bundle;\)V',r'attachBaseContext\(Landroid/content/Context;\)V',r'onStart\(\)V',r'onResume\(\)V']:
        m=re.search(r'\.method[^\n]* '+method_rx+r'\n(.*?)\.end method',s,re.S)
        if m:
            print('\nMETHOD',method_rx)
            print(m.group(1)[:30000])

print('\n=== EXACT LEGACY PACKAGE LITERALS WITH METHOD CONTEXT ===')
count=0
for p in root.rglob('*.smali'):
    try:s=p.read_text(encoding='utf-8',errors='replace')
    except:continue
    if '"com.ticktick.task"' not in s: continue
    lines=s.splitlines(); current=''
    for i,line in enumerate(lines,1):
        if line.startswith('.method '): current=line.strip()
        if '"com.ticktick.task"' in line:
            print(f'{p.relative_to(root)}:{i}: {current} :: {line.strip()}')
            count+=1
print('TOTAL_EXACT_PACKAGE_LITERALS',count)

print('\n=== PACKAGE NAME / COMPONENT ENABLEMENT / PROCESS TERMINATION SITES ===')
needles=['getPackageName()Ljava/lang/String;','setComponentEnabledSetting','killProcess','System;->exit','Runtime;->exit','finishAffinity','uncaughtException','loadLibrary']
for needle in needles:
    print('\n--',needle,'--')
    n=0
    for p in root.rglob('*.smali'):
        try:s=p.read_text(encoding='utf-8',errors='replace')
        except:continue
        if needle not in s: continue
        lines=s.splitlines(); current=''
        for i,line in enumerate(lines,1):
            if line.startswith('.method '): current=line.strip()
            if needle in line:
                lo=max(0,i-4); hi=min(len(lines),i+5)
                print(f'FILE {p.relative_to(root)}:{i} {current}')
                print('\n'.join(lines[lo:hi]))
                n+=1
                if n>=80: break
        if n>=80: break
    print('COUNT_SHOWN',n)

print('\n=== PROVIDER AUTHORITIES / INIT PROVIDERS ===')
for m in re.finditer(r'<provider\b.*?(?:/>|</provider>)',manifest,re.S):
    block=' '.join(m.group(0).split())
    if any(x in block.lower() for x in ['init','startup','firebase','bugsnag','provider']): print(block)
PY

echo 'FORensics complete'
