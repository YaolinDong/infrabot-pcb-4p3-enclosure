# SPDX-License-Identifier: MIT
"""Freeze the checked two-part simple enclosure and its previews."""
from pathlib import Path
import json,hashlib,zipfile,datetime
R=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=json.loads((R/'parameters.json').read_text());f=json.loads((R/'fit-check.json').read_text());v=json.loads((R/'verification.json').read_text())
assert all(v['source_hashes_preserved'].values()), 'A package needs the complete external source audit; restore missing references first'
assert f['passed_geometry'] and v['passed'];assert len(list((R/'STL').glob('*.stl')))==2
change=json.loads((R/'change-review.json').read_text());assert change['passed'] and change['revision']==p['revision']
assert change['geometry_binding']==f['geometry_binding']
b=f['geometry_binding'];assert b['parameters_sha256']==sha(R/'parameters.json') and b['generator_sha256']==sha(R/'source/generate_simple.py')
for n,h in b['exports'].items():assert sha(R/n)==h,n
for n,h in b.get('support_sources',{}).items():assert sha(R/n)==h,n
render=json.loads((R/'.work/render-record.json').read_text());assert render['geometry_binding']==b and render['renderer_sha256']==sha(R/'source/render_simple.py')
for n,h in render['images'].items():assert sha(R/'preview'/n)==h,n
# Restrict bundles to the published edition and the reports of this build.
public_files=(R.parent/'tools/public_manifest.txt').read_text().splitlines()
files=[R.parent/name for name in public_files if name.startswith('simple/')]
files += [R/n for n in ['fit-check.json','verification.json','reuse-review.json','change-review.json']]
m={'revision':p['revision'],'status':'FIT_PROTOTYPE_NOT_PHYSICALLY_VERIFIED','created_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds'),'printed_parts':2,'screen_standoff_mm':16,'no_tapping_required':True,'printed_keycaps':0,'lightpipes':0,'internal_retainer_parts':0,'required_hardware':p['required_hardware'],'geometry_pass':True,'step_stl_pass':True,'actuator_and_finger_geometry_pass':True,'direct_LED_sightlines_pass':True,'physical_fit_verified':False,'preview_PNGs':len(list((R/'preview').glob('*.png'))),'artifacts':[{'path':x.relative_to(R).as_posix(),'bytes':x.stat().st_size,'sha256':sha(x)} for x in sorted(files)]}
(R/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');dest=R/('infrabot_pcb_4p3_'+p['revision']+'.zip')
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for file in sorted(files)+[R/'manifest.json']:z.write(file,p['revision']+'/'+file.relative_to(R).as_posix())
with zipfile.ZipFile(dest) as z:
 for row in m['artifacts']:assert hashlib.sha256(z.read(p['revision']+'/'+row['path'])).hexdigest()==row['sha256']
(R/'archive-sha256.txt').write_text(sha(dest)+'  '+dest.name+'\n');print(dest.name,dest.stat().st_size,'bytes;',len(files)+1,'files; PNGs',m['preview_PNGs'])
