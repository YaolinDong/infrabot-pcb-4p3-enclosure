#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Restore exact immutable STEP inputs from their small tracked gzip files."""
from pathlib import Path
import gzip,hashlib,json,os,tempfile
ROOT=Path(__file__).resolve().parents[1]
def restore():
    projects=json.loads((ROOT/'projects.json').read_text())
    project=ROOT/projects['projects']['simple']['path']
    manifest=json.loads((project/'reference/inputs.json').read_text());created=0
    for row in manifest['inputs']:
        src=(project/row['compressed']).resolve();dst=(project/row['output']).resolve()
        assert src.is_relative_to(project) and dst.is_relative_to(project),'Reference path leaves project'
        if dst.exists():
            assert hashlib.sha256(dst.read_bytes()).hexdigest()==row['sha256'],f'Existing reference differs: {dst}'
            continue
        raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['compressed_sha256'],src
        data=gzip.decompress(raw);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],dst
        dst.parent.mkdir(parents=True,exist_ok=True)
        # A concurrent build must never see a partially unpacked reference.
        with tempfile.NamedTemporaryFile(dir=dst.parent,prefix='.restore-',suffix='.tmp',delete=False) as handle:
            temporary=Path(handle.name);handle.write(data)
        try:os.replace(temporary,dst)
        finally:temporary.unlink(missing_ok=True)
        created+=1
    print(f'References verified: {len(manifest["inputs"])}; restored: {created}')
if __name__=='__main__':restore()
