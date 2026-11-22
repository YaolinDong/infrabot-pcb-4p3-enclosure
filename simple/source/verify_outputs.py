# SPDX-License-Identifier: MIT
"""Independent STEP reload, STL manifold and board pin-envelope checks."""
from pathlib import Path
import json,struct,hashlib
import argparse
from source_audit import audit_sources
ap=argparse.ArgumentParser();ap.add_argument("--allow-missing-external",action="store_true");args=ap.parse_args()
import cadquery as cq
import numpy as np
ROOT=Path(__file__).resolve().parents[1];report={'step':[],'stl':[],'pin_collisions':[],'errors':[]};shapes={}
for p in sorted((ROOT/'STEP').glob('*.step')):
    if p.name.startswith('00_'):continue
    s=cq.importers.importStep(str(p)).val();solids=s.Solids();row={'file':p.name,'valid':s.isValid(),'solid_count':len(solids),'volume_mm3':s.Volume()};report['step'].append(row);shapes[p.stem]=s
    if not row['valid'] or len(solids)!=1 or s.Volume()<=0:report['errors'].append('STEP '+p.name)
for p in sorted((ROOT/'STL').glob('*.stl')):
    raw=p.read_bytes();n=struct.unpack('<I',raw[80:84])[0];assert len(raw)==84+50*n,p.name+' not binary STL'
    data=np.frombuffer(raw[84:],dtype=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')]))['v'].astype(np.float64)
    points=data.reshape(-1,3);verts,ids=np.unique(np.round(points,5),axis=0,return_inverse=True);f=ids.reshape(-1,3);edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);unique,counts=np.unique(edges,axis=0,return_counts=True)
    volume=np.einsum('ij,ij->i',data[:,0],np.cross(data[:,1],data[:,2])).sum()/6
    row={'file':p.name,'triangles':n,'vertices_welded_1e_5mm':len(verts),'nonmanifold_edges':int(np.count_nonzero(counts!=2)),'signed_volume_mm3':float(volume),'min_z_mm':float(points[:,2].min())};report['stl'].append(row)
    if row['nonmanifold_edges'] or abs(volume)<1e-5 or abs(row['min_z_mm'])>.0001:report['errors'].append('STL '+p.name)
base=shapes['01_lower_shell']
for pin in json.loads((ROOT/'source/pcb-pin-envelopes.json').read_text()):
    x,y=pin['xy_mm'];s=cq.Solid.makeCylinder(pin['radius_mm'],pin['top_z']-pin['bottom_z'],cq.Vector(x,y,pin['bottom_z']));volume=base.intersect(s).Volume()
    if volume>1e-4:report['pin_collisions'].append({'ref':pin['ref'],'pin':pin['pin'],'volume_mm3':volume,'xy_mm':[x,y]})
if report['pin_collisions']:report['errors'].append('PCB pin/peg envelope touches lower shell')
p=json.loads((ROOT/'parameters.json').read_text());audit=audit_sources(ROOT,p['sources'],args.allow_missing_external)
report['source_validation']=audit;report['source_hashes_preserved']=audit['checks'];report['errors'].extend(audit['errors'])
binding=json.loads((ROOT/'fit-check.json').read_text())['geometry_binding']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if sha(ROOT/'parameters.json')!=binding['parameters_sha256'] or sha(ROOT/'source/generate_simple.py')!=binding['generator_sha256']:report['errors'].append('stale parameters or generator: regenerate CAD')
for name,h in binding['exports'].items():
    if sha(ROOT/name)!=h:report['errors'].append('export changed: '+name)
for name,h in binding.get('support_sources',{}).items():
    if sha(ROOT/name)!=h:report['errors'].append('export helper changed: '+name)
report['geometry_binding_pass']=not report['errors']
report['passed']=not report['errors'];(ROOT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if report['passed'] else 1)
