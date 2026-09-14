# DIRECTIVE release manifest gate — 14 September 2026 17:45 BST

## Scope

Non-destructive release-engineering hardening on `directive-approved-icon-recovery-14092026`.

The protected Phase 1 runtime baseline is unchanged. No application source, DEX, Android resource, startup behaviour, Habit/Pomodoro behaviour, navigation, calendar/task-duration workflow, package bytes, signing material, or approved-icon byte was modified.

## Finding

The existing release-candidate identity gate bound APK hash, package/version, SDK and signer evidence, but release manifest/badging safety still lacked an independent fail-closed check for three conditions that can make a nominal release unsuitable:

1. an APK accidentally marked `application-debuggable`;
2. an APK accidentally marked `application-testOnly`; and
3. missing, duplicated or unexpected launchable activity identity.

## Remediation

Added `support/verify_directive_release_manifest_gate.py`.

The verifier consumes captured `aapt dump badging` evidence and requires:

- exactly one package identity line matching the independently supplied expected package;
- exactly one launchable activity matching the independently supplied expected launchable activity;
- targetSdk exactly 36;
- no `application-debuggable` marker; and
- no `application-testOnly` marker.

It does not infer the production package namespace or launch activity. Those values must be supplied from separately reconciled authoritative release identity evidence.

## Deterministic local verification

Six fixture cases were executed before publication:

1. valid release badging — PASS;
2. debuggable release candidate — correctly rejected;
3. testOnly release candidate — correctly rejected;
4. missing launchable activity — correctly rejected;
5. multiple launchable activities — correctly rejected;
6. wrong launchable activity — correctly rejected.

Result: **6/6 deterministic manifest-gate fixtures PASS**.

## Evidence classification

`RELEASE_MANIFEST_GATE_IMPLEMENTED: PASS_LOCAL`

`RELEASE_MANIFEST_GATE_FIXTURES: 6/6 PASS`

`ANDROID16_TARGETSDK_GUARD: PASS_LOCAL`

`APPLICATION_SOURCE_MUTATED: NO`

`RUNTIME_BASELINE_CHANGED: NO`

`SIGNING_MATERIAL_CHANGED: NO`

`DEVICE_RUNTIME_RETESTED: NO`

The exact authorised production package/launcher identity must still be reconciled before this gate can be used as final release acceptance evidence for a real candidate.
