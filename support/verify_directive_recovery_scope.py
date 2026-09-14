#!/usr/bin/env python3
import argparse
import subprocess
import sys

PROTECTED_PREFIXES = (
    "sealed-source/",
    "sealed-patch/",
    "directive-remediation/",
)

PROTECTED_EXACT = {
    "BUILD_INPUT.json",
    ".github/workflows/android-build.yml",
    ".github/workflows/android-layout-acceptance.yml",
    ".github/workflows/android-reboot-receiver-diagnostic-v5.yml",
    ".github/workflows/android-reboot-state-diagnostic-v4.yml",
    ".github/workflows/android-release-compile.yml",
    ".github/workflows/android-runtime-acceptance.yml",
    ".github/workflows/final-exec002-convergence-v2.yml",
    ".github/workflows/final-exec002-convergence-v3.yml",
    ".github/workflows/final-exec002-convergence-v6.yml",
    ".github/workflows/final-exec002-convergence.yml",
    ".github/workflows/final-exec002-reboot-proof-v7.yml",
    ".github/workflows/final-exec002-reboot-proof-v8.yml",
}

ALLOWED_PREFIXES = ("support/", "docs/")
ALLOWED_EXACT = {"DIRECTIVE_CONTINUITY_RECOVERY_14092026.md"}
ALLOWED_WORKFLOW_PREFIX = ".github/workflows/directive-approved-icon-"
ALLOWED_ICON_SUFFIXES = (
    "/res/mipmap-mdpi/ic_launcher.png",
    "/res/mipmap-hdpi/ic_launcher.png",
    "/res/mipmap-xhdpi/ic_launcher.png",
    "/res/mipmap-xxhdpi/ic_launcher.png",
    "/res/mipmap-xxxhdpi/ic_launcher.png",
    "/res/drawable/ic_launcher_foreground.png",
    "/res/drawable-v33/ic_launcher_monochrome.png",
    "/res/mipmap-anydpi-v26/ic_launcher.xml",
    "/res/mipmap-anydpi-v26/ic_launcher_round.xml",
    "/res/values/directive_icon_colors.xml",
)


def changed_paths(base: str) -> list[str]:
    output = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        text=True,
    )
    return [line for line in output.splitlines() if line]


def is_allowed(path: str) -> bool:
    if path in ALLOWED_EXACT or path.startswith(ALLOWED_PREFIXES):
        return True
    if path.startswith(ALLOWED_WORKFLOW_PREFIX) and path.endswith((".yml", ".yaml")):
        return True
    return any(path.endswith(suffix) for suffix in ALLOWED_ICON_SUFFIXES)


def is_protected(path: str) -> bool:
    return path in PROTECTED_EXACT or path.startswith(PROTECTED_PREFIXES)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reject recovery-branch changes outside the DIRECTIVE approved-icon/release-engineering scope."
    )
    parser.add_argument("--base", required=True, help="Protected baseline commit/ref")
    args = parser.parse_args()

    paths = changed_paths(args.base)
    protected_changes = [path for path in paths if is_protected(path)]
    out_of_scope = [path for path in paths if not is_allowed(path)]

    failures = sorted(set(protected_changes + out_of_scope))
    if failures:
        print("FAIL: recovery branch scope violation")
        for path in failures:
            print(f" - {path}")
        return 1

    print(f"PASS: {len(paths)} changed path(s) remain inside recovery allowlist")
    for path in paths:
        print(f" + {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
