#!/usr/bin/env bash
set -euo pipefail

BASE=support/directive8_startup_runtime_fix_build.sh
CRASH_PATCHER=support/patch_directive_startup_crash_capture.py
D11_PATCHER=support/patch_directive11_startup_surface_and_runtime_capture.py
GEN=/tmp/directive11_generated_build.sh

for f in "$BASE" "$CRASH_PATCHER" "$D11_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text(encoding='utf-8')
for old,new in (
 ('com.directive.v8','com.directive.v11'),
 ('DIRECTIVE_8','DIRECTIVE_11'),
 ('DIRECTIVE 8','DIRECTIVE 11'),
 ('8.0.0','11.0.0'),
 ('8800','9100'),
 ('directive8-test.jks','directive11-test.jks'),
 ('directive8test','directive11test'),
 ('DIRECTIVE8_','DIRECTIVE11_'),
):
    src=src.replace(old,new)
anchor='cp "$PROJECT_ROOT/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json" out-v8/evidence/\n'
if src.count(anchor)!=1:
    raise SystemExit(f'D11 source-remediation insertion anchor count={src.count(anchor)}')
addition=anchor+'''python3 support/patch_directive_startup_crash_capture.py "$PROJECT_ROOT" 11 | tee out-v8/evidence/STARTUP_CRASH_CAPTURE.txt
cp "$PROJECT_ROOT/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json" out-v8/evidence/
python3 support/patch_directive11_startup_surface_and_runtime_capture.py "$PROJECT_ROOT" | tee out-v8/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE.txt
cp "$PROJECT_ROOT/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json" out-v8/evidence/
'''
src=src.replace(anchor,addition,1)
src=src.replace("'physical_samsung_android16_acceptance=UNEXECUTED'", "'physical_samsung_android16_acceptance=UNEXECUTED_D11;D8=FAIL'")
old_echo="echo 'PASS: DIRECTIVE 11 startup-process-exit remediated APK built and statically verified'"
new_echo="""grep -Fq '\"startup_throwable_rethrown\": true' out-v8/evidence/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json
grep -Fq '\"authentication_licensing_entitlement_logic_changed\": false' out-v8/evidence/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json
grep -Fq '\"inherited_ticktick_window_background_removed_from_launcher_styles\": true' out-v8/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json
grep -Fq '\"directive_launch_background_wired\": true' out-v8/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json
grep -Fq '\"system_only_filter_verified\": true' out-v8/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json
grep -Fq '\"d10_receiver_flag_hypothesis_carried_forward\": false' out-v8/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json
grep -Fq '\"activity_thread_abort_capture_added\": true' out-v8/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json
grep -Fq '\"global_uncaught_capture_added\": true' out-v8/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json
grep -Fq '\"authentication_licensing_premium_entitlement_logic_changed\": false' out-v8/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json
echo 'PASS: DIRECTIVE 11 startup surface corrected and fatal runtime capture extended; FINAL_GO=false'"""
if old_echo not in src:
    raise SystemExit('D11 terminal build message anchor missing')
src=src.replace(old_echo,new_echo,1)
Path(sys.argv[2]).write_text(src,encoding='utf-8')
PY
chmod +x "$GEN"
bash "$GEN"

rm -rf out-v11
mv out-v8 out-v11
APK=out-v11/DIRECTIVE_11_11.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"

# Final identity and package gates.
grep -Fq "package: name='com.directive.v11' versionCode='9100' versionName='11.0.0'" out-v11/evidence/APK_BADGING.txt
grep -Fq "application-label:'DIRECTIVE 11'" out-v11/evidence/APK_BADGING.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v11/evidence/APK_PERMISSIONS.txt
grep -Fq '16K_ALIGNMENT=PASS' out-v11/evidence/ELF_16K_ALIGNMENT.txt

# Inherited binary namespaces and app-owned package identities remain under the existing D8 gates.
grep -Fq '"critical_variant_discriminator_fixed": true' out-v11/evidence/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"launcher_manager_dynamic_package_contract_verified": true' out-v11/evidence/DIRECTIVE_LAUNCHER_ALIAS_NAMESPACE_REPORT.json
grep -Fq '"provider_runtime_authority_contract_verified": true' out-v11/evidence/DIRECTIVE_PROVIDER_AUTHORITY_NAMESPACE_REPORT.json
grep -Fq '"inherited_provider_class_namespace_preserved": true' out-v11/evidence/DIRECTIVE_PROVIDER_AUTHORITY_NAMESPACE_REPORT.json
grep -Fq '"pro_entitlement_guard_preserved": true' out-v11/evidence/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json

