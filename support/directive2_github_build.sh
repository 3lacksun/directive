#!/usr/bin/env bash
set -euo pipefail

BUILD_TOOLS_VERSION="${BUILD_TOOLS_VERSION:-35.0.0}"
ANDROID_PLATFORM="${ANDROID_PLATFORM:-android-35}"
MIN_SDK="${MIN_SDK:-21}"
APKTOOL_VERSION="${APKTOOL_VERSION:-2.12.1}"
APKTOOL_SHA256="${APKTOOL_SHA256:-66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa}"
ANDROID_HOME="${ANDROID_HOME:-/usr/local/lib/android/sdk}"
export ANDROID_HOME ANDROID_SDK_ROOT="$ANDROID_HOME"

mkdir -p out/evidence

python3 - <<'PY' > /tmp/directive2_source.env
import json, shlex
d=json.load(open('DIRECTIVE2_SOURCE.json'))
assert d['sha256']=='78263f9236855d40e522596f21630dd134e380c55d7f3a7814caedf5bfa4d3a3'
assert d['filename']=='DIRECTIVE_2_APKBUILDER_1_1_0_PROJECT_09092026105600.zip'
assert d['target_package']=='com.directive.v2'
assert d['target_version_name']=='2.0.4'
assert int(d['target_version_code'])==8204
print('SOURCE_URL='+shlex.quote(d['url']))
print('SOURCE_SHA256='+shlex.quote(d['sha256']))
PY
source /tmp/directive2_source.env

curl -fL --retry 5 --retry-delay 2 "$SOURCE_URL" -o source.zip
echo "$SOURCE_SHA256  source.zip" | sha256sum -c -
unzip -t source.zip > out/evidence/SOURCE_ZIP_TEST.txt
rm -rf input
mkdir input
unzip -q source.zip -d input

PROJECT_ROOT="$(python3 - <<'PY'
from pathlib import Path
c=[]
for p in Path('input').rglob('AndroidManifest.xml'):
    r=p.parent
    if (r/'.project').is_file() and (r/'res').is_dir() and (r/'smali').is_dir():
        c.append(r)
if len(c)!=1:
    raise SystemExit(f'expected exactly one DIRECTIVE project root, got {c}')
print(c[0])
PY
)"
export PROJECT_ROOT
printf 'PROJECT_ROOT=%s\n' "$PROJECT_ROOT" | tee out/evidence/PROJECT_ROOT.txt

python3 - <<'PY'
import os,pathlib,json,re
root=pathlib.Path(os.environ['PROJECT_ROOT'])
manifest=(root/'AndroidManifest.xml').read_text(errors='replace')
assert 'package="com.directive.v2"' in manifest
for x in ['INTERNET','ACCESS_NETWORK_STATE','ACCESS_WIFI_STATE','CHANGE_NETWORK_STATE','CHANGE_WIFI_STATE']:
    if f'android.permission.{x}' in manifest:
        raise SystemExit('forbidden network permission '+x)
for x in ['READ_CALENDAR','WRITE_CALENDAR']:
    if f'android.permission.{x}' not in manifest:
        raise SystemExit('missing '+x)

# Remove editor-only backup files left by APK Builder; they are not Android resources.
backups=list((root/'res').rglob('*.original'))
for p in backups:
    p.unlink()
print('Removed editor backup resources:', [str(p.relative_to(root)) for p in backups])

# Deterministic Java compile correction identified by GitHub javac.
p=root/'src/com/directive/planner/DirectiveCalendarProviderSync.java'
s=p.read_text()
if 'Build.VERSION' in s and 'import android.os.Build;' not in s:
    marker='package com.directive.planner;'
    if marker not in s:
        raise SystemExit('DirectiveCalendarProviderSync package marker missing')
    p.write_text(s.replace(marker, marker+'\nimport android.os.Build;',1))

