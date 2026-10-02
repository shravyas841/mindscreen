"""Verify the frozen evaluation methods and checked-in evidence artifacts."""

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "FROZEN_SHA256.txt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    failures = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        expected, relative = line.split(maxsplit=1)
        path = (ROOT / relative).resolve()
        actual = sha256(path)
        status = "OK" if actual == expected else "MISMATCH"
        print(f"{status:8} {relative}")
        if actual != expected:
            failures.append(relative)
    if failures:
        raise SystemExit(f"Hash verification failed for {len(failures)} file(s)")


if __name__ == "__main__":
    main()
