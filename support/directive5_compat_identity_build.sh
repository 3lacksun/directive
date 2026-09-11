#!/usr/bin/env bash
set -euo pipefail

BUILD_TOOLS_VERSION="${BUILD_TOOLS_VERSION:-35.0.0}"
ANDROID_PLATFORM="${ANDROID_PLATFORM:-android-35}"
MIN_SDK="${MIN_SDK:-21}"
APKTOOL_VERSION="${APKTOOL_VERSION:-2.12.1}"
APKTOOL_SHA256="${APKTOOL_SHA256:-66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa}"
ANDROID_HOME="${ANDROID_HOME:-/usr/local/lib/android/sdk}"
export ANDROID_HOME ANDROID_SDK_ROOT="$ANDROID_HOME"

OUT=out-v15
mkdir -p "$OUT/evidence"
python3 - <<'PY' > /tmp/directive_source.env
import json, shlex
d=json.load(open('DIRECTIVE2_SOURCE.json'))
assert d['sha256']=='78263f9236855d40e522596f21630dd134e380c55d7f3a7814caedf5bfa4d3a3'
print('SOURCE_URL='+shlex.quote(d['url']))
print('SOURCE_SHA256='+shlex.quote(d['sha256']))
PY
source /tmp/directive_source.env
curl -fL --retry 5 --retry-delay 2 "$SOURCE_URL" -o "$OUT/source.zip"
echo "$SOURCE_SHA256  $OUT/source.zip" | sha256sum -c - | tee "$OUT/evidence/SOURCE_SHA_VERIFY.txt"
unzip -t "$OUT/source.zip" > "$OUT/evidence/SOURCE_ZIP_TEST.txt"
rm -rf "$OUT/input" && mkdir -p "$OUT/input"
unzip -q "$OUT/source.zip" -d "$OUT/input"

PROJECT_ROOT="$(python3 - <<'PY'
from pathlib import Path
c=[]
for p in Path('out-v15/input').rglob('AndroidManifest.xml'):
    r=p.parent
    if (r/'.project').is_file() and (r/'res').is_dir() and (r/'smali').is_dir(): c.append(r)
if len(c)!=1: raise SystemExit(f'expected one project root, got {c}')
print(c[0])
PY
)"
export PROJECT_ROOT
printf 'PROJECT_ROOT=%s\n' "$PROJECT_ROOT" | tee "$OUT/evidence/PROJECT_ROOT.txt"

python3 - <<'PY'
import os, pathlib, json, re
root=pathlib.Path(os.environ['PROJECT_ROOT'])
for p in (root/'res').rglob('*.original'): p.unlink()

# Compatibility baseline: restore the installed Android package identity that the
# inherited application code and original offline rebrand were designed around.
# This does not rename Java/JNI classes and does not touch auth/licensing logic.
text_ext={'.xml','.smali','.java','.json','.txt','.properties','.html','.js','.css','.md','.yml','.yaml'}
replacements={
    'com.directive.v2':'com.ticktick.task',
    'DIRECTIVE 2':'DIRECTIVE 5',
}
counts={k:0 for k in replacements}
for p in root.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in text_ext: continue
    try:s=p.read_text(encoding='utf-8')
    except Exception:continue
    old=s
    for a,b in replacements.items():
        n=s.count(a)
        if n: counts[a]+=n; s=s.replace(a,b)
    if s!=old:p.write_text(s,encoding='utf-8')

manifest=root/'AndroidManifest.xml'
s=manifest.read_text(encoding='utf-8')
s=re.sub(r'android:versionCode="[^"]+"','android:versionCode="8500"',s,count=1)
s=re.sub(r'android:versionName="[^"]+"','android:versionName="5.0.0"',s,count=1)
manifest.write_text(s,encoding='utf-8')

# Compile correction retained from verified GitHub build chain.
p=root/'src/com/directive/planner/DirectiveCalendarProviderSync.java'
if p.is_file():
    s=p.read_text()
    if 'Build.VERSION' in s and 'import android.os.Build;' not in s:
        p.write_text(s.replace('package com.directive.planner;','package com.directive.planner;\nimport android.os.Build;',1))

launch=root/'res/drawable/directive_launch_background.xml'
if launch.is_file():
    s=launch.read_text()
    s=s.replace('<item android:drawable="#F4F6F9"/>','<item><shape android:shape="rectangle"><solid android:color="#F4F6F9"/></shape></item>',1)
    launch.write_text(s)

