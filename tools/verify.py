#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate the downloadable snapshot without installing CAD tools."""
import gzip
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
HOME_PATH = re.compile(rb"/home[/][^/\s\x00]+")
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")


def manifest(root):
    lines = (root / "tools/public_manifest.txt").read_text().splitlines()
    if len(lines) != len(set(lines)):
        raise ValueError("duplicate public manifest entry")
    for name in lines:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or not name or path.as_posix() != name:
            raise ValueError("invalid public manifest path")
    return set(lines)


def mesh(data):
    if len(data) < 84:
        raise ValueError("short binary STL")
    count, = struct.unpack_from("<I", data, 80)
    if not count or len(data) != 84 + 50 * count:
        raise ValueError("invalid STL triangle count")
    low, high = [math.inf]*3, [-math.inf]*3
    volume = 0.0
    for row in struct.iter_unpack("<12fH", memoryview(data)[84:]):
        if not all(map(math.isfinite, row[:12])):
            raise ValueError("non-finite STL coordinates")
        a, b, c = row[3:6], row[6:9], row[9:12]
        for i in range(3):
            low[i] = min(low[i], a[i], b[i], c[i])
            high[i] = max(high[i], a[i], b[i], c[i])
        volume += (a[0]*(b[1]*c[2]-b[2]*c[1]) + a[1]*(b[2]*c[0]-b[0]*c[2])
                   + a[2]*(b[0]*c[1]-b[1]*c[0]))
    if volume <= 0 or any(l >= h for l,h in zip(low, high)):
        raise ValueError("degenerate or inverted STL")
    return count, low + high, volume / 6


def check_links(root, path, data):
    for link in LINK.findall(data.decode()):
        target = urlsplit(link.strip("<>"))
        if target.scheme or target.netloc or not target.path:
            continue
        dest = (path.parent / unquote(target.path)).resolve()
        if not dest.is_relative_to(root.resolve()) or not dest.exists():
            raise ValueError(f"broken local link in {path.relative_to(root)}")


def verify(root=ROOT):
    names = manifest(root)
    index = json.loads((root / "model-index.json").read_text())
    records = {entry["path"]: entry for entry in index["files"]}
    assets = {s for s in names if Path(s).suffix.lower() in (".stl", ".step", ".dxf", ".png")}
    if assets != records.keys() or len(records) != len(index["files"]):
        raise ValueError("catalog and public model/preview list differ")
    if index["total_bytes"] != sum(item["bytes"] for item in records.values()):
        raise ValueError("catalog total differs")
    for edition in ("simple", "deluxe"):
        for folder in ("STL", "STEP"):
            for path in (root / edition / folder).iterdir():
                if path.is_file() and path.relative_to(root).as_posix() not in assets:
                    raise ValueError("unlisted model: " + path.name)
    for name in sorted(names):
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError("missing or non-regular public file: " + name)
        data = path.read_bytes()
        if HOME_PATH.search(data) or (name.endswith(".gz") and HOME_PATH.search(gzip.decompress(data))):
            raise ValueError("absolute home path: " + name)
        if name in records:
            item = records[name]
            if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError("asset digest or size differs: " + name)
            if name.endswith(".stl"):
                mesh(data)
            if name.endswith(".step") and not data.startswith(b"ISO-10303-21;"):
                raise ValueError("invalid STEP header: " + name)
        if name.endswith(".md"):
            check_links(root, path, data)
    for row in json.loads((root / "simple/reference/inputs.json").read_text())["inputs"]:
        name = "simple/" + row["compressed"]
        if name not in names:
            raise ValueError("missing frozen input")
        data = (root / name).read_bytes()
        raw = gzip.decompress(data)
        if (len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]
                or hashlib.sha256(data).hexdigest() != row["compressed_sha256"]):
            raise ValueError("frozen reference differs: " + name)
    return len(records), len(names)


if __name__ == "__main__":
    try:
        assets, files = verify()
    except (ValueError, OSError, KeyError) as error:
        sys.exit(str(error))
    print(f"Verified {assets} model/preview files and {files} public paths.")
