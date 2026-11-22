#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Index explicitly selected public assets, excluding local build products."""
import hashlib
import json
from pathlib import Path
from verify import ROOT, manifest


def role(path):
    if path.suffix == ".png":
        return "preview"
    if path.name.startswith(("10_", "11_")):
        return "optional_fit_test"
    if path.name.startswith("00_fit"):
        return "assembly_with_electronic_reference"
    if path.name.startswith("00_"):
        return "assembly_reference"
    return {".stl": "print_part", ".dxf": "layout_reference", ".step": "editable_part"}[path.suffix]


def make_catalog():
    editions = json.loads((ROOT / "projects.json").read_text())["projects"]
    files = []
    for name in sorted(manifest(ROOT)):
        path = Path(name)
        if path.suffix not in {".stl", ".step", ".dxf", ".png"}:
            continue
        data = (ROOT / path).read_bytes()
        files.append({"edition": path.parts[0], "path": name, "role": role(path),
                      "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    return {"units": "mm", "editions": editions, "files": files,
            "total_bytes": sum(entry["bytes"] for entry in files)}


if __name__ == "__main__":
    catalog = make_catalog()
    (ROOT/"model-index.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    print(f"Indexed {len(catalog['files'])} model and preview files.")
