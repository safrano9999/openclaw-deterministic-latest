#!/usr/bin/env python3
# Source of truth: SCRIPTS/githubactions. Generated copies are overwritten.
"""Check immutable runtime bundle identity without building OpenClaw."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest


class RuntimeBundleTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.config = self.root / "build.conf"
        self.config.write_text("OPENCLAW_VERSION=2026.9.5\nOPENCLAW_UPSTREAM_SHA=" + "a" * 40 +
            "\nOPENCLAW_BUILD_LABEL=2026.9.5-patched\nOPENCLAW_DETERMINISTIC_RELEASE_TAG=2026.9.5-deterministic.3\n")
        self.output = self.root / "runtime.tar.gz"
        self.package("openclaw.tgz", "openclaw")

    def package(self, filename, name, version="2026.9.5"):
        with tarfile.open(self.root / filename, "w:gz") as archive:
            for path, data in {
                "package/package.json": json.dumps({"name": name, "version": version,
                    "dependencies": {"zod": "4.6.2"}, "exports": {"./new": "./dist/new.js"}}).encode(),
                "package/dist/deterministic-gateway-replies.txt": b"dummy reply",
                "package/dist/control-ui/index.html": b"UI",
            }.items():
                member = tarfile.TarInfo(path)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))

    def bundle(self):
        return subprocess.run([sys.executable, str(Path(__file__).with_name("package-runtime.py")),
            str(self.root / "openclaw.tgz"), str(self.config), str(self.output)],
            text=True, capture_output=True)

    def test_complete_package_bytes_and_stable_identity_are_preserved(self):
        result = self.bundle()
        self.assertEqual(result.returncode, 0, result.stderr)
        original = self.output.read_bytes()
        with tarfile.open(self.output) as archive:
            manifest = json.load(archive.extractfile("manifest.json"))
            self.assertEqual(manifest["version"], "2026.9.5")
            self.assertEqual(manifest["displayVersion"], "2026.9.5-patched")
            self.assertEqual(manifest["upstreamCommit"], "a" * 40)
            for name in ("openclaw.tgz",):
                data = archive.extractfile(name).read()
                self.assertEqual(data, (self.root / name).read_bytes())
                self.assertEqual(hashlib.sha256(data).hexdigest(), manifest["artifacts"][name])
        self.assertEqual(self.bundle().returncode, 0)
        self.assertEqual(self.output.read_bytes(), original)

    def test_mixed_release_openclaw_does_not_replace_previous_bundle(self):
        self.assertEqual(self.bundle().returncode, 0)
        original = self.output.read_bytes()
        self.package("openclaw.tgz", "openclaw", "2026.9.4")
        self.assertNotEqual(self.bundle().returncode, 0)
        self.assertEqual(self.output.read_bytes(), original)

    def test_floating_main_is_not_a_source_pin(self):
        self.config.write_text(self.config.read_text().replace("a" * 40, "main"))
        self.assertNotEqual(self.bundle().returncode, 0)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
