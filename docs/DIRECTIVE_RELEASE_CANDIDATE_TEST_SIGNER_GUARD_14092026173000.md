# DIRECTIVE release-candidate test-signer guard — 14 September 2026 17:30 BST

## Scope

Non-destructive release-engineering correction on `directive-approved-icon-recovery-14092026`.

The protected runtime-proven Phase 1 baseline remains unchanged. No application source, DEX, Android resource, startup behaviour, Habit/Pomodoro behaviour, navigation, calendar/task-duration workflow, package identity, approved icon byte or signing material is modified by this change.

## Defect found

`support/verify_directive_release_candidate.py` validated candidate APK hash, package/version identity, APK Signature Scheme v2-or-newer evidence, single-signer evidence and an expected signer certificate. However, unlike the dedicated signer verifier, it did not independently prohibit the known disposable Phase 1 EXEC002 test certificate.

That created an avoidable acceptance gap: a caller could supply the disposable certificate as the expected release identity and have the all-in-one candidate gate treat it as an ordinary expected signer.

## Remediation

The release-candidate gate now embeds the locked disposable certificate SHA-256:

`420a3ce0c50cd0c77aa5633fecbbcb4436145e871f26bc9feae9d6cb15bef81c`

It fails closed in both directions:

1. the expected production/release certificate may not equal the disposable Phase 1 certificate; and
2. the actual candidate signer extracted from `apksigner --print-certs` evidence may not equal the disposable Phase 1 certificate.

This duplicates the critical production/test boundary inside the all-in-one release-candidate gate so its safety does not depend on callers also running a separate verifier.

## Local deterministic verification

Three targeted fixture cases were executed before publication:

1. synthetic stable signer with matching candidate identity — PASS;
2. disposable Phase 1 certificate configured as the expected production identity — correctly rejected;
3. candidate signed by the disposable Phase 1 certificate while another production identity is expected — correctly rejected.

Result: **3/3 targeted regression fixtures PASS**.

## Classification

`RELEASE_CANDIDATE_TEST_SIGNER_GUARD: PASS_LOCAL`

`APPLICATION_SOURCE_MUTATED: NO`

`RUNTIME_BASELINE_CHANGED: NO`

`SIGNING_MATERIAL_CHANGED: NO`

`DEVICE_RUNTIME_RETESTED: NO`

`AUTHORISED_STABLE_SIGNER_FINGERPRINT_RECOVERED: NO`

This verification does not establish the production signer identity and does not claim device-runtime PASS.