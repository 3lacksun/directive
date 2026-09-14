# DIRECTIVE Android 16 release identity gate — 14 September 2026 17:35 BST

## Scope

Non-destructive release-engineering hardening on `directive-approved-icon-recovery-14092026`.

The runtime-proven Phase 1 baseline remains protected. This change does not modify application source, DEX, Android resources, startup behaviour, Habit/Pomodoro behaviour, navigation, calendar/task-duration workflows, package contents, signing material, or approved-icon bytes.

## Finding

The release-candidate verifier already bound the exact APK SHA-256, package/version identity and signer evidence, but it did not bind the candidate's Android SDK identity. A correctly hashed and signed APK could therefore have passed the gate while declaring an unexpected `minSdkVersion`, `compileSdkVersion` or `targetSdkVersion`.

For DIRECTIVE release readiness this was too weak because Android 16/API 36 compatibility is a locked priority and must not be inferred from signer/package identity alone.

## Remediation

`support/verify_directive_release_candidate.py` now requires and verifies:

- `--expected-min-sdk` against the unique `sdkVersion` line in `aapt dump badging` evidence;
- `--expected-compile-sdk` against `compileSdkVersion` on the unique package identity line;
- `--expected-target-sdk` against the unique `targetSdkVersion` line;
- `compileSdkVersion=36` for a DIRECTIVE release candidate; and
- `targetSdkVersion=36` for a DIRECTIVE release candidate.

The verifier fails closed if SDK evidence is missing, duplicated, mismatched, or if a caller attempts to configure a non-API-36 compile/target identity.

This remains a package/static release gate. It does not claim that Android 16 device or emulator runtime behaviour has been executed.

## Deterministic local verification

Six cases were executed before publication:

1. matching synthetic candidate with minSdk 26, compileSdk 36 and targetSdk 36 — PASS;
2. candidate targetSdk changed to 35 — correctly rejected;
3. candidate compileSdk changed to 35 — correctly rejected;
4. candidate minSdk changed from expected 26 to 24 — correctly rejected;
5. caller attempts to configure expected targetSdk 35 — correctly rejected;
6. duplicate targetSdk evidence — correctly rejected.

Result: **6/6 deterministic Android SDK identity fixtures PASS**.

## Evidence classification

`ANDROID16_RELEASE_IDENTITY_GATE: PASS_LOCAL`

`ANDROID16_TARGET_SDK_LOCK: 36`

`ANDROID16_COMPILE_SDK_LOCK: 36`

`APPLICATION_SOURCE_MUTATED: NO`

`RUNTIME_BASELINE_CHANGED: NO`

`SIGNING_MATERIAL_CHANGED: NO`

`DEVICE_RUNTIME_RETESTED: NO`

No device-runtime PASS is claimed by this milestone.
