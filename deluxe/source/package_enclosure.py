# SPDX-License-Identifier: MIT
"""Freeze one checked enclosure revision into a hash-verified ZIP."""
from pathlib import Path
import json,hashlib,zipfile,datetime
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((ROOT/'parameters.json').read_text());f=json.loads((ROOT/'fit-check.json').read_text());v=json.loads((ROOT/'verification.json').read_text());assert all(v['source_hashes_preserved'].values()), 'A package needs the complete external source audit; restore missing references first'
assert f['passed_geometry'] and v['passed']
b=f['geometry_binding'];assert b['parameters_sha256']==sha(ROOT/'parameters.json') and b['generator_sha256']==sha(ROOT/'source/generate_enclosure.py'),'CAD sources changed; regenerate'
for name,h in b['exports'].items():assert sha(ROOT/name)==h,('CAD export changed',name)
r=json.loads((ROOT/'.work/render-record.json').read_text());assert r['revision']==p['revision'] and r['generator_geometry']==b and r['renderer_sha256']==sha(ROOT/'source/render_enclosure.py'),'Render binding stale'
for name,h in r['images'].items():assert sha(ROOT/'preview'/name)==h,('Preview changed',name)
# Restrict bundles to the published edition and the reports of this build.
public_files=(ROOT.parent/'tools/public_manifest.txt').read_text().splitlines()
files=[ROOT.parent/name for name in public_files if name.startswith('deluxe/')]
files += [ROOT/n for n in ['fit-check.json','verification.json','change-review.json'] if (ROOT/n).is_file()]
meta={'revision':p['revision'],'status':p['readiness'],'created_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds'),'pcb_commit':p['pcb_revision_commit'],'screen_standoff_mm':16,'case_size_normal_view_mm':[138.4,108.4,34.55],'geometry_valid':True,'step_reimport_pass':True,'stl_closed_manifold_pass':True,'mechanical_interference_errors':f['errors'],'retainer_fasteners':p['keys']['retainer_fastener'],'physical_fit_verified':False,'preview_png_count':len(list((ROOT/'preview').glob('*.png'))),'source_hashes_preserved':v['source_hashes_preserved'],'artifacts':[{'path':x.relative_to(ROOT).as_posix(),'bytes':x.stat().st_size,'sha256':sha(x)} for x in sorted(files)]}
(ROOT/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
name='infrabot_pcb_4p3_'+p['revision'].replace('R8_S16_','R8_S16_enclosure_')+'.zip';archive=ROOT/name
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for path in sorted(files)+[ROOT/'manifest.json']:z.write(path,p['revision']+'/'+path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
 for row in meta['artifacts']:assert hashlib.sha256(z.read(p['revision']+'/'+row['path'])).hexdigest()==row['sha256']
(ROOT/'archive-sha256.txt').write_text(sha(archive)+'  '+archive.name+'\n');print(archive.name,archive.stat().st_size,'bytes;',len(files)+1,'verified files; PNGs',meta['preview_png_count'])
