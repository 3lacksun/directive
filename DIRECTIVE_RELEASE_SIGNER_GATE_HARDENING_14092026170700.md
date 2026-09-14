# DIRECTIVE release signer gate hardening — 14 September 2026 17:07 BST

## Scope

Non-destructive release-engineering hardening on `directive-approved-icon-recovery-14092026`.

Protected runtime authority remains the user-confirmed Phase 1 baseline. No application source, DEX, Android resource, startup behaviour, Habit/Pomodoro behaviour, navigation, calendar/task-duration workflow, package identity, signing material, or approved-icon byte is changed by this work.

## Finding

The first production signer gate required a matching certificate SHA-256 and a textual `Verifies` marker, but it did not independently require:

- the standalone successful `Verifies` line emitted by `apksigner`;
- an explicit `Number of signers: 1` result; or
- successful APK Signature Scheme v2-or-newer verification.

That left unnecessary ambiguity in malformed or synthetic evidence handling.

## Remediation

`support/verify_directive_release_signer_gate.py` now additionally requires:

1. a standalone successful `Verifies` marker;
2. exactly one reported signer;
3. at least one successful APK Signature Scheme v2-or-newer result;
4. exactly one unique valid certificate SHA-256;
5. exact equality with the independently supplied authorised release certificate SHA-256; and
6. explicit rejection of the disposable Phase 1 test certificate `420a3ce0c50cd0c77aa5633fecbbcb4436145e871f26bc9feae9d6cb15bef81c` as either expected production identity or actual candidate signer.

The verifier still stores no production private key, certificate, keystore or secret.

## Deterministic local verification

Eight fixture cases were executed against the hardened verifier before publication:

1. matching synthetic stable signer with v2 verification — PASS;
2. v1-only candidate — correctly rejected;
3. two reported signers using the same certificate — correctly rejected;
4. embedded/non-standalone `Verifies` text — correctly rejected;
5. missing `Number of signers` evidence — correctly rejected;
6. mismatched stable signer — correctly rejected;
7. disposable Phase 1 test certificate as candidate signer — correctly rejected;
8. disposable Phase 1 test certificate configured as expected production signer — correctly rejected.

Result: **8/8 deterministic signer-gate fixtures PASS**.

## Evidence classification

`SIGNER_GATE_HARDENING: PASS_LOCAL`

`APPLICATION_SOURCE_MUTATED: NO`

`RUNTIME_BASELINE_CHANGED: NO`

`SIGNING_MATERIAL_CHANGED: NO`

`AUTHORISED_STABLE_SIGNER_FINGERPRINT_RECOVERED: NO`

`REAL_STABLE_SIGNED_CANDIDATE_VERIFIED: NO`

`DEVICE_RUNTIME_RETESTED: NO`

The exact authorised stable signer fingerprint remains an open evidence dependency; no fingerprint has been inferred from the disposable Phase 1 package or unrelated application evidence.
