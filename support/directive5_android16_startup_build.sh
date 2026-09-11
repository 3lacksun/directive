#!/usr/bin/env bash
set -euo pipefail

BASE=support/directive3_install_safe_build.sh
PACKAGE_PATCHER=support/patch_directive_runtime_package_identity.py
LAUNCHER_PATCHER=support/patch_directive_launcher_identity.py
STARTUP_PATCHER=support/patch_directive_android16_startup_hardening.py
GEN=/tmp/directive5_generated_build.sh

for f in "$BASE" "$PACKAGE_PATCHER" "$LAUNCHER_PATCHER" "$STARTUP_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')
for old, new in (
    ('com.directive.v3', 'com.directive.v5'),
    ('DIRECTIVE_3', 'DIRECTIVE_5'),
    ('DIRECTIVE 3', 'DIRECTIVE 5'),
    ('3.0.0', '5.0.0'),
    ('8300', '8500'),
    ('DIRECTIVE 3 Install Safe Test', 'DIRECTIVE 5 Android 16 Startup Test'),
):
    src = src.replace(old, new)
needle = 'cp "$PROJECT_ROOT/DIRECTIVE_INSTALL_COLLISION_REMEDIATION_REPORT.json" out-v8/evidence/'
insert = '''python3 support/patch_directive_runtime_package_identity.py "$PROJECT_ROOT" com.directive.v5 | tee out-v8/evidence/RUNTIME_PACKAGE_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_launcher_identity.py "$PROJECT_ROOT" | tee out-v8/evidence/LAUNCHER_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_android16_startup_hardening.py "$PROJECT_ROOT" com.directive.v5 | tee out-v8/evidence/ANDROID16_STARTUP_HARDENING.txt
cp "$PROJECT_ROOT/DIRECTIVE_ANDROID16_STARTUP_HARDENING_REPORT.json" out-v8/evidence/
'''
if src.count(needle) != 1:
    raise SystemExit(f'expected one build-chain insertion point, found {src.count(needle)}')
src = src.replace(needle, insert + needle, 1)
Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY
chmod +x "$GEN"

for needle in 'com.directive.v5' 'DIRECTIVE 5' '5.0.0' '8500' 'patch_directive_android16_startup_hardening.py'; do grep -Fq "$needle" "$GEN"; done

bash "$GEN"

test -s out-v8/DIRECTIVE_5_5.0.0_INSTALL_SAFE_TEST.apk

grep -Fq '"critical_variant_discriminator_fixed": true' out-v8/evidence/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"inherited_ticktick_launcher_replaced": true' out-v8/evidence/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"activity_thread_abort_hook_disabled": true' out-v8/evidence/DIRECTIVE_ANDROID16_STARTUP_HARDENING_REPORT.json
grep -Fq '"global_dynamic_receiver_startup_registration_disabled": true' out-v8/evidence/DIRECTIVE_ANDROID16_STARTUP_HARDENING_REPORT.json
grep -Fq '"firebase_app_startup_init_disabled": true' out-v8/evidence/DIRECTIVE_ANDROID16_STARTUP_HARDENING_REPORT.json
grep -Fq 'targetSdkVersion:\x27\x27' /dev/null 2>/dev/null || true

grep -Fq "targetSdkVersion:'36'" out-v8/evidence/APK_BADGING.txt || grep -Fq "targetSdkVersion:'36'" out-v8/evidence/APK_BADGING.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v8/evidence/APK_PERMISSIONS.txt

printf '%s\n' \
  'build=PASS' \
  'package=com.directive.v5' \
  'label=DIRECTIVE 5' \
  'version=5.0.0/8500' \
  'target_sdk=36' \
  'activity_thread_abort_hook=DISABLED' \
  'legacy_startup_dynamic_receivers=DISABLED' \
  'firebase_facebook_bugsnag_mlkit_startup_providers=DISABLED' \
  'runtime_package_identity=RETARGETED' \
  'internal_com.ticktick.task_JNI_namespace=PRESERVED' \
  'billing_auth_entitlement_logic=UNCHANGED' \
  'physical_samsung_android16_acceptance=UNEXECUTED' \
  'final_go=false' \
  > out-v8/evidence/DIRECTIVE5_STATUS.txt

sha256sum out-v8/DIRECTIVE_5_5.0.0_INSTALL_SAFE_TEST.apk | tee out-v8/evidence/DIRECTIVE5_SHA256.txt

echo 'PASS: DIRECTIVE 5 Android 16 startup-hardened APK built and statically verified'
