#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
from pathlib import Path

EXPECTED_PHASE1_APK = "DIRECTIVE_LEGACY_MONETISATION_REMOVED_PHASE1_TESTSIGNED_12092026175450.apk"
EXPECTED_PHASE1_SHA256 = "d30a725ccecefa01cf480e3ad3a266f61b298357affd5628a5b7934478170c85"
EXPECTED_TEST_CERT_SHA256 = "420a3ce0c50cd0c77aa5633fecbbcb4436145e871f26bc9feae9d6cb15bef81c"
EXPECTED_BASELINE_APK = "DIRECTIVE_EXEC002_ANDROID16_RECEIVER_FIXED_TESTSIGNED_11092026174220.apk"
EXPECTED_BASELINE_SHA256 = "58bf319f1ddf0920680cea5a3cbab572a6406e01734a6a24cfb174b66ef2cf75"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalise(value: str) -> str:
    return value.lower().replace(":", "").strip()


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed continuity check for the runtime-proven DIRECTIVE Phase 1 test-signed baseline."
    )
    parser.add_argument("--report", required=True, type=Path, help="Phase 1 verification JSON")
    parser.add_argument("--apk", type=Path, help="Optional exact Phase 1 APK for byte-hash verification")
    parser.add_argument(
        "--expected-release-cert-sha256",
        help="Optional authorised stable/release certificate fingerprint. The Phase 1 disposable test signer must NOT be mistaken for it.",
    )
    args = parser.parse_args()

    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except Exception as exc:
        return fail(f"cannot read report: {exc}")

    checks = {
        "product": report.get("product") == "DIRECTIVE",
        "baseline": report.get("baseline") == EXPECTED_BASELINE_APK,
        "baseline_sha256": normalise(str(report.get("baseline_sha256", ""))) == EXPECTED_BASELINE_SHA256,
        "output": report.get("output") == EXPECTED_PHASE1_APK,
        "output_sha256": normalise(str(report.get("output_sha256", ""))) == EXPECTED_PHASE1_SHA256,
        "patch_verification": report.get("patch_verification_pass") is True,
        "zip_integrity": report.get("zip_integrity") == "PASS",
        "v2_verified": report.get("v2_signature_independent_verification", {}).get("verified") is True,
        "v2_certificate": normalise(str(report.get("v2_signature_independent_verification", {}).get("certificate_sha256", ""))) == EXPECTED_TEST_CERT_SHA256,
        "known_good_certificate": normalise(str(report.get("v2_verifier_crosscheck_against_original_known_good", {}).get("certificate_sha256", ""))) == EXPECTED_TEST_CERT_SHA256,
        "runtime_unexecuted": report.get("runtime_device_install") == "UNEXECUTED",
    }

    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        return fail("report continuity mismatch: " + ", ".join(failed))

    if args.apk:
        if not args.apk.is_file():
            return fail(f"APK not found: {args.apk}")
        apk_hash = sha256_file(args.apk)
        if apk_hash != EXPECTED_PHASE1_SHA256:
            return fail(f"APK SHA-256 mismatch: {apk_hash}")

    if args.expected_release_cert_sha256:
        release_cert = normalise(args.expected_release_cert_sha256)
        if release_cert == EXPECTED_TEST_CERT_SHA256:
            return fail("authorised stable/release certificate equals disposable Phase 1 test certificate")
        print(f"PASS: release signer is distinct from Phase 1 disposable test signer ({release_cert})")

    print("PASS: DIRECTIVE Phase 1 report identity and disposable test-signer continuity verified")
    print(f" phase1_apk={EXPECTED_PHASE1_APK}")
    print(f" phase1_sha256={EXPECTED_PHASE1_SHA256}")
    print(f" phase1_test_cert_sha256={EXPECTED_TEST_CERT_SHA256}")
    print(" device_runtime=UNEXECUTED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
