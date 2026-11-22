# SPDX-License-Identifier: MIT
"""Check local CAD inputs and optionally the original measurement sources."""
import hashlib
import json
import os
from pathlib import Path


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def contained(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Input path escapes its declared root")
    return path


def audit_sources(root, sources, allow_missing_external):
    mapping = {}
    map_name = os.environ.get("ENCLOSURE_SOURCE_MAP")
    if map_name:
        map_file = Path(map_name).resolve()
        mapping = {key: map_file.parent / name
                   for key, name in json.loads(map_file.read_text()).items()}
    pcb = os.environ.get("PCB_WORKSPACE")
    checks, missing, errors = {}, [], []
    for key, source in sources.items():
        if pcb and "public_reference" in source:
            ref = source["public_reference"]
            path = contained(Path(pcb), ref["file"])
            if not path.is_file() or digest(path) != ref["sha256"]:
                errors.append("Invalid public board reference: " + key)
        if "file" in source:
            path = contained(root, source["file"])
        elif key in mapping:
            path = mapping[key]
        else:
            missing.append(key)
            checks[key] = None
            if not allow_missing_external:
                errors.append("External input unavailable: " + key)
            continue
        checks[key] = path.is_file() and digest(path) == source["sha256"]
        if not checks[key]:
            errors.append("Missing or changed input: " + key)
    return {"checks": checks, "missing": missing, "errors": errors,
            "passed": not errors, "complete": not missing and not errors}
