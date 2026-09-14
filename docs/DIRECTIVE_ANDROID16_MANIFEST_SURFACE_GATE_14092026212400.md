# DIRECTIVE Android 16 manifest surface gate — 14 September 2026 21:24 BST

## Scope

Non-destructive release-engineering hardening on `directive-approved-icon-recovery-14092026`.

The runtime-proven Phase 1 baseline remains protected. No application source, DEX, Android resource, startup behaviour, Habit/Pomodoro behaviour, navigation, calendar/task-duration workflow, package identity, signing material, or approved-icon byte is changed by this work.

## Gap closed

The existing manifest/badging gate verifies release flags, launcher identity and target SDK, but did not independently constrain the broader Android manifest attack surface. A candidate could therefore require additional review if a build introduced a new exported component, an intent-filter component without explicit `android:exported`, or a high-risk permission.

## Implementation

Added `support/verify_directive_android16_surface.py`.

The verifier consumes decoded merged APK manifest XML plus an independently maintained exact exported-component allowlist. It fails closed when:

- a high-risk permission is present, including package installation, all-files access, overlay/settings mutation, broad package visibility, usage-stat access, accessibility binding, SMS, phone or call-log permissions;
- `android:debuggable=true` or `android:testOnly=true` is present;
- a manifest component lacks `android:name`;
- a component with an intent filter lacks explicit `android:exported`;
- an exported activity, alias, service, receiver or provider is not in the authorised allowlist; or
- an authorised exported component disappears from the candidate.

The allowlist is supplied at verification time rather than invented in this branch, preserving the requirement to reconcile exact production component identity from authoritative candidate evidence.

## Deterministic local verification

Seven fixtures were executed before publication:

1. expected launcher exported, private receiver non-exported — PASS;
2. unexpected exported receiver — correctly rejected;
3. `REQUEST_INSTALL_PACKAGES` introduced — correctly rejected;
4. intent-filter launcher missing explicit `android:exported` — correctly rejected;
5. `android:debuggable=true` — correctly rejected;
6. authorised exported component missing from candidate — correctly rejected;
7. malformed exported-component allowlist — correctly rejected.

Result: **7/7 deterministic Android 16 manifest-surface fixtures PASS**.

## Evidence classification

`ANDROID16_MANIFEST_SURFACE_GATE: PASS_LOCAL`

`APPLICATION_SOURCE_MUTATED: NO`

`RUNTIME_BASELINE_CHANGED: NO`

`ANDROID_RESOURCES_CHANGED: NO`

`SIGNING_MATERIAL_CHANGED: NO`

`DEVICE_RUNTIME_RETESTED: NO`

`PRODUCTION_EXPORTED_COMPONENT_ALLOWLIST_RECONCILED: NO`

The new gate is ready to consume the exact decoded manifest and authorised exported-component list from a future stable release candidate. It does not infer or assert those production identities itself.
