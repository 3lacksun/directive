#!/usr/bin/env python3
import argparse
import subprocess
import sys

PROTECTED_BASE = "67ac7ec4631503ae47caeaf6cae41c5724b57ef4"

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


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        text=True,
        capture_output=True,
        check=check,
    )


def verify_protected_base(requested_base: str) -> None:
    if requested_base != PROTECTED_BASE:
        raise RuntimeError(
            f"requested base {requested_base!r} does not equal locked protected base {PROTECTED_BASE}"
        )

    resolved = git("rev-parse", "--verify", f"{PROTECTED_BASE}^{{commit}}").stdout.strip()
    if resolved != PROTECTED_BASE:
        raise RuntimeError(
            f"locked protected base resolves to unexpected commit {resolved}"
        )

    ancestor = git("merge-base", "--is-ancestor", PROTECTED_BASE, "HEAD", check=False)
    if ancestor.returncode != 0:
        raise RuntimeError("locked protected base is not an ancestor of HEAD")

    merge_base = git("merge-base", PROTECTED_BASE, "HEAD").stdout.strip()
    if merge_base != PROTECTED_BASE:
        raise RuntimeError(
            f"unexpected merge-base {merge_base}; expected locked protected base {PROTECTED_BASE}"
        )


def changed_paths() -> list[str]:
    output = git("diff", "--name-only", f"{PROTECTED_BASE}...HEAD").stdout
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
    parser.add_argument(
        "--base",
        default=PROTECTED_BASE,
        help="Protected baseline commit; must equal the locked Phase 1 recovery base",
    )
    args = parser.parse_args()

    try:
        verify_protected_base(args.base)
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"FAIL: protected-base continuity error: {exc}")
        return 1

    paths = changed_paths()
    protected_changes = [path for path in paths if is_protected(path)]
    out_of_scope = [path for path in paths if not is_allowed(path)]

    failures = sorted(set(protected_changes + out_of_scope))
    if failures:
        print("FAIL: recovery branch scope violation")
        for path in failures:
            print(f" - {path}")
        return 1

    print(
        f"PASS: locked base {PROTECTED_BASE} is the verified ancestor/merge-base and "
        f"{len(paths)} changed path(s) remain inside the recovery allowlist"
    )
    for path in paths:
        print(f" + {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
