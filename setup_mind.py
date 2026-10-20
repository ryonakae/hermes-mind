#!/usr/bin/env python3
"""Fetch the pinned upstream mind.py artifact into this plugin."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import urllib.request


MIND_VERSION = "7.0.0"
UPSTREAM_COMMIT = "ade5b2a20e37773e2ae58640b13b59840b739177"
MIND_SHA256 = "ae2fc389b3b09c93cb432ab55b71063d98b400da6b18d6bc178322bc8f3fcf69"
UPSTREAM_URL = f"https://raw.githubusercontent.com/Da7-Tech/mind/{UPSTREAM_COMMIT}/mind.py"
DOWNLOAD_TIMEOUT_SECONDS = 30
CHUNK_SIZE = 1024 * 1024
DEFAULT_DESTINATION = Path(__file__).resolve().parent / "vendor" / "mind.py"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def install_artifact(destination: Path) -> bool:
    """Install the verified artifact, returning False when already current."""
    destination = Path(destination)
    if destination.is_file() and _sha256(destination) == MIND_SHA256:
        return False

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    digest = hashlib.sha256()
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{destination.name}.",
            dir=destination.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            with urllib.request.urlopen(UPSTREAM_URL, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                for chunk in iter(lambda: response.read(CHUNK_SIZE), b""):
                    temporary.write(chunk)
                    digest.update(chunk)
            temporary.flush()
            os.fsync(temporary.fileno())

        actual_sha256 = digest.hexdigest()
        if actual_sha256 != MIND_SHA256:
            raise RuntimeError(
                f"downloaded mind.py SHA-256 {actual_sha256} does not match pinned {MIND_SHA256}"
            )

        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, destination)
        temporary_path = None
        return True
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install the pinned hermes-mind upstream artifact")
    parser.add_argument(
        "--destination",
        type=Path,
        default=DEFAULT_DESTINATION,
        help=f"artifact path (default: {DEFAULT_DESTINATION})",
    )
    args = parser.parse_args(argv)

    destination = args.destination.expanduser()
    try:
        changed = install_artifact(destination)
    except Exception as exc:
        print(f"setup failed; existing artifact was not replaced: {exc}", file=sys.stderr)
        return 1

    if changed:
        print(f"installed mind {MIND_VERSION} at {destination}")
    else:
        print(f"mind {MIND_VERSION} already verified at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
