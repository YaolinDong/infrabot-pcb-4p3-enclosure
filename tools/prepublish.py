# SPDX-License-Identifier: MIT
"""Check the proposed public tree and, optionally, every reachable revision."""
import argparse
import gzip
import os
from pathlib import Path
import stat
import subprocess
import sys

from verify import HOME_PATH, ROOT, manifest, verify


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def private_rules():
    name = os.environ.get("INFRABOT_PRIVATE_DENYLIST")
    if not name:
        if os.environ.get("CI", "").lower() == "true":
            print("SKIP private literal scan in CI (external denylist unavailable)")
            return []
        sys.exit("Set INFRABOT_PRIVATE_DENYLIST to the private rule file")
    path = Path(name).resolve()
    mode = path.stat().st_mode
    if path.is_relative_to(ROOT) or not stat.S_ISREG(mode) or stat.S_IMODE(mode) != 0o600:
        sys.exit("Use a mode-0600 regular rule file outside the repository")
    rules = [line.lower() for line in path.read_bytes().splitlines() if line]
    if not rules:
        sys.exit("Empty private rule file")
    return rules


def scan(data, rules, label, compressed=False):
    content = data.lower()
    hits = [str(i) for i, rule in enumerate(rules, 1) if rule in content]
    if hits:
        sys.exit(f"{label}: private rule number(s) " + ", ".join(hits))
    if HOME_PATH.search(data):
        sys.exit(f"{label}: absolute home path")
    if compressed and data.startswith(b"\x1f\x8b"):
        scan(gzip.decompress(data), rules, label)


def history(rules):
    for rev in git("rev-list", "--all").splitlines():
        scan(git("ls-tree", "-rz", "--name-only", rev), rules, "historical paths")
    scan(git("for-each-ref", "--format=%(refname)"), rules, "refs")
    objects = git("rev-list", "--objects", "--no-object-names", "--all").splitlines()
    for oid in set(objects):
        kind = git("cat-file", "-t", oid).strip()
        scan(git("cat-file", kind, oid), rules, "reachable object", compressed=kind == b"blob")
    with subprocess.Popen(["git", "log", "-p", "--all", "--binary"], cwd=ROOT,
                          stdout=subprocess.PIPE) as proc:
        # Do not print patch lines: a rejected line can itself contain a private value.
        # Overlap chunks so a rule crossing a read boundary is still detected.
        tail = b""
        overlap = max([256] + [len(rule) for rule in rules])
        while chunk := proc.stdout.read(1024 * 1024):
            scan(tail + chunk, rules, "binary patch")
            tail = (tail + chunk)[-overlap:]
        if proc.wait():
            sys.exit("git log failed")
    print(f"Checked reachable history ({len(set(objects))} objects) and binary patches")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args()
    rules = private_rules()
    names = manifest(ROOT)
    tracked = {p.decode() for p in git("ls-files", "-z").split(b"\0") if p}
    if tracked != names:
        sys.exit("Git index differs from the public manifest")
    for name in sorted(names):
        scan(name.encode(), rules, "public path")
        scan((ROOT/name).read_bytes(), rules, "public file", compressed=name.endswith(".gz"))
    verify()
    print("Public manifest, files and model index verified")
    if args.history:
        history(rules)