# Android aapt2 requires drawable references in android:drawable; a literal colour belongs in a shape.
launch=root/'res/drawable/directive_launch_background.xml'
if launch.is_file():
    s=launch.read_text()
    bad='<item android:drawable="#F4F6F9"/>'
    good='<item><shape android:shape="rectangle"><solid android:color="#F4F6F9"/></shape></item>'
    if bad in s:
        launch.write_text(s.replace(bad,good,1))
    if re.search(r'android:drawable\s*=\s*"#[0-9A-Fa-f]{3,8}"',launch.read_text()):
        raise SystemExit('invalid literal colour remains in android:drawable')

# Convert APK Builder/Apktool-M JSON metadata into standard Apktool 2.x metadata.
meta=json.loads((root/'apktool.json').read_text())
def q(v):
    if v is None:return 'null'
    if isinstance(v,bool):return 'true' if v else 'false'
    return json.dumps(str(v),ensure_ascii=False)
out=['version: '+q('2.12.1'),'apkFileName: '+q(meta.get('apkFileName','DIRECTIVE_2_2.0.4_8204.apk')),'isFrameworkApk: false']
uf=meta.get('UsesFramework') or {}
out += ['usesFramework:','  ids:']+[f'  - {i}' for i in uf.get('ids',[1])]+['  tag: '+q(uf.get('tag'))]
sdk=meta.get('sdkInfo') or {}
out += ['sdkInfo:','  minSdkVersion: '+q(sdk.get('minSdkVersion','21')),'  targetSdkVersion: '+q(sdk.get('targetSdkVersion','37'))]
pi=meta.get('PackageInfo') or {}
out += ['packageInfo:','  forcedPackageId: '+q(pi.get('forcedPackageId','127')),'  renameManifestPackage: '+q(pi.get('renameManifestPackage'))]
vi=meta.get('VersionInfo') or {}
out += ['versionInfo:','  versionCode: '+q(vi.get('versionCode','8204')),'  versionName: '+q(vi.get('versionName','2.0.4'))]
out += ['resourcesAreCompressed: false','sharedLibrary: false','sparseResources: '+('true' if meta.get('sparseResources',False) else 'false'),'doNotCompress:']
out += ['- '+q(x) for x in meta.get('doNotCompress',[])]
out += ['unknownFiles:']
out += ['  '+q(k)+': '+q(v) for k,v in sorted((meta.get('unknownFiles') or {}).items())]
(root/'apktool.yml').write_text('\n'.join(out)+'\n')
print('PASS: source normalisation')
PY

curl -fL --retry 5 --retry-delay 2 "https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VERSION}/apktool_${APKTOOL_VERSION}.jar" -o apktool.jar
echo "$APKTOOL_SHA256  apktool.jar" | sha256sum -c -
java -jar apktool.jar --version | tee out/evidence/APKTOOL_VERSION.txt

rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist"
java -Xmx8g -jar apktool.jar b -f "$PROJECT_ROOT" -o out/DIRECTIVE_2_base_unsigned.apk 2>&1 | tee out/evidence/APKTOOL_BUILD_LOG.txt
test -s out/DIRECTIVE_2_base_unsigned.apk
unzip -t out/DIRECTIVE_2_base_unsigned.apk > out/evidence/APKTOOL_BASE_ZIP_TEST.txt

ANDROID_JAR="$ANDROID_HOME/platforms/$ANDROID_PLATFORM/android.jar"
rm -rf out/classes out/extdex
mkdir -p out/classes out/extdex
mapfile -t JAVA_FILES < <(find "$PROJECT_ROOT/src" -type f -name '*.java' | sort)
test "${#JAVA_FILES[@]}" -ge 6
javac -encoding UTF-8 -source 8 -target 8 -cp "$ANDROID_JAR" -d out/classes "${JAVA_FILES[@]}" 2>&1 | tee out/evidence/JAVAC_EXTENSION_LOG.txt
jar cf out/DIRECTIVE_LOCAL_EXTENSION.jar -C out/classes .
"$ANDROID_HOME/build-tools/$BUILD_TOOLS_VERSION/d8" --lib "$ANDROID_JAR" --min-api "$MIN_SDK" --output out/extdex out/DIRECTIVE_LOCAL_EXTENSION.jar
test -s out/extdex/classes.dex
strings out/extdex/classes.dex | grep -Fq 'Lcom/directive/planner/DirectivePlannerActivity;'
strings out/extdex/classes.dex | grep -Fq 'Lcom/directive/reminder/DirectivePersistentAlertService;'
strings out/extdex/classes.dex | grep -Fq 'Lcom/directive/reminder/DirectivePersistentAlertStopReceiver;'

