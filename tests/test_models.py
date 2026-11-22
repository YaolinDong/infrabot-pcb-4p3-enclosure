# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import os
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify import manifest, mesh, verify


class ReleaseChecks(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name in manifest(ROOT):
            dest = self.root / name
            dest.parent.mkdir(exist_ok=True, parents=True)
            try:
                os.link(ROOT / name, dest)
            except OSError:
                shutil.copyfile(ROOT / name, dest)

    def replace(self, name, data):
        path = self.root / name
        path.unlink()
        path.write_bytes(data)

    def test_release_snapshot(self):
        assets, _ = verify(self.root)
        self.assertEqual(assets, len(json.loads((ROOT/"model-index.json").read_text())["files"]))

    def test_changed_mesh(self):
        path = next(self.root.glob("simple/STL/*.stl"))
        self.replace(path.relative_to(self.root), b"!" + path.read_bytes()[1:])
        with self.assertRaisesRegex(ValueError, "digest or size"):
            verify(self.root)

    def test_missing_file(self):
        (self.root / "simple/STL/01_lower_shell.stl").unlink()
        with self.assertRaisesRegex(ValueError, "missing or non-regular"):
            verify(self.root)

    def test_broken_assembly_link(self):
        self.replace("simple/README.md", b"[hardware](missing-file.json)")
        with self.assertRaisesRegex(ValueError, "broken local link"):
            verify(self.root)

    def test_unlisted_step(self):
        (self.root / "simple/STEP/extra.step").touch()
        with self.assertRaisesRegex(ValueError, "unlisted model"):
            verify(self.root)

    def test_invalid_mesh(self):
        with self.assertRaisesRegex(ValueError, "triangle count"):
            mesh(bytes(84))