meta=json.loads((root/'apktool.json').read_text())
def q(v):
    if v is None:return 'null'
    if isinstance(v,bool):return 'true' if v else 'false'
    return json.dumps(str(v),ensure_ascii=False)
out=['version: '+q('2.12.1'),'apkFileName: '+q('DIRECTIVE_5_5.0.0_8500.apk'),'isFrameworkApk: false']
uf=meta.get('UsesFramework') or {}; out+=['usesFramework:','  ids:']+[f'  - {i}' for i in uf.get('ids',[1])]+['  tag: '+q(uf.get('tag'))]
out+=['sdkInfo:','  minSdkVersion: "21"','  targetSdkVersion: "37"']
pi=meta.get('PackageInfo') or {}; out+=['packageInfo:','  forcedPackageId: '+q(pi.get('forcedPackageId','127')),'  renameManifestPackage: null']
out+=['versionInfo:','  versionCode: "8500"','  versionName: "5.0.0"','resourcesAreCompressed: false','sharedLibrary: false','sparseResources: '+('true' if meta.get('sparseResources',False) else 'false'),'doNotCompress:']
out += ['- '+q(x) for x in meta.get('doNotCompress',[])]
out += ['unknownFiles:']+['  '+q(k)+': '+q(v) for k,v in sorted((meta.get('unknownFiles') or {}).items())]
(root/'apktool.yml').write_text('\n'.join(out)+'\n')

m=manifest.read_text()
assert 'package="com.ticktick.task"' in m
assert 'android:versionCode="8500"' in m and 'android:versionName="5.0.0"' in m
for x in ['INTERNET','ACCESS_NETWORK_STATE','ACCESS_WIFI_STATE','CHANGE_NETWORK_STATE','CHANGE_WIFI_STATE']:
    if f'android.permission.{x}' in m: raise SystemExit('forbidden network permission '+x)
for x in ['READ_CALENDAR','WRITE_CALENDAR']:
    if f'android.permission.{x}' not in m: raise SystemExit('missing '+x)
