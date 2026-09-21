#!/usr/bin/env python3
# Source of truth: SCRIPTS/githubactions. Generated copies are overwritten.
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('pins', Path(__file__).with_name('read-core-pins.py'))
pins = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pins)


class CorePinsTests(unittest.TestCase):
    def test_manual_override_and_stable_default_drive_actual_build_pins(self):
        for override in ('b' * 40, ''):
            with self.subTest(override=override), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                (root / 'fedora45-ai-core-pre').mkdir()
                (root / 'fedora45-ai-core').mkdir()
                (root / 'fedora45-ai-core-pre/Containerfile').write_text(
                    'ARG OPENCLAW_VERSION=2026.9.5\nARG OPENCLAW_UPSTREAM_SHA=' + override + '\n')
                (root / 'fedora45-ai-core/build.conf').write_text('OPENCLAW_EPHEMERAL_COMMIT=' + 'e' * 40 + '\n')
                build = root / 'build.conf'
                build.write_text('OPENCLAW_VERSION=2026.9.5\nOPENCLAW_UPSTREAM_SHA=' + 'a' * 40 +
                    '\nOPENCLAW_DETERMINISTIC_RELEASE_TAG=2026.9.5-deterministic.3\n')
                def github(command, **kwargs):
                    if command[-1].endswith('/commits/v2026.9.5'):
                        self.assertFalse(override)
                        return json.dumps({'sha': 'c' * 40})
                    return json.dumps([{'tag_name': '2026.9.5-deterministic.3'}])
                with patch.object(pins.subprocess, 'check_output', side_effect=github):
                    selected = pins.read_pins(root, build)
                self.assertEqual(selected['upstream_sha'], override or 'c' * 40)
                self.assertEqual(selected['ephemeral_sha'], 'e' * 40)
                self.assertIn('OPENCLAW_UPSTREAM_SHA=' + (override or 'c' * 40), build.read_text())
                self.assertIn('OPENCLAW_DETERMINISTIC_RELEASE_TAG=2026.9.5-deterministic.4', build.read_text())


if __name__ == '__main__':
    unittest.main()
