from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]
SETUP_SCRIPT = REPO / "setup_mind.py"


def load_setup():
    spec = importlib.util.spec_from_file_location("_test_hermes_mind_setup", SETUP_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self.payload) - self.offset
        chunk = self.payload[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


class SetupMindTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = load_setup()
        cls.artifact = (REPO / "vendor" / "mind.py").read_bytes()

    def test_downloads_verified_artifact_to_destination(self):
        with tempfile.TemporaryDirectory(prefix="hermes-mind-setup-") as temp:
            destination = Path(temp) / "vendor" / "mind.py"
            with patch.object(self.setup.urllib.request, "urlopen", return_value=_Response(self.artifact)) as urlopen:
                changed = self.setup.install_artifact(destination)

            self.assertTrue(changed)
            self.assertEqual(destination.read_bytes(), self.artifact)
            urlopen.assert_called_once_with(self.setup.UPSTREAM_URL, timeout=self.setup.DOWNLOAD_TIMEOUT_SECONDS)

    def test_correct_existing_artifact_is_idempotent_without_network(self):
        with tempfile.TemporaryDirectory(prefix="hermes-mind-setup-") as temp:
            destination = Path(temp) / "mind.py"
            destination.write_bytes(self.artifact)
            with patch.object(self.setup.urllib.request, "urlopen", side_effect=AssertionError("network used")):
                changed = self.setup.install_artifact(destination)

            self.assertFalse(changed)
            self.assertEqual(destination.read_bytes(), self.artifact)

    def test_hash_failure_preserves_existing_artifact(self):
        original = b"existing artifact"
        with tempfile.TemporaryDirectory(prefix="hermes-mind-setup-") as temp:
            destination = Path(temp) / "mind.py"
            destination.write_bytes(original)
            bad_payload = b"wrong upstream bytes"
            with patch.object(self.setup.urllib.request, "urlopen", return_value=_Response(bad_payload)):
                with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                    self.setup.install_artifact(destination)

            self.assertEqual(destination.read_bytes(), original)

    def test_network_failure_preserves_existing_artifact(self):
        original = b"existing artifact"
        with tempfile.TemporaryDirectory(prefix="hermes-mind-setup-") as temp:
            destination = Path(temp) / "mind.py"
            destination.write_bytes(original)
            with patch.object(self.setup.urllib.request, "urlopen", side_effect=OSError("offline")):
                with self.assertRaisesRegex(OSError, "offline"):
                    self.setup.install_artifact(destination)

            self.assertEqual(destination.read_bytes(), original)

    def test_pinned_provenance_constants_are_stable(self):
        self.assertEqual(self.setup.UPSTREAM_COMMIT, "ade5b2a20e37773e2ae58640b13b59840b739177")
        self.assertEqual(
            self.setup.MIND_SHA256,
            "ae2fc389b3b09c93cb432ab55b71063d98b400da6b18d6bc178322bc8f3fcf69",
        )
        self.assertEqual(hashlib.sha256(self.artifact).hexdigest(), self.setup.MIND_SHA256)


if __name__ == "__main__":
    unittest.main(verbosity=2)