report={
 'status':'PASS','target_package':'com.ticktick.task','target_label':'DIRECTIVE 5',
 'version_name':'5.0.0','version_code':8500,'replacement_counts':counts,
 'compatibility_mode':'restore original installed package identity while retaining DIRECTIVE visible branding',
 'internal_class_namespace':'com.ticktick.task preserved','auth_licensing_entitlement_modified':False,
 'final_identity_status':'diagnostic compatibility baseline; numbered com.directive package migration remains unresolved'
}
(root/'DIRECTIVE5_COMPAT_IDENTITY_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
PY

python3 support/patch_directive_launcher_identity.py "$PROJECT_ROOT" | tee "$OUT/evidence/LAUNCHER_IDENTITY_REMEDIATION.txt"
cp "$PROJECT_ROOT/DIRECTIVE5_COMPAT_IDENTITY_REPORT.json" "$OUT/evidence/"
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json" "$OUT/evidence/"

curl -fL --retry 5 --retry-delay 2 "https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VERSION}/apktool_${APKTOOL_VERSION}.jar" -o "$OUT/apktool.jar"
echo "$APKTOOL_SHA256  $OUT/apktool.jar" | sha256sum -c -
rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist"
java -Xmx8g -jar "$OUT/apktool.jar" b -f "$PROJECT_ROOT" -o "$OUT/DIRECTIVE_5_base_unsigned.apk" 2>&1 | tee "$OUT/evidence/APKTOOL_BUILD_LOG.txt"
test -s "$OUT/DIRECTIVE_5_base_unsigned.apk"

ANDROID_JAR="$ANDROID_HOME/platforms/$ANDROID_PLATFORM/android.jar"
rm -rf "$OUT/classes" "$OUT/extdex" && mkdir -p "$OUT/classes" "$OUT/extdex"
mapfile -t JAVA_FILES < <(find "$PROJECT_ROOT/src" -type f -name '*.java' | sort)
javac -encoding UTF-8 -source 8 -target 8 -cp "$ANDROID_JAR" -d "$OUT/classes" "${JAVA_FILES[@]}" 2>&1 | tee "$OUT/evidence/JAVAC_EXTENSION_LOG.txt"
jar cf "$OUT/DIRECTIVE_LOCAL_EXTENSION.jar" -C "$OUT/classes" .
"$ANDROID_HOME/build-tools/$BUILD_TOOLS_VERSION/d8" --lib "$ANDROID_JAR" --min-api "$MIN_SDK" --output "$OUT/extdex" "$OUT/DIRECTIVE_LOCAL_EXTENSION.jar"

python3 - <<'PY'
import zipfile,re,shutil,pathlib
src=pathlib.Path('out-v15/DIRECTIVE_5_base_unsigned.apk'); dst=pathlib.Path('out-v15/DIRECTIVE_5_with_extension.apk'); ext=pathlib.Path('out-v15/extdex/classes.dex')
shutil.copy2(src,dst)
with zipfile.ZipFile(dst,'a') as z:
    nums=[]
    for n in z.namelist():
        m=re.fullmatch(r'classes(\d*)\.dex',n)
        if m:nums.append(int(m.group(1) or '1'))
    name=f'classes{max(nums)+1}.dex'
    z.writestr(name,ext.read_bytes(),compress_type=zipfile.ZIP_STORED)
    print('Injected',name)
PY

BT="$ANDROID_HOME/build-tools/$BUILD_TOOLS_VERSION"
"$BT/zipalign" -f -P 16 4 "$OUT/DIRECTIVE_5_with_extension.apk" "$OUT/DIRECTIVE_5_aligned.apk"
"$BT/zipalign" -c -P 16 4 "$OUT/DIRECTIVE_5_aligned.apk" | tee "$OUT/evidence/ZIPALIGN.txt"
keytool -genkeypair -noprompt -keystore "$OUT/directive5-test.jks" -storepass android -keypass android -alias directive5test -keyalg RSA -keysize 3072 -validity 3650 -dname 'CN=DIRECTIVE 5 Compatibility Test, O=NexaRenew, C=GB'
"$BT/apksigner" sign --ks "$OUT/directive5-test.jks" --ks-key-alias directive5test --ks-pass pass:android --key-pass pass:android --out "$OUT/DIRECTIVE_5_5.0.0_COMPAT_IDENTITY_TEST.apk" "$OUT/DIRECTIVE_5_aligned.apk"
"$BT/apksigner" verify --verbose --print-certs "$OUT/DIRECTIVE_5_5.0.0_COMPAT_IDENTITY_TEST.apk" | tee "$OUT/evidence/APKSIGNER_VERIFY.txt"
"$BT/aapt" dump badging "$OUT/DIRECTIVE_5_5.0.0_COMPAT_IDENTITY_TEST.apk" | tee "$OUT/evidence/APK_BADGING.txt"
"$BT/aapt" dump permissions "$OUT/DIRECTIVE_5_5.0.0_COMPAT_IDENTITY_TEST.apk" | tee "$OUT/evidence/APK_PERMISSIONS.txt"

grep -Fq "package: name='com.ticktick.task' versionCode='8500' versionName='5.0.0'" "$OUT/evidence/APK_BADGING.txt"
grep -Fq "application-label:'DIRECTIVE 5'" "$OUT/evidence/APK_BADGING.txt"
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' "$OUT/evidence/APK_PERMISSIONS.txt"
grep -Fq 'android.permission.READ_CALENDAR' "$OUT/evidence/APK_PERMISSIONS.txt"
grep -Fq 'android.permission.WRITE_CALENDAR' "$OUT/evidence/APK_PERMISSIONS.txt"
sha256sum "$OUT/DIRECTIVE_5_5.0.0_COMPAT_IDENTITY_TEST.apk" | tee "$OUT/evidence/SHA256SUMS.txt"
printf '%s\n' \
 'build=PASS' \
 'static_verification=PASS' \
 'package_identity=com.ticktick.task' \
 'visible_label=DIRECTIVE 5' \
 'offline_network_permission_gate=PASS' \
 'auth_licensing_entitlement_logic=UNCHANGED' \
 'physical_android16_acceptance=UNEXECUTED' \
 'numbered_package_migration=UNRESOLVED' \
 'final_go=false' > "$OUT/evidence/BUILD_STATUS.txt"

echo 'PASS: DIRECTIVE 5 compatibility-identity candidate built and statically verified'
