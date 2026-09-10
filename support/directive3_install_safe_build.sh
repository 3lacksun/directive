#!/usr/bin/env bash
set -euo pipefail

BUILD_TOOLS_VERSION="${BUILD_TOOLS_VERSION:-35.0.0}"
ANDROID_PLATFORM="${ANDROID_PLATFORM:-android-35}"
MIN_SDK="${MIN_SDK:-21}"
APKTOOL_VERSION="${APKTOOL_VERSION:-2.12.1}"
APKTOOL_SHA256="${APKTOOL_SHA256:-66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa}"
ANDROID_HOME="${ANDROID_HOME:-/usr/local/lib/android/sdk}"
export ANDROID_HOME ANDROID_SDK_ROOT="$ANDROID_HOME"

mkdir -p out-v8/evidence
python3 - <<'PY' > /tmp/directive_source.env
import json, shlex
d=json.load(open('DIRECTIVE2_SOURCE.json'))
assert d['sha256']=='78263f9236855d40e522596f21630dd134e380c55d7f3a7814caedf5bfa4d3a3'
print('SOURCE_URL='+shlex.quote(d['url']))
print('SOURCE_SHA256='+shlex.quote(d['sha256']))
PY
source /tmp/directive_source.env
curl -fL --retry 5 --retry-delay 2 "$SOURCE_URL" -o out-v8/source.zip
echo "$SOURCE_SHA256  out-v8/source.zip" | sha256sum -c - | tee out-v8/evidence/SOURCE_SHA_VERIFY.txt
unzip -t out-v8/source.zip > out-v8/evidence/SOURCE_ZIP_TEST.txt
rm -rf out-v8/input && mkdir -p out-v8/input
unzip -q out-v8/source.zip -d out-v8/input

PROJECT_ROOT="$(python3 - <<'PY'
from pathlib import Path
c=[]
for p in Path('out-v8/input').rglob('AndroidManifest.xml'):
    r=p.parent
    if (r/'.project').is_file() and (r/'res').is_dir() and (r/'smali').is_dir(): c.append(r)
if len(c)!=1: raise SystemExit(f'expected one project root, got {c}')
print(c[0])
PY
)"
export PROJECT_ROOT
printf 'PROJECT_ROOT=%s\n' "$PROJECT_ROOT" | tee out-v8/evidence/PROJECT_ROOT.txt

python3 - <<'PY'
import os, pathlib, json, re
root=pathlib.Path(os.environ['PROJECT_ROOT'])

# Remove editor-only resource backups that aapt2 rejects.
for p in (root/'res').rglob('*.original'): p.unlink()

# Side-by-side install identity. Internal inherited class namespaces are intentionally preserved.
replacements={
    'com.directive.v2':'com.directive.v3',
    'DIRECTIVE 2':'DIRECTIVE 3',
    'com.ticktick.task.permission.signature':'com.directive.v3.permission.signature',
    'com.ticktick.task.permission.READ_TASKS':'com.directive.v3.permission.READ_TASKS',
    'com.ticktick.task.permission.WEAR_ACCESS':'com.directive.v3.permission.WEAR_ACCESS',
    'com.ticktick.task.permission.WEAR_DATA_CHANGED_BROADCAST':'com.directive.v3.permission.WEAR_DATA_CHANGED_BROADCAST',
    'com.ticktick.task.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION':'com.directive.v3.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION',
    'com.facebook.app.FacebookContentProvider687713684576416':'com.directive.v3.facebookcontentprovider',
}
text_ext={'.xml','.smali','.java','.json','.txt','.properties','.html','.js','.css','.md','.yml','.yaml'}
counts={k:0 for k in replacements}
for p in root.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in text_ext: continue
    try: s=p.read_text(encoding='utf-8')
    except Exception: continue
    old=s
    for a,b in replacements.items():
        n=s.count(a)
        if n: counts[a]+=n; s=s.replace(a,b)
    if s!=old: p.write_text(s,encoding='utf-8')

manifest=root/'AndroidManifest.xml'
s=manifest.read_text(encoding='utf-8')
s=re.sub(r'android:versionCode="[^"]+"','android:versionCode="8300"',s,count=1)
s=re.sub(r'android:versionName="[^"]+"','android:versionName="3.0.0"',s,count=1)
manifest.write_text(s,encoding='utf-8')

# Compile correction from v6.
p=root/'src/com/directive/planner/DirectiveCalendarProviderSync.java'
if p.is_file():
    s=p.read_text()
    if 'Build.VERSION' in s and 'import android.os.Build;' not in s:
        p.write_text(s.replace('package com.directive.planner;','package com.directive.planner;\nimport android.os.Build;',1))