# Verify D11 crash-recorder markers survived assembly. The recorder rethrows/delegates; it is not a crash bypass.
for dex in classes.dex classes2.dex classes3.dex classes4.dex classes5.dex classes6.dex; do
  unzip -p "$APK" "$dex" 2>/dev/null || true
done | strings > out-v11/evidence/APK_D11_DEX_STRINGS.txt
grep -Fq 'DIRECTIVE_STARTUP_CRASH' out-v11/evidence/APK_D11_DEX_STRINGS.txt
grep -Fq 'DIRECTIVE_11_CRASH_' out-v11/evidence/APK_D11_DEX_STRINGS.txt

# Verify the DIRECTIVE launch assets are packaged and the old TickTick launch background is no longer
# referenced by the specific launcher styles in the source tree used for this APK.
PROJECT_ROOT="$(sed -n 's/^PROJECT_ROOT=//p' out-v11/evidence/PROJECT_ROOT.txt)"
test -n "$PROJECT_ROOT"
grep -Fq '@drawable/directive_launch_background' "$PROJECT_ROOT/res/values/styles.xml"
grep -Fq '@drawable/directive_launch_background' "$PROJECT_ROOT/res/values-night/styles.xml"
python3 - "$PROJECT_ROOT" > out-v11/evidence/STARTUP_STYLE_FINAL_GATE.txt <<'PY'
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
checks={
 root/'res/values/styles.xml': {'AppTheme.Launcher','AppTheme.Launcher.Compat'},
 root/'res/values-night/styles.xml': {'AppTheme.Launcher'},
}
rx=re.compile(r'<style\b[^>]*\bname="(?P<name>[^"]+)"[^>]*>(?P<body>.*?)</style>',re.S)
for p,wanted in checks.items():
 s=p.read_text(encoding='utf-8')
 blocks={m.group('name'):m.group('body') for m in rx.finditer(s) if m.group('name') in wanted}
 if set(blocks)!=wanted: raise SystemExit(f'missing styles in {p}: {wanted-set(blocks)}')
 for name,body in blocks.items():
  if '@drawable/directive_launch_background' not in body: raise SystemExit(f'{p}:{name} missing DIRECTIVE background')
  if '@drawable/ticktick_launcher_bg' in body: raise SystemExit(f'{p}:{name} still references TickTick launcher')
  print('PASS',p.relative_to(root),name)
print('STARTUP_STYLE_FINAL_GATE=PASS')
PY
grep -Fq 'STARTUP_STYLE_FINAL_GATE=PASS' out-v11/evidence/STARTUP_STYLE_FINAL_GATE.txt

# Confirm the D10 receiver hypothesis is intentionally not present: the exact system-only filter uses
# its original two-argument Context.registerReceiver path.
grep -Fq '"system_only_filter_verified": true' out-v11/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json
grep -Fq '"original_system_broadcast_registration_preserved": true' out-v11/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json

printf '%s\n' \
  'candidate=DIRECTIVE 11' \
  'package=com.directive.v11' \
  'version=11.0.0/9100' \
  'startup_surface=DIRECTIVE_BACKGROUND_WIRED' \
  'd10_receiver_hypothesis=RETIRED_SYSTEM_BROADCAST_EXEMPTION' \
  'application_oncreate_crash_capture=PRESERVED_RETHROW' \
  'activity_thread_abort_crash_capture=ADDED_BEFORE_EXISTING_KILL' \
  'global_uncaught_crash_capture=ADDED_BEFORE_EXISTING_DELEGATION_OR_KILL' \
  'inherited_java_jni_namespace=PRESERVED' \
  'offline_no_network_permission_boundary=PRESERVED' \
  'authentication_licensing_premium_entitlement_logic=UNCHANGED' \
  'physical_d8_samsung_android16=FAIL' \
  'd10_physical_android16_runtime=UNEXECUTED' \
  'd11_physical_android16_runtime=UNEXECUTED' \
  'final_go=false' > out-v11/evidence/DIRECTIVE11_RUNTIME_DISPOSITION.txt

sha256sum "$APK" | tee out-v11/evidence/DIRECTIVE11_SHA256_FINAL.txt
echo 'PASS: DIRECTIVE 11 built and statically verified; runtime remains UNEXECUTED and FINAL_GO=false'
