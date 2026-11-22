#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare printable geometry after a rebuild (dimensions in mm)."""
import argparse
from pathlib import Path
from verify import mesh


def compare(original, rebuilt):
    def files(root):
        return {p.relative_to(root) for p in root.glob("*/STL/*.stl")}
    expected = files(original)
    if not expected or expected != files(rebuilt):
        raise ValueError("STL file lists differ or are empty")
    for name in sorted(expected):
        n0, box0, v0 = mesh((original / name).read_bytes())
        n1, box1, v1 = mesh((rebuilt / name).read_bytes())
        bounds_delta = max(abs(a-b) for a,b in zip(box0, box1))
        volume_delta = abs(v1-v0) / v0
        print(f"{name}: {n0}/{n1} triangles; max bounds delta {bounds_delta:.8g} mm; "
              f"volume {v0:.8f}/{v1:.8f} mm³; relative delta {volume_delta:.8g}")
        if n0 != n1 or bounds_delta > 0.01 or volume_delta > 0.0001:
            raise ValueError("geometry differs: " + str(name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("original", type=Path)
    parser.add_argument("rebuilt", type=Path)
    args = parser.parse_args()
    compare(args.original, args.rebuilt)