# aapt2 requires a drawable resource rather than a literal colour in android:drawable.
launch=root/'res/drawable/directive_launch_background.xml'
if launch.is_file():
    s=launch.read_text()
    s=s.replace('<item android:drawable="#F4F6F9"/>','<item><shape android:shape="rectangle"><solid android:color="#F4F6F9"/></shape></item>',1)
    launch.write_text(s)

# Build standard Apktool metadata from APK Builder/Apktool-M JSON.
meta=json.loads((root/'apktool.json').read_text())
def q(v):
    if v is None:return 'null'
    if isinstance(v,bool):return 'true' if v else 'false'
    return json.dumps(str(v),ensure_ascii=False)
out=['version: '+q('2.12.1'),'apkFileName: '+q('DIRECTIVE_3_3.0.0_8300.apk'),'isFrameworkApk: false']
uf=meta.get('UsesFramework') or {}; out+=['usesFramework:','  ids:']+[f'  - {i}' for i in uf.get('ids',[1])]+['  tag: '+q(uf.get('tag'))]
out+=['sdkInfo:','  minSdkVersion: "21"','  targetSdkVersion: "37"']
pi=meta.get('PackageInfo') or {}; out+=['packageInfo:','  forcedPackageId: '+q(pi.get('forcedPackageId','127')),'  renameManifestPackage: null']
out+=['versionInfo:','  versionCode: "8300"','  versionName: "3.0.0"','resourcesAreCompressed: false','sharedLibrary: false','sparseResources: '+('true' if meta.get('sparseResources',False) else 'false'),'doNotCompress:']
out += ['- '+q(x) for x in meta.get('doNotCompress',[])]
out += ['unknownFiles:']+['  '+q(k)+': '+q(v) for k,v in sorted((meta.get('unknownFiles') or {}).items())]
(root/'apktool.yml').write_text('\n'.join(out)+'\n')

# Fail-closed source gates for known installation collisions.
m=manifest.read_text()
assert 'package="com.directive.v3"' in m
assert 'android:versionCode="8300"' in m and 'android:versionName="3.0.0"' in m
for x in ['INTERNET','ACCESS_NETWORK_STATE','ACCESS_WIFI_STATE','CHANGE_NETWORK_STATE','CHANGE_WIFI_STATE']:
    if f'android.permission.{x}' in m: raise SystemExit('forbidden network permission '+x)
for x in ['READ_CALENDAR','WRITE_CALENDAR']:
    if f'android.permission.{x}' not in m: raise SystemExit('missing '+x)
for old in ['com.ticktick.task.permission.signature','com.ticktick.task.permission.READ_TASKS','com.ticktick.task.permission.WEAR_ACCESS','com.ticktick.task.permission.WEAR_DATA_CHANGED_BROADCAST','com.ticktick.task.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION','com.facebook.app.FacebookContentProvider687713684576416']:
    if old in m: raise SystemExit('install-collision identifier remains: '+old)

