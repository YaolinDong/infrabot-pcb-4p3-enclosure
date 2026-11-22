# SPDX-License-Identifier: MIT
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "simple/source"))
from source_audit import audit_sources


class MeasurementSources(unittest.TestCase):
    def test_geometry_only_relaxes_absent_external_sources(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            data = {"drawing": {"sha256": hashlib.sha256(b"original").hexdigest()}}
            self.assertTrue(audit_sources(root, data, True)["passed"])
            self.assertFalse(audit_sources(root, data, False)["passed"])
            source_map = root / "map.json"
            source_map.write_text(json.dumps({"drawing": "original.bin"}))
            os.environ["ENCLOSURE_SOURCE_MAP"] = str(source_map)
            self.assertFalse(audit_sources(root, data, True)["passed"])
            (root / "original.bin").write_bytes(b"wrong")
            self.assertFalse(audit_sources(root, data, True)["passed"])
            (root / "original.bin").write_bytes(b"original")
            self.assertTrue(audit_sources(root, data, False)["complete"])
            data["required"] = {"file": "required.step", "sha256": data["drawing"]["sha256"]}
            self.assertFalse(audit_sources(root, data, True)["passed"])
