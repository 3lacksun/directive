# DIRECTIVE release-candidate identity gate — 14 September 2026 17:20 BST

## Scope

Non-destructive release-engineering work on `directive-approved-icon-recovery-14092026`.

The protected runtime-proven Phase 1 baseline remains unchanged. This change does not modify application source, DEX, Android resources, startup behaviour, Habit/Pomodoro behaviour, navigation, calendar/task-duration workflows, package identity, signing material, or approved icon bytes.

## Improvement

Added `support/verify_directive_release_candidate.py` to bind all release-critical APK identity evidence into one fail-closed check.

The verifier requires the exact candidate APK plus independently supplied expected values for:

- APK SHA-256;
- package/application ID;
- versionCode;
- versionName;
- authorised release certificate SHA-256;
- captured `aapt dump badging` evidence; and
- captured `apksigner verify --verbose --print-certs` evidence.

Acceptance requires:

1. candidate bytes hash exactly to the expected APK SHA-256;
2. badging contains exactly one package identity line;
3. package, versionCode and versionName exactly match the supplied expected release identity;
4. `apksigner` reports a standalone `Verifies` result;
5. exactly one signer is reported;
6. APK Signature Scheme v2 or newer verifies successfully;
7. exactly one unique valid certificate SHA-256 is present; and
8. that certificate exactly matches the independently supplied authorised release fingerprint.

This gate deliberately does not hard-code a production package namespace or stable certificate fingerprint while those values are not independently established by current authority.

## Deterministic local verification

Nine fixture cases were executed before publication:

1. fully matching synthetic candidate — PASS;
2. APK SHA-256 mismatch — correctly rejected;
3. package mismatch — correctly rejected;
4. versionCode mismatch — correctly rejected;
5. versionName mismatch — correctly rejected;
6. signer-certificate mismatch — correctly rejected;
7. v1-only signature evidence — correctly rejected;
8. two reported signers — correctly rejected;
9. duplicate package identity lines — correctly rejected.

Result: **9/9 deterministic candidate-identity fixtures PASS**.

## Evidence classification

`RELEASE_CANDIDATE_IDENTITY_GATE_IMPLEMENTED: PASS`

`RELEASE_CANDIDATE_IDENTITY_GATE_FIXTURES: 9/9 PASS`

`APPLICATION_SOURCE_MUTATED: NO`

`RUNTIME_BASELINE_CHANGED: NO`

`SIGNING_MATERIAL_CHANGED: NO`

`PRODUCTION_PACKAGE_ID_ASSERTED: NO`

`AUTHORISED_STABLE_SIGNER_FINGERPRINT_RECOVERED: NO`

`REAL_RELEASE_CANDIDATE_VERIFIED: NO`

`DEVICE_RUNTIME_RETESTED: NO`

The gate is ready to consume exact production identity values and real APK evidence once those are independently recovered/authorised.