report={'status':'PASS','target_package':'com.directive.v3','target_label':'DIRECTIVE 3','version_name':'3.0.0','version_code':8300,'replacement_counts':counts,'protected_auth_or_entitlement_state_changed':False,'note':'Side-by-side install-safe diagnostic successor; inherited internal class namespaces intentionally preserved.'}
(root/'DIRECTIVE_INSTALL_COLLISION_REMEDIATION_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
PY
cp "$PROJECT_ROOT/DIRECTIVE_INSTALL_COLLISION_REMEDIATION_REPORT.json" out-v8/evidence/

curl -fL --retry 5 --retry-delay 2 "https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VERSION}/apktool_${APKTOOL_VERSION}.jar" -o out-v8/apktool.jar
echo "$APKTOOL_SHA256  out-v8/apktool.jar" | sha256sum -c -
rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist"
java -Xmx8g -jar out-v8/apktool.jar b -f "$PROJECT_ROOT" -o out-v8/DIRECTIVE_3_base_unsigned.apk 2>&1 | tee out-v8/evidence/APKTOOL_BUILD_LOG.txt
test -s out-v8/DIRECTIVE_3_base_unsigned.apk

ANDROID_JAR="$ANDROID_HOME/platforms/$ANDROID_PLATFORM/android.jar"
rm -rf out-v8/classes out-v8/extdex && mkdir -p out-v8/classes out-v8/extdex
mapfile -t JAVA_FILES < <(find "$PROJECT_ROOT/src" -type f -name '*.java' | sort)
javac -encoding UTF-8 -source 8 -target 8 -cp "$ANDROID_JAR" -d out-v8/classes "${JAVA_FILES[@]}" 2>&1 | tee out-v8/evidence/JAVAC_EXTENSION_LOG.txt
jar cf out-v8/DIRECTIVE_LOCAL_EXTENSION.jar -C out-v8/classes .
"$ANDROID_HOME/build-tools/$BUILD_TOOLS_VERSION/d8" --lib "$ANDROID_JAR" --min-api "$MIN_SDK" --output out-v8/extdex out-v8/DIRECTIVE_LOCAL_EXTENSION.jar

python3 - <<'PY'
import zipfile,re,shutil,pathlib
src=pathlib.Path('out-v8/DIRECTIVE_3_base_unsigned.apk'); dst=pathlib.Path('out-v8/DIRECTIVE_3_with_extension.apk'); ext=pathlib.Path('out-v8/extdex/classes.dex')
shutil.copy2(src,dst)
with zipfile.ZipFile(dst,'a') as z:
    nums=[]
    for n in z.namelist():
        m=re.fullmatch(r'classes(\d*)\.dex',n)
        if m: nums.append(int(m.group(1) or '1'))
    name=f'classes{max(nums)+1}.dex'
    z.writestr(name,ext.read_bytes(),compress_type=zipfile.ZIP_STORED)
    print('Injected',name)
PY

BT="$ANDROID_HOME/build-tools/$BUILD_TOOLS_VERSION"
"$BT/zipalign" -f -P 16 4 out-v8/DIRECTIVE_3_with_extension.apk out-v8/DIRECTIVE_3_aligned.apk
"$BT/zipalign" -c -P 16 4 out-v8/DIRECTIVE_3_aligned.apk | tee out-v8/evidence/ZIPALIGN.txt

# One build identity for this side-by-side candidate. This is NOT the established V2 signer.
keytool -genkeypair -noprompt -keystore out-v8/directive3-test.jks -storepass android -keypass android -alias directive3test -keyalg RSA -keysize 3072 -validity 3650 -dname 'CN=DIRECTIVE 3 Install Safe Test, O=NexaRenew, C=GB'
"$BT/apksigner" sign --ks out-v8/directive3-test.jks --ks-key-alias directive3test --ks-pass pass:android --key-pass pass:android --out out-v8/DIRECTIVE_3_3.0.0_INSTALL_SAFE_TEST.apk out-v8/DIRECTIVE_3_aligned.apk
"$BT/apksigner" verify --verbose --print-certs out-v8/DIRECTIVE_3_3.0.0_INSTALL_SAFE_TEST.apk | tee out-v8/evidence/APKSIGNER_VERIFY.txt
"$BT/aapt" dump badging out-v8/DIRECTIVE_3_3.0.0_INSTALL_SAFE_TEST.apk | tee out-v8/evidence/APK_BADGING.txt
"$BT/aapt" dump permissions out-v8/DIRECTIVE_3_3.0.0_INSTALL_SAFE_TEST.apk | tee out-v8/evidence/APK_PERMISSIONS.txt

grep -Fq "package: name='com.directive.v3' versionCode='8300' versionName='3.0.0'" out-v8/evidence/APK_BADGING.txt
grep -Fq "application-label:'DIRECTIVE 3'" out-v8/evidence/APK_BADGING.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v8/evidence/APK_PERMISSIONS.txt
! grep -Fq 'com.ticktick.task.permission.' out-v8/evidence/APK_PERMISSIONS.txt
! grep -Fq 'com.ticktick.task.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION' out-v8/evidence/APK_PERMISSIONS.txt
grep -Fq 'com.directive.v3.permission.signature' out-v8/evidence/APK_PERMISSIONS.txt
grep -Fq 'android.permission.READ_CALENDAR' out-v8/evidence/APK_PERMISSIONS.txt
grep -Fq 'android.permission.WRITE_CALENDAR' out-v8/evidence/APK_PERMISSIONS.txt
sha256sum out-v8/DIRECTIVE_3_3.0.0_INSTALL_SAFE_TEST.apk | tee out-v8/evidence/SHA256SUMS.txt
printf '%s\n' 'build=PASS' 'static_verification=PASS' 'install_collision_namespace_remediation=PASS' 'package=com.directive.v3' 'label=DIRECTIVE 3' 'signing=SIDE_BY_SIDE_TEST_KEY' 'same_package_v2_upgrade=NOT_APPLICABLE' 'physical_acceptance=UNEXECUTED' 'final_go=false' > out-v8/evidence/BUILD_STATUS.txt

echo 'PASS: DIRECTIVE 3 side-by-side install-safe APK built and statically verified'