python3 - <<'PY'
import zipfile,re,shutil,pathlib
src=pathlib.Path('out/DIRECTIVE_2_base_unsigned.apk')
dst=pathlib.Path('out/DIRECTIVE_2_with_extension.apk')
ext=pathlib.Path('out/extdex/classes.dex')
shutil.copy2(src,dst)
with zipfile.ZipFile(dst,'a') as z:
    nums=[]
    for n in z.namelist():
        m=re.fullmatch(r'classes(\d*)\.dex',n)
        if m: nums.append(int(m.group(1) or '1'))
    if not nums: raise SystemExit('base APK contains no classes dex')
    name=f'classes{max(nums)+1}.dex'
    z.writestr(name,ext.read_bytes(),compress_type=zipfile.ZIP_STORED)
    print('Injected',name)
PY
unzip -t out/DIRECTIVE_2_with_extension.apk > out/evidence/EXTENSION_INJECT_ZIP_TEST.txt

BT="$ANDROID_HOME/build-tools/$BUILD_TOOLS_VERSION"
"$BT/zipalign" -f -P 16 4 out/DIRECTIVE_2_with_extension.apk out/DIRECTIVE_2_aligned.apk
"$BT/zipalign" -c -P 16 4 out/DIRECTIVE_2_aligned.apk | tee out/evidence/ZIPALIGN.txt
keytool -genkeypair -noprompt -keystore out/test.jks -storepass android -keypass android -alias directive2github -keyalg RSA -keysize 3072 -validity 3650 -dname 'CN=DIRECTIVE 2 GitHub Test, O=NexaRenew, C=GB'
"$BT/apksigner" sign --ks out/test.jks --ks-key-alias directive2github --ks-pass pass:android --key-pass pass:android --out out/DIRECTIVE_2_2.0.4_GITHUB_TEST.apk out/DIRECTIVE_2_aligned.apk
"$BT/apksigner" verify --verbose --print-certs out/DIRECTIVE_2_2.0.4_GITHUB_TEST.apk | tee out/evidence/APKSIGNER_VERIFY.txt
"$BT/aapt" dump badging out/DIRECTIVE_2_2.0.4_GITHUB_TEST.apk | tee out/evidence/APK_BADGING.txt
"$BT/aapt" dump permissions out/DIRECTIVE_2_2.0.4_GITHUB_TEST.apk | tee out/evidence/APK_PERMISSIONS.txt

grep -Fq "package: name='com.directive.v2' versionCode='8204' versionName='2.0.4'" out/evidence/APK_BADGING.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out/evidence/APK_PERMISSIONS.txt
grep -Fq 'android.permission.READ_CALENDAR' out/evidence/APK_PERMISSIONS.txt
grep -Fq 'android.permission.WRITE_CALENDAR' out/evidence/APK_PERMISSIONS.txt
sha256sum out/DIRECTIVE_2_2.0.4_GITHUB_TEST.apk | tee out/evidence/SHA256SUMS.txt
printf '%s\n' 'build=PASS' 'static_verification=PASS' 'signing=EPHEMERAL_GITHUB_TEST_KEY' 'android16_runtime=UNEXECUTED' 'physical_acceptance=UNEXECUTED' 'final_go=false' > out/evidence/BUILD_STATUS.txt

echo 'PASS: DIRECTIVE 2 GitHub APK build and static verification'
