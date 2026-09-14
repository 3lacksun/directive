#!/usr/bin/env python3
import argparse
import hashlib
import re
import sys
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-f]{64}$")
PHASE1_TEST_CERT_SHA256 = "420a3ce0c50cd0c77aa5633fecbbcb4436145e871f26bc9feae9d6cb15bef81c"
DIRECTIVE_TARGET_SDK = "36"
PKG_RE = re.compile(
    r"^package:\s+name='([^']+)'\s+versionCode='([^']+)'\s+versionName='([^']*)'.*?compileSdkVersion='([^']+)'",
    re.MULTILINE,
)
MIN_SDK_RE = re.compile(r"^sdkVersion:'([^']+)'\s*$", re.MULTILINE)
TARGET_SDK_RE = re.compile(r"^targetSdkVersion:'([^']+)'\s*$", re.MULTILINE)
SIGNER_COUNT_RE = re.compile(r"^Number of signers:\s*(\d+)\s*$", re.MULTILINE)
CERT_RE = re.compile(r"certificate SHA-256 digest:\s*([0-9A-Fa-f:]{64,95})", re.I)
SCHEME_RE = re.compile(
    r"^Verified using v(2|3|3\.1|3\.2|4) scheme(?: \([^)]*\))?:\s*true\s*$",
    re.MULTILINE,
)


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def normalise_hex(value: str) -> str:
    return re.sub(r"[^0-9a-f]", "", value.lower())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exactly_one(pattern: re.Pattern[str], text: str, label: str) -> str:
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {label}, found {len(matches)}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed DIRECTIVE APK release-candidate identity gate."
    )
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--expected-apk-sha256", required=True)
    parser.add_argument("--expected-package", required=True)
    parser.add_argument("--expected-version-code", required=True)
    parser.add_argument("--expected-version-name", required=True)
    parser.add_argument("--expected-min-sdk", required=True)
    parser.add_argument("--expected-compile-sdk", required=True)
    parser.add_argument("--expected-target-sdk", required=True)
    parser.add_argument("--expected-release-cert-sha256", required=True)
    parser.add_argument("--aapt-badging-output", type=Path, required=True)
    parser.add_argument("--apksigner-output", type=Path, required=True)
    args = parser.parse_args()

    if not args.apk.is_file():
        return fail(f"APK not found: {args.apk}")

    expected_apk = normalise_hex(args.expected_apk_sha256)
    expected_cert = normalise_hex(args.expected_release_cert_sha256)
    if not HEX64.fullmatch(expected_apk):
        return fail("expected APK SHA-256 is not 64 hex")
    if not HEX64.fullmatch(expected_cert):
        return fail("expected release certificate SHA-256 is not 64 hex")
    if expected_cert == PHASE1_TEST_CERT_SHA256:
        return fail("expected release certificate equals the disposable Phase 1 test certificate")
    if args.expected_target_sdk != DIRECTIVE_TARGET_SDK:
        return fail(
            f"DIRECTIVE release targetSdk must be {DIRECTIVE_TARGET_SDK}, got {args.expected_target_sdk}"
        )
    if args.expected_compile_sdk != DIRECTIVE_TARGET_SDK:
        return fail(
            f"DIRECTIVE release compileSdk must be {DIRECTIVE_TARGET_SDK}, got {args.expected_compile_sdk}"
        )

    actual_apk = sha256_file(args.apk)
    if actual_apk != expected_apk:
        return fail(f"APK SHA-256 mismatch: actual={actual_apk} expected={expected_apk}")

    if not args.aapt_badging_output.is_file():
        return fail("aapt badging evidence missing")
    badging = args.aapt_badging_output.read_text(encoding="utf-8", errors="replace")
    package_matches = PKG_RE.findall(badging)
    if len(package_matches) != 1:
        return fail(f"expected exactly one package identity line, found {len(package_matches)}")

    package_name, version_code, version_name, compile_sdk = package_matches[0]
    try:
        min_sdk = exactly_one(MIN_SDK_RE, badging, "min sdkVersion line")
        target_sdk = exactly_one(TARGET_SDK_RE, badging, "targetSdkVersion line")
    except ValueError as exc:
        return fail(str(exc))

    identity_checks = (
        ("package", package_name, args.expected_package),
        ("versionCode", version_code, args.expected_version_code),
        ("versionName", version_name, args.expected_version_name),
        ("minSdk", min_sdk, args.expected_min_sdk),
        ("compileSdk", compile_sdk, args.expected_compile_sdk),
        ("targetSdk", target_sdk, args.expected_target_sdk),
    )
    for label, actual, expected in identity_checks:
        if actual != expected:
            return fail(f"{label} mismatch: actual={actual} expected={expected}")

    if target_sdk != DIRECTIVE_TARGET_SDK or compile_sdk != DIRECTIVE_TARGET_SDK:
        return fail("candidate is not an Android 16/API 36 DIRECTIVE release candidate")

    if not args.apksigner_output.is_file():
        return fail("apksigner evidence missing")
    signer = args.apksigner_output.read_text(encoding="utf-8", errors="replace")
    if not re.search(r"^Verifies\s*$", signer, re.MULTILINE):
        return fail("apksigner evidence lacks standalone Verifies marker")

    signer_counts = SIGNER_COUNT_RE.findall(signer)
    if len(signer_counts) != 1 or signer_counts[0] != "1":
        return fail("apksigner evidence does not report exactly one signer")
    if not SCHEME_RE.search(signer):
        return fail("no verified APK Signature Scheme v2-or-newer evidence")

    certificates = sorted(
        {
            normalise_hex(value)
            for value in CERT_RE.findall(signer)
            if HEX64.fullmatch(normalise_hex(value))
        }
    )
    if len(certificates) != 1:
        return fail(
            f"expected exactly one unique signer certificate SHA-256, found {len(certificates)}"
        )
    if certificates[0] == PHASE1_TEST_CERT_SHA256:
        return fail("candidate is signed by the disposable Phase 1 test certificate")
    if certificates[0] != expected_cert:
        return fail(
            f"release signer mismatch: actual={certificates[0]} expected={expected_cert}"
        )

    print("PASS: DIRECTIVE release candidate identity is internally bound")
    print(f" apk_sha256={actual_apk}")
    print(f" package={package_name}")
    print(f" versionCode={version_code}")
    print(f" versionName={version_name}")
    print(f" minSdk={min_sdk}")
    print(f" compileSdk={compile_sdk}")
    print(f" targetSdk={target_sdk}")
    print(f" release_cert_sha256={certificates[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
