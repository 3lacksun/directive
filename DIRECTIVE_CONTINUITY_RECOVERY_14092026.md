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

The GitHub branch inventory did not contain `directive-approved-icon-source-13092026` or any other branch matching `icon`. The previously reported icon/release-engineering support scripts were also not discoverable in the repository default-branch code search.

Therefore the earlier isolated icon work must not be claimed as persisted Git authority unless its exact bytes are recovered from an independent persistent source and cryptographically re-verified.

## Recovery rules

1. Preserve the Phase 1 runtime-proven APK/source as rollback authority.
2. Keep icon/release-engineering work isolated from runtime source until exact approved assets and provenance are recovered and verified.
3. Accept only exact recovered approved icon bytes; do not synthesize substitute artwork.
4. Verify hashes/object identity before any icon resource enters a commit.
5. Keep Android 16 compatibility verification non-destructive until source/runtime authority is reconciled.
6. Do not claim device-runtime PASS without actual device/emulator evidence for the exact candidate.
7. Preserve signer continuity; do not replace signing identity silently.

## Current status

`RECOVERY_BRANCH_CREATED: PASS`

`APPLICATION_SOURCE_MUTATED: NO`

`RUNTIME_BASELINE_CHANGED: NO`

`DEVICE_RUNTIME_RETESTED: NO`

`PRIOR_ICON_BRANCH_RECOVERED: NO`

## Next safe locally executable step

Recover the exact approved icon resource pack and any surviving release-engineering scripts/evidence from persistent project storage, verify their hashes independently, then reintroduce them only on this isolated recovery branch. If exact bytes cannot be recovered, keep the icon change blocked rather than reconstructing it from assumptions.
