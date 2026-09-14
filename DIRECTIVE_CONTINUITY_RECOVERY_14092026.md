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

`support/verify_directive_recovery_scope.py` now provides a fail-closed Git diff gate for this recovery branch.

The guard rejects modifications to the protected sealed source, sealed patch, remediation source, build input, and inherited Android/runtime/convergence workflows. Its allowlist is limited to recovery support/documentation, a dedicated approved-icon workflow namespace, and the exact launcher/adaptive-icon resource path shapes needed for later verified icon restoration.

Local deterministic fixture verification was executed before publication:

- allowed `support/`-only change: PASS
- protected `sealed-source/` mutation: correctly rejected

GitHub comparison against the protected base commit after publication reports the recovery branch as two commits ahead, zero behind, with exactly two changed paths:

- `DIRECTIVE_CONTINUITY_RECOVERY_14092026.md`
- `support/verify_directive_recovery_scope.py`

No application/runtime resource or source path differs from the protected base at this checkpoint.

## Current status

`RECOVERY_BRANCH_CREATED: PASS`

`RECOVERY_SCOPE_GUARD_IMPLEMENTED: PASS`

`RECOVERY_SCOPE_GUARD_LOCAL_FIXTURE: PASS`

`PROTECTED_BASE_DIFF_APPLICATION_PATHS: 0`

`APPLICATION_SOURCE_MUTATED: NO`

`RUNTIME_BASELINE_CHANGED: NO`

`DEVICE_RUNTIME_RETESTED: NO`

`PRIOR_ICON_BRANCH_RECOVERED: NO`

`APPROVED_ICON_BINARY_PACK_RECOVERED: NO`

## Next safe locally executable step

Continue release-readiness work that does not require missing icon binaries: establish signer-continuity verification and Android 16/package invariants from persisted authoritative evidence. Restore approved icon resources only if their exact bytes and locked provenance are recovered; otherwise keep that subtask blocked.
