# DIRECTIVE continuity recovery — 14 September 2026

## Purpose

This branch is an isolated, non-destructive recovery line created after reconciliation found that the previously reported `directive-approved-icon-source-13092026` branch and its recorded commits were not present in the current authoritative GitHub repository.

## Protected runtime authority

The runtime-proven Phase 1 baseline remains protected. This recovery branch does not modify application source, DEX, startup behaviour, Habit/Pomodoro behaviour, navigation, calendar/task-duration behaviour, resources, signing material, or package identity.

Do not reintroduce rejected startup-time Habit/Pomodoro patches. Do not perform speculative resource pruning.

## Branch provenance

Recovery branch: `directive-approved-icon-recovery-14092026`

Base commit: `67ac7ec4631503ae47caeaf6cae41c5724b57ef4`

Base ref at recovery time: `main`

Repository: `3lacksun/directive`

## Reconciliation finding

The previously reported icon source branch was not available when continuity recovery began. The exact approved icon resource pack referenced by earlier work is also not currently discoverable from the expected persistent Library location, so approved icon binaries remain blocked rather than being reconstructed from assumptions.

Therefore earlier isolated icon work must not be claimed as persisted Git authority unless its exact bytes are recovered from an independent persistent source and cryptographically re-verified.

## Recovery rules

1. Preserve the Phase 1 runtime-proven APK/source as rollback authority.
2. Keep icon/release-engineering work isolated from runtime source until exact approved assets and provenance are recovered and verified.
3. Accept only exact recovered approved icon bytes; do not synthesize substitute artwork.
4. Verify hashes/object identity before any icon resource enters a commit.
5. Keep Android 16 compatibility verification non-destructive until source/runtime authority is reconciled.
6. Do not claim device-runtime PASS without actual device/emulator evidence for the exact candidate.
7. Preserve signer continuity; do not replace signing identity silently.

## Recovery-scope guard

`support/verify_directive_recovery_scope.py` provides a fail-closed Git diff gate for this recovery branch.

The guard rejects modifications to the protected sealed source, sealed patch, remediation source, build input, and inherited Android/runtime/convergence workflows. Its allowlist is limited to recovery support/documentation, a dedicated approved-icon workflow namespace, and the exact launcher/adaptive-icon resource path shapes needed for later verified icon restoration.

Deterministic fixture verification:

- allowed `support/`-only change: PASS
- protected `sealed-source/` mutation: correctly rejected

No application/runtime resource or source path is permitted to change silently on this recovery branch.

## Phase 1 signer/package continuity

Persistent Phase 1 evidence was reconciled against `DIRECTIVE_LEGACY_MONETISATION_REMOVAL_PHASE1_REPORT_12092026175450.json`.

Locked identities:

- predecessor Android 16 receiver-fixed test candidate: `DIRECTIVE_EXEC002_ANDROID16_RECEIVER_FIXED_TESTSIGNED_11092026174220.apk`
- predecessor SHA-256: `58bf319f1ddf0920680cea5a3cbab572a6406e01734a6a24cfb174b66ef2cf75`
- runtime-proven Phase 1 candidate: `DIRECTIVE_LEGACY_MONETISATION_REMOVED_PHASE1_TESTSIGNED_12092026175450.apk`
- Phase 1 SHA-256: `d30a725ccecefa01cf480e3ad3a266f61b298357affd5628a5b7934478170c85`
- disposable EXEC002 Phase 1 test certificate SHA-256: `420a3ce0c50cd0c77aa5633fecbbcb4436145e871f26bc9feae9d6cb15bef81c`

`support/verify_directive_phase1_signer.py` now fails closed if the persisted Phase 1 report changes any locked package/hash/signature identity, loses v2 verification, loses patch/ZIP verification, or incorrectly claims device runtime execution. It can additionally hash-check the exact APK when those bytes are supplied and can verify that an explicitly supplied authorised release certificate is distinct from the disposable Phase 1 test certificate.

Executed local verification against the persisted authoritative Phase 1 report:

- exact report continuity: PASS
- exact Phase 1 test certificate continuity: PASS
- deliberately corrupted certificate fixture: correctly rejected
- device runtime evidence remains `UNEXECUTED` in the report and is not upgraded by this check

The Phase 1 report explicitly states that the disposable test certificate differs from the DIRECTIVE stable signing identity. The exact authorised stable/release certificate fingerprint has not yet been independently recovered in this recovery run, so production signer continuity remains OPEN rather than inferred.

## Current status

`RECOVERY_BRANCH_CREATED: PASS`

`RECOVERY_SCOPE_GUARD_IMPLEMENTED: PASS`

`RECOVERY_SCOPE_GUARD_LOCAL_FIXTURE: PASS`

`PHASE1_REPORT_CONTINUITY_VERIFIER_IMPLEMENTED: PASS`

`PHASE1_REPORT_CONTINUITY_LOCAL_VERIFY: PASS`

`PHASE1_SIGNER_NEGATIVE_FIXTURE: PASS`

`PHASE1_TEST_CERT_SHA256: 420a3ce0c50cd0c77aa5633fecbbcb4436145e871f26bc9feae9d6cb15bef81c`

`AUTHORISED_STABLE_SIGNER_FINGERPRINT_RECOVERED: NO`

`PROTECTED_BASE_DIFF_APPLICATION_PATHS: 0`

`APPLICATION_SOURCE_MUTATED: NO`

`RUNTIME_BASELINE_CHANGED: NO`

`DEVICE_RUNTIME_RETESTED: NO`

`PRIOR_ICON_BRANCH_RECOVERED: NO`

`APPROVED_ICON_BINARY_PACK_RECOVERED: NO`

## Next safe locally executable step

Continue non-destructive release-readiness reconciliation: recover the exact authorised stable/release signer fingerprint and Android 16/package invariants from persisted authoritative evidence, then encode those as fail-closed verification gates. Restore approved icon resources only if their exact bytes and locked provenance are recovered; otherwise keep that subtask blocked.
