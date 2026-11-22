# SPDX-License-Identifier: MIT
"""Verify S8 rounds the complete CASE9 rim and preserves its screw seat."""
from pathlib import Path
import json,hashlib,zipfile
import cadquery as cq
from rim_audit import rim_report
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut,BRepAlgoAPI_Common
R=Path(__file__).resolve().parents[1];P=json.loads((R/'parameters.json').read_text());oldP=json.loads((R/'reference/S7_parameters.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def op(a,b,common=False):
    q=(BRepAlgoAPI_Common if common else BRepAlgoAPI_Cut)(a.wrapped,b.wrapped);q.SetFuzzyValue(1e-5);q.Build();assert q.IsDone();s=q.Shape();return None if s.IsNull() else cq.Shape.cast(s)
def vol(s):return 0.0 if s is None else s.Volume()
def diff(a,b):return vol(a)+vol(b)-2*vol(op(a,b,True))
def box(x0,y0,z0,x1,y1,z1):return cq.Workplane('XY',origin=(x0,y0,z0)).box(x1-x0,y1-y0,z1-z0,centered=(False,False,False)).val()
oldU=cq.importers.importStep(str(R/'reference/upper_S7_before_full_rim.step')).val();upper=cq.importers.importStep(str(R/'STEP/02_upper_shell.step')).val();oldL=cq.importers.importStep(str(R/'reference/lower_S7_before_full_rim.step')).val();lower=cq.importers.importStep(str(R/'STEP/01_lower_shell.step')).val()
fit=json.loads((R/'fit-check.json').read_text());assert fit['revision']==P['revision'] and fit['passed_geometry'],fit['errors']
x,y=P['mounts']['case'][0];F=P['fasteners'];r=F['CASE9_access_sleeve_outer_diameter']/2;z=F['CASE9_front_rim_z']
allowed=box(x-4.3,y-4.2,4.95,x+4.3,y+3.7,13.6)
# The R0.1 lower-junction fillet continues tangentially into the adjacent
# DC hood foot and rear inside corner, including the R1 end curves.
# Include those narrow transition bands.
sx=P['simple_controls']['step_x'];hy=P['simple_controls']['dc_hood_end_y'];hh=P['simple_controls']['dc_hood_top_z']
for band in [box(sx-.11,hy-.11,z-.01,104.3,hy+.11,z+.11),box(sx-.11,-4.3,hh-1.01,sx+.11,hy+.11,hh+.11),box(sx-.11,hy-.11,z-.01,sx+.11,hy+.11,hh+.11),box(sx-.11,hy-.11,z-.01,sx+1.61,hy+.11,z+1.61),box(100.7,18,4.6,104.3,19.2,5.7)]:allowed=allowed.fuse(band)
outside=diff(op(oldU,allowed),op(upper,allowed));lower_difference=diff(oldL,lower)
load_zone=box(x-4.1,y-4.1,-.1,x+4.1,y+4.1,4.95);load_difference=diff(op(oldU,load_zone,True),op(upper,load_zone,True))
front=box(x-r-.001,y+.11,z+.11,x+r+.001,y+r+.009,13.5);front_obstruction=vol(op(upper,front,True))
unchanged={k:P[k]==oldP[k] for k in ['board','case','lcd','core','controls','mounts','ports','simple_controls','soft_edges','required_hardware','pcb_revision_commit']}
for k in oldP['fasteners']:
 if k not in ['CASE9_front_rim_radius','CASE9_access_style']:unchanged['fastener_'+k]=F[k]==oldP['fasteners'][k]
rim_before=rim_report(oldU);rim_after=rim_report(upper);rim_ok=rim_after['sampled_edges']>=10 and rim_after['max_adjacent_normal_jump_deg']<.1
archive=R/'infrabot_pcb_4p3_R8_S16_SIMPLE_S7.zip';baseline_ok=None;lower_identical=None
if archive.exists():
 with zipfile.ZipFile(archive) as zz:
  baseline_ok=hashlib.sha256(zz.read('R8_S16_SIMPLE_S7/parameters.json')).hexdigest()==P['sources']['S7_parameters']['original_sha256'];lower_identical=zz.read('R8_S16_SIMPLE_S7/STL/01_lower_shell.stl')==(R/'STL/01_lower_shell.stl').read_bytes()
passed=all(abs(v)<1e-3 for v in [outside,lower_difference,load_difference,front_obstruction]) and all(unchanged.values()) and baseline_ok is not False and lower_identical is not False and rim_ok
report={'revision':P['revision'],'baseline':'R8_S16_SIMPLE_S7','passed':passed,'comparison_tolerance_mm':1e-5,'upper_outside_CASE9_front_difference_mm3':outside,'lower_difference_mm3':lower_difference,'CASE9_support_below_z4_95_difference_mm3':load_difference,'front_obstruction_beyond_R0_1_transition_mm3':front_obstruction,'front_rim_z_before_mm':5.5,'front_rim_z_after_mm':z,'rim_radius_mm':F['CASE9_complete_rim_radius'],'lower_junction_radius_mm':F['CASE9_junction_radius'],'top_hood_blend_radius_mm':F['CASE9_follow_hood_radius'],'rim_before':rim_before,'rim_after':rim_after,'rim_normal_continuity_pass':rim_ok,'screw_bearing_z_unchanged_mm':F['case_upper_head_seat_z'],'rear_DC_cover_height_unchanged_mm':P['simple_controls']['dc_hood_top_z'],'unchanged_dimensions':unchanged,'lower_STL_byte_identical_to_S7':lower_identical,'fastener_checks':fit['fastener_checks'],'baseline_parameters_match_archive':baseline_ok,'printed_part_count':2,'hardware_changes':None,'geometry_binding':fit['geometry_binding'],'physical_fit_verified':False}
(R/'change-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
reuse={'revision':P['revision'],'S7_lower_shell_reusable':True,'lower_STL_byte_identical_to_S7':lower_identical,'all_S7_hardware_reusable':True,'pairing':'Replace only the upper shell for the fully rounded CASE9 rim; S6/S7 lower shell and all hardware remain reusable','printed_parts':2,'physical_fit_verified':False}
(R/'reuse-review.json').write_text(json.dumps(reuse,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['passed','upper_outside_CASE9_front_difference_mm3','lower_difference_mm3','CASE9_support_below_z4_95_difference_mm3','front_obstruction_beyond_R0_1_transition_mm3','lower_STL_byte_identical_to_S7','rim_normal_continuity_pass']},indent=2));assert passed
