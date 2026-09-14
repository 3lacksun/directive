#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

PACKAGE_RE = re.compile(r"^package:\s+name='([^']+)'", re.MULTILINE)
LAUNCHABLE_RE = re.compile(r"^launchable-activity:\s+name='([^']+)'", re.MULTILINE)
DEBUGGABLE_RE = re.compile(r"^application-debuggable\s*$", re.MULTILINE)
TEST_ONLY_RE = re.compile(r"^application-testOnly\s*$", re.MULTILINE)
TARGET_SDK_RE = re.compile(r"^targetSdkVersion:'([^']+)'\s*$", re.MULTILINE)


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def exactly_one(pattern: re.Pattern[str], text: str, label: str) -> str:
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {label}, found {len(matches)}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed DIRECTIVE release manifest/badging gate."
    )
    parser.add_argument("--aapt-badging-output", type=Path, required=True)
    parser.add_argument("--expected-package", required=True)
    parser.add_argument("--expected-launchable-activity", required=True)
    parser.add_argument("--expected-target-sdk", default="36")
    args = parser.parse_args()

    if args.expected_target_sdk != "36":
        return fail(
            f"DIRECTIVE release targetSdk must remain 36, got {args.expected_target_sdk}"
        )
    if not args.aapt_badging_output.is_file():
        return fail(f"aapt badging evidence missing: {args.aapt_badging_output}")

    badging = args.aapt_badging_output.read_text(encoding="utf-8", errors="replace")

    if DEBUGGABLE_RE.search(badging):
        return fail("release candidate is marked application-debuggable")
    if TEST_ONLY_RE.search(badging):
        return fail("release candidate is marked application-testOnly")

    try:
        package_name = exactly_one(PACKAGE_RE, badging, "package identity line")
        launchable = exactly_one(LAUNCHABLE_RE, badging, "launchable activity")
        target_sdk = exactly_one(TARGET_SDK_RE, badging, "targetSdkVersion line")
    except ValueError as exc:
        return fail(str(exc))

    if package_name != args.expected_package:
        return fail(
            f"package mismatch: actual={package_name} expected={args.expected_package}"
        )
    if launchable != args.expected_launchable_activity:
        return fail(
            f"launchable activity mismatch: actual={launchable} expected={args.expected_launchable_activity}"
        )
    if target_sdk != args.expected_target_sdk:
        return fail(
            f"targetSdk mismatch: actual={target_sdk} expected={args.expected_target_sdk}"
        )

    print("PASS: DIRECTIVE release manifest/badging gate")
    print(f" package={package_name}")
    print(f" launchable_activity={launchable}")
    print(f" targetSdk={target_sdk}")
    print(" debuggable=false")
    print(" testOnly=false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
