#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

PHASE1_TEST_CERT_SHA256 = "420a3ce0c50cd0c77aa5633fecbbcb4436145e871f26bc9feae9d6cb15bef81c"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
CERT_PATTERNS = (
    re.compile(r"certificate SHA-256 digest:\s*([0-9A-Fa-f:]{64,95})", re.I),
    re.compile(r"Signer #\d+ certificate SHA-256 digest:\s*([0-9A-Fa-f:]{64,95})", re.I),
)
NUMBER_OF_SIGNERS = re.compile(r"^Number of signers:\s*(\d+)\s*$", re.I | re.M)
SCHEME_PATTERN = re.compile(
    r"^Verified using v(\d+(?:\.\d+)?) scheme \([^\n]+\):\s*(true|false)\s*$",
    re.I | re.M,
)


def normalise(value: str) -> str:
    return re.sub(r"[^0-9a-f]", "", value.lower())


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def extract_cert(text: str):
    hits = []
    for pattern in CERT_PATTERNS:
        for match in pattern.finditer(text):
            value = normalise(match.group(1))
            if HEX64.fullmatch(value):
                hits.append(value)
    return sorted(set(hits))


def verified_modern_scheme(text: str) -> bool:
    for version, result in SCHEME_PATTERN.findall(text):
        try:
            major = int(version.split(".", 1)[0])
        except ValueError:
            continue
        if major >= 2 and result.lower() == "true":
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed DIRECTIVE production signer acceptance gate.")
    parser.add_argument(
        "--expected-release-cert-sha256",
        required=True,
        help="Authoritative stable/release certificate SHA-256 fingerprint",
    )
    parser.add_argument(
        "--apksigner-output",
        required=True,
        type=Path,
        help="Captured `apksigner verify --verbose --print-certs` output for the exact candidate",
    )
    args = parser.parse_args()

    expected = normalise(args.expected_release_cert_sha256)
    if not HEX64.fullmatch(expected):
        return fail("expected release certificate is not a 64-hex SHA-256 fingerprint")
    if expected == PHASE1_TEST_CERT_SHA256:
        return fail("expected release certificate equals the disposable Phase 1 test certificate")
    if not args.apksigner_output.is_file():
        return fail(f"apksigner output not found: {args.apksigner_output}")

    text = args.apksigner_output.read_text(encoding="utf-8", errors="replace")
    if not re.search(r"^Verifies\s*$", text, re.I | re.M):
        return fail("apksigner output does not contain the standalone successful verification marker")

    signer_match = NUMBER_OF_SIGNERS.search(text)
    if not signer_match:
        return fail("apksigner output does not report Number of signers")
    signer_count = int(signer_match.group(1))
    if signer_count != 1:
        return fail(f"expected exactly one signer, found: {signer_count}")

    if not verified_modern_scheme(text):
        return fail("candidate is not verified by any APK Signature Scheme v2 or newer")

    certs = extract_cert(text)
    if not certs:
        return fail("no valid certificate SHA-256 fingerprint found in apksigner output")
    if len(certs) != 1:
        return fail("expected exactly one unique signer certificate, found: " + ",".join(certs))

    actual = certs[0]
    if actual == PHASE1_TEST_CERT_SHA256:
        return fail("candidate is signed by the disposable Phase 1 test certificate")
    if actual != expected:
        return fail(f"release signer mismatch: actual={actual} expected={expected}")

    print("PASS: DIRECTIVE production signer fingerprint matches authoritative release identity")
    print(f" release_cert_sha256={actual}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
