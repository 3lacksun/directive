# DIRECTIVE recovery-base ancestry gate — 14 September 2026 22:25 BST

## Scope

Non-destructive recovery/release-engineering hardening on `directive-approved-icon-recovery-14092026`.

The runtime-proven Phase 1 baseline remains the rollback authority. No application source, DEX, Android resource, startup behaviour, Habit/Pomodoro behaviour, navigation, calendar/task-duration workflow, package identity, signing material or approved icon binary is changed by this remediation.

## Finding

`support/verify_directive_recovery_scope.py` previously accepted an arbitrary caller-supplied `--base` ref and then evaluated the recovery diff relative to that ref.

The allowlist still protected obvious runtime paths, but a mistaken or deliberately substituted base could weaken the provenance guarantee because the verifier did not independently prove that the comparison was anchored to the exact protected Phase 1 recovery base.

## Remediation

The recovery-scope verifier now locks the protected base to:

`67ac7ec4631503ae47caeaf6cae41c5724b57ef4`

Before evaluating changed paths it now requires all of the following:

1. any supplied `--base` value exactly equals the locked base SHA;
2. the locked SHA resolves to that exact commit object;
3. the locked base is an ancestor of `HEAD`;
4. `git merge-base <locked-base> HEAD` equals the locked base exactly; and
5. the recovery diff is always calculated from the locked base rather than from an arbitrary caller-controlled ref.

The existing protected-path and recovery allowlist checks remain in place.

## Deterministic local regression verification

Four isolated Git fixtures were executed before publication:

1. locked base + allowed `support/` change — PASS;
2. caller attempts `--base HEAD` instead of the locked SHA — correctly rejected;
3. locked-base descendant containing a `sealed-source/` mutation — correctly rejected;
4. unrelated/orphan branch where the locked base is not an ancestor — correctly rejected.

Result: **4/4 deterministic recovery-base fixtures PASS**.

## Approved visual reference reconciliation

A fresh GPT Library search for `DIRECTIVE_APPROVED_BRAND_UI_REFERENCE_01092026140811.png`, approved launcher/adaptive icon material and the earlier icon-source branch artefacts did not recover the exact approved binary/reference. The historical DIRECTIVE audit likewise records that the named PNG was not discoverable and classified visual-fidelity proof as UNVERIFIABLE.

No substitute artwork has been generated or accepted.

## Evidence classification

`RECOVERY_BASE_SHA_LOCKED: PASS`

`RECOVERY_BASE_ANCESTRY_GATE: PASS_LOCAL`

`WRONG_BASE_NEGATIVE_FIXTURE: PASS`

`PROTECTED_PATH_NEGATIVE_FIXTURE: PASS`

`UNRELATED_HISTORY_NEGATIVE_FIXTURE: PASS`

`APPROVED_ICON_REFERENCE_RECOVERED: NO`

`APPLICATION_SOURCE_MUTATED: NO`

`RUNTIME_BASELINE_CHANGED: NO`

`DEVICE_RUNTIME_RETESTED: NO`
