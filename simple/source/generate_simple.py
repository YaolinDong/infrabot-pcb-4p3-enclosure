# SPDX-License-Identifier: MIT
"""Two-piece enclosure for R8 / 16 mm LCD posts and exposed stock controls."""
from pathlib import Path
import json,math,hashlib
import cadquery as cq
from normalize_stl import normalize_stl
from rim_audit import rim_edges,rim_report
ROOT=Path(__file__).resolve().parents[1];P=json.loads((ROOT/'parameters.json').read_text());C=P['case'];S=P['simple_controls'];M=P['mounts'];B=P['board'];LCD=P['lcd']
F=P['fasteners']
assert B['size']==[100,130] and LCD['standoff']==16.0
assert S['deck_z']-S['deck_thickness']>=C['seam_z'], 'Control deck underside must stay at or above the matching lower-shell seam'
assert S['deck_thickness']>=2.0, 'Keep the control deck at least 2 mm thick'
D={};D['glass_top_z']=LCD['glass_top_z_measured'] if LCD['glass_top_z_measured'] is not None else sum(LCD[k] for k in ['standoff','pcb_thickness','lcm_thickness','touch_thickness','total_mount_adhesive_allowance']);D['face_bottom_z']=D['glass_top_z']+C['glass_gap'];D['face_top_z']=D['face_bottom_z']+C['face_thickness'];D['case_size_normal_view_mm']=[130+2*C['edge_margin'],100+2*C['edge_margin'],D['face_top_z']-C['bottom_z']]
for f in ['STEP','STL','preview','.work']:(ROOT/f).mkdir(exist_ok=True)
PARTS={};REFS={};COLORS={}
ROUND=P['soft_edges'];ROUND_OPS=[]
def box(x0,y0,z0,x1,y1,z1,r=0):
    s=cq.Workplane('XY',origin=((x0+x1)/2,(y0+y1)/2,z0)).box(x1-x0,y1-y0,z1-z0,centered=(True,True,False))
    if r:s=s.edges('|Z').fillet(r)
    return s.val()
def cyl(x,y,z0,z1,r):return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,y,z0))
def hexprism(x,y,z0,z1,af):return cq.Workplane('XY',origin=(x,y,z0)).polygon(6,af/math.cos(math.pi/6)).extrude(z1-z0).val()
def fuse(ss):return ss[0].fuse(*ss[1:]).clean() if len(ss)>1 else ss[0]
def cut(s,ts):return s.cut(*ts).clean() if ts else s
def bb(s):
    b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def near(a,b):return abs(a-b)<1e-5
def round_edges(s,label,radius,predicate):
    edges=[e for e in s.Edges() if predicate(e,e.BoundingBox())]
    assert edges,label+' selected no edges'
    before=s.Volume();print('Round',label,'R',radius,'edges',len(edges),flush=True)
    result=cq.Workplane(obj=s).newObject(edges).fillet(radius).val().clean()
    assert result.isValid() and len(result.Solids())==1,label
    ROUND_OPS.append({'label':label,'radius_mm':radius,'selected_edges':len(edges),'volume_change_mm3':result.Volume()-before})
    return result
def text(label,x,y,z,size=2,depth=.4):return cq.Workplane('XY').text(label,size,depth,combine=False,font='DejaVu Sans',kind='bold').val().rotate((0,0,0),(0,0,1),90).translate((x,y,z))
def ring(x0,y0,z0,x1,y1,z1,wall,r):return box(x0,y0,z0,x1,y1,z1,r).cut(box(x0+wall,y0+wall,z0-.1,x1-wall,y1-wall,z1+.1,max(.2,r-wall))).clean()
def add(name,shape,color,ref=False):
    assert shape.isValid() and shape.Volume()>0,name
    if not ref:assert len(shape.Solids())==1,name+' must be one printable solid'
    (REFS if ref else PARTS)[name]=shape;COLORS[name]=color

def ports():
    shapes=[]
    for p in P['ports']:
        lo,hi=p['span'];z0,z1=p['z']
        if p['side']=='+Y':shapes.append(box(lo,129.1,z0,hi,140,z1,.6))
        elif p['side']=='-Y':shapes.append(box(lo,-10,z0,hi,2,z1,.6))
        else:shapes.append(box(98.8,lo,z0,110,hi,z1,.6))
    return shapes

print('Lower shell: S4 seam retained, softened exterior bottom rim',flush=True)
a=C['edge_margin'];x0,y0,x1,y1=-a,-a,100+a,130+a;floor_top=C['bottom_z']+C['floor'];seam=C['seam_z'];fb=D['face_bottom_z'];ft=D['face_top_z'];deck=S['deck_z'];db=deck-S['deck_thickness'];sx=S['step_x'];hood=S['dc_hood_top_z'];hy=S['dc_hood_end_y']
lower=box(x0,y0,C['bottom_z'],x1,y1,seam,C['corner_radius'])
lower=round_edges(lower,'lower exterior bottom rim',ROUND['lower_bottom_radius'],lambda e,b:near(b.zmin,C['bottom_z']) and near(b.zmax,C['bottom_z']))
lower=lower.cut(box(x0+C['wall'],y0+C['wall'],floor_top,x1-C['wall'],y1-C['wall'],seam+.2,C['corner_radius']-C['wall']))
mounts=M['lcd']+M['core']+M['case'];bosses=[];holes=[]
for x,y in mounts:
    bosses.extend([cyl(x,y,floor_top-.1,M['boss_neck_bottom_z'],M['boss_lower_diameter']/2),cyl(x,y,M['boss_neck_bottom_z']-.1,-B['thickness'],M['boss_neck_diameter']/2)])
    holes.append(cyl(x,y,C['bottom_z']-.2,.3,M['screw_clearance']/2))
    if [x,y] in M['lcd']:
        holes.append(cyl(x,y,C['bottom_z']-.2,F['LCD_lower_head_seat_z'],F['head_clearance']/2))
    else:
        holes.append(hexprism(x,y,C['bottom_z']-.2,M['nut_top_z'],M['nut_af']))
lower=fuse([lower]+bosses);lower=cut(lower,holes+ports());lower=cut(lower,[box(-5.5,y,-4.8,0,y+9,-2.8,.6) for y in [25,41,57,73,89,105]])
for x,y in [(7,22),(7,108),(92,8),(92,123)]:lower=lower.cut(cyl(x,y,C['bottom_z']-.1,C['bottom_z']+.7,3.5))
add('01_lower_shell',lower,(.18,.22,.27))

print('One-piece upper: raised screen, lowered stock-control terrace',flush=True)
upper=box(x0,y0,seam,x1,y1,ft,C['corner_radius'])
upper=cut(upper,[box(sx,hy,deck,x1+1,y1+1,ft+1),box(sx,y0-1,hood,x1+1,hy,ft+1)])
# Round the outside before hollowing or cutting ports: interface apertures
# remain at their exact previous dimensions, and concave toes add material.
upper=round_edges(upper,'DC hood outer front vertical corner',ROUND['DC_hood_radius'],lambda e,b:near(b.xmin,x1) and near(b.xmax,x1) and near(b.ymin,hy) and near(b.ymax,hy))
upper=round_edges(upper,'long step base into control deck',ROUND['step_base_radius'],lambda e,b:near(b.zmin,deck) and near(b.zmax,deck) and near(b.xmin,sx) and near(b.xmax,sx))
upper=round_edges(upper,'DC hood exposed top rim',ROUND['DC_hood_radius'],lambda e,b:near(b.zmin,hood) and near(b.zmax,hood) and not (near(b.xmin,sx) and near(b.xmax,sx)))
upper=round_edges(upper,'screen outer rim and long step top',ROUND['screen_outer_and_step_top_radius'],lambda e,b:near(b.zmin,ft) and near(b.zmax,ft))
upper=round_edges(upper,'control terrace exterior rim',ROUND['control_outer_radius'],lambda e,b:near(b.zmin,deck) and near(b.zmax,deck) and ((near(b.xmin,x1) and near(b.xmax,x1)) or (near(b.ymin,y1) and near(b.ymax,y1)) or (b.xmin>x1-C['corner_radius']-.01 and b.ymin>y1-C['corner_radius']-.01)))
upper=cut(upper,[box(x0+C['wall'],y0+C['wall'],seam-.2,x1-C['wall'],y1-C['wall'],db,1.2),box(x0+C['wall'],y0+C['wall'],seam-.2,sx-C['wall'],y1-C['wall'],fb,1.2),box(sx-C['wall']-.1,y0+C['wall'],seam-.2,x1-C['wall'],hy-C['wall'],hood-S['deck_thickness'],1.2)])
lipouter=[x0+C['wall']+C['lip_clearance'],y0+C['wall']+C['lip_clearance'],x1-C['wall']-C['lip_clearance'],y1-C['wall']-C['lip_clearance']]
lip=ring(lipouter[0],lipouter[1],seam-C['lip_depth'],lipouter[2],lipouter[3],seam+.25,C['lip_wall'],.8)
bridge=ring(x0,y0,seam,x1,y1,seam+1.2,C['wall']+C['lip_clearance']+C['lip_wall'],C['corner_radius']);upper=fuse([upper,lip,bridge])
for x,y in M['lcd']:upper=upper.fuse(cyl(x,y,LCD['standoff']+LCD['pcb_thickness'],fb+.1,2.9))
# Integrated stiffening ribs do not add assembly parts.
for y in S['deck_rib_y']:upper=upper.fuse(box(sx-.4,y-.8,db-S['deck_rib_depth'],x1-C['wall']-C['lip_clearance']-.2,y+.8,db+.1))
# The panel is now approximately level with LED1. Only a rounded hole edge remains.
x,y=P['controls']['LED1'];wf=S['LED1_well_top_z']
if S['LED1_integrated_cup']:upper=upper.fuse(cyl(x,y,wf-S['LED1_well_floor'],db+.1,S['LED1_well_outer_diameter']/2))
# The tall POWER body needs an integral rounded surround above the low deck.
x,y=P['controls']['SW1'];pg=S['power_guard'];h=pg['outer_size']/2
power_guard=box(x-h,y-h,db-.1,x+h,y+h,pg['top_z'],pg['outer_corner_radius'])
power_guard=cq.Workplane(obj=power_guard).edges('>Z').fillet(pg['top_edge_radius']).val()
upper=upper.fuse(power_guard)
# Integral RESET guard keeps the bare original actuator 1 mm below its rim.
x,y=P['controls']['SW2'];guard=S['reset_guard'];upper=upper.fuse(cyl(x,y,db-.1,guard['top_z'],guard['outer_diameter']/2));upper=upper.clean()
wa,wb,wc,wd=LCD['lens_window_bbox'];e=LCD['window_extra_each_side'];window=[wa-e,wb-e,wc+e,wd+e]
upper=upper.cut(box(window[0],window[1],fb-.2,window[2],window[3],ft+.2,1)).clean()
edges=[q for q in upper.Edges() if abs(q.BoundingBox().zmin-ft)<1e-5 and abs(q.BoundingBox().zmax-ft)<1e-5 and window[0]-.1<=q.Center().x<=window[2]+.1 and window[1]-.1<=q.Center().y<=window[3]+.1]
assert edges,'Screen window edge selection'
upper=round_edges(upper,'screen window opening rim',ROUND['screen_window_radius'],lambda q,b:near(b.zmin,ft) and near(b.zmax,ft) and window[0]-.1<=q.Center().x<=window[2]+.1 and window[1]-.1<=q.Center().y<=window[3]+.1)
ts=ports()
for ref in ['SW1','SW2','SW3','SW4']:
    x,y=P['controls'][ref]
    if ref=='SW1':h=S['power_hole_size']/2;ts.append(box(x-h,y-h,db-.3,x+h,y+h,pg['top_z']+.3,.8))
    else:
        ts.append(cyl(x,y,db-.3,guard['top_z']+.3,(guard['inner_diameter'] if ref=='SW2' else S['momentary_hole_diameter'])/2))
        # 12 mm switch bodies need 0.5 mm vertical clearance under this low panel.
        h=S['momentary_body_relief_size']/2
        ts.append(box(x-h,y-h,db-.3,x+h,y+h,S['momentary_body_relief_top_z'],.3))
x,y=P['controls']['LED1'];r0=S['LED1_hole_diameter']/2;r1=S['LED1_well_inner_diameter']/2;bv=S['LED1_profile_bottom_tangent_mm'];th=S['LED1_profile_top_tangent_mm'];height=deck-wf
# A revolved G1 Bezier blend joins the small bore vertically and the
# operating terrace horizontally. This removes the two abrupt well edges.
hole_bottom=min(db,wf-S['LED1_well_floor'])-.2
profile=(cq.Workplane('XZ').moveTo(0,hole_bottom)
 .lineTo(r0,hole_bottom).lineTo(r0,wf)
 .bezier([(r0,wf+bv),(r1-th,deck),(r1,deck)],includeCurrent=True)
 .lineTo(r1,deck+.3).lineTo(0,deck+.3).close())
bowl_cut=profile.revolve(360,(0,0),(0,1)).val().translate((x,y,0));assert bowl_cut.isValid();ts.append(bowl_cut)
x,y=P['controls']['LED2'];ts.append(cyl(x,y,db-.3,deck+.3,S['LED2_hole_diameter']/2))
for x,y in M['lcd']:ts += [cyl(x,y,16,ft+.2,M['screw_clearance']/2),cyl(x,y,ft-M['front_head_recess'],ft+.2,M['front_head_diameter']/2)]
upper=cut(upper,ts)
gx,gy=P['controls']['SW2']
upper=round_edges(upper,'RESET inner and outer mouth',ROUND['RESET_rim_radius'],lambda e,b:near(b.zmin,guard['top_z']) and near(b.zmax,guard['top_z']) and abs(e.Center().x-gx)<.1 and abs(e.Center().y-gy)<.1)
for ref,label in [('SW1','POWER'),('SW2','RESET'),('SW3','STOP'),('SW4','RESUME'),('LED1','PWR'),('LED2','STATUS')]:
    _,y=P['controls'][ref];upper=upper.cut(text(label,80.5,y,deck-.3,1.65 if ref.startswith('LED') else 2.0,.5))
upper=upper.cut(text('INFRABOT',70.5,66,ft-.35,2.6,.5)).clean()

# Right-side fasteners clamp through integral supports onto the PCB, which is
# supported by the existing lower bosses. No tall screw bends the bare panel.
for x,y in M['top_case_fasteners']:upper=upper.fuse(cyl(x,y,0,db+.2,F['case_support_diameter']/2),tol=1e-5).clean()
# CASE9 crosses the DC hood edge: add a closed access sleeve for its deep head.
x,y=M['case'][0];sleeve=cyl(x,y,db,F['CASE9_access_sleeve_top_z'],F['CASE9_access_sleeve_outer_diameter']/2)
sleeve=cq.Workplane(obj=sleeve).edges('>Z').fillet(F['CASE9_access_sleeve_edge_radius']).val();upper=upper.fuse(sleeve,tol=1e-5).clean()
case_cuts=[]
for x,y in M['top_case_fasteners']:
    case_cuts += [cyl(x,y,-.2,hood+.3,M['screw_clearance']/2),cyl(x,y,F['case_upper_head_seat_z'],hood+.3,F['head_clearance']/2)]
upper=cut(upper,case_cuts)
# CASE9 does not need a tall front tube: the screw bears at Z3.5, well below
# the DC cover. Remove the front half down to the operating deck, retaining
# the rear barrier next to the DC connector. Avoid the POWER guard at Y23.
if F['CASE9_front_open']:
    x,y=M['case'][0];front_z=F['CASE9_front_rim_z'];outer_r=F['CASE9_access_sleeve_outer_diameter']/2;bore_r=F['head_clearance']/2
    # Place the cylindrical BRep seam in the removed front half, rather than
    # on an upright rim edge. Rebuilding this face does not change its radius.
    plug=cyl(x,y,F['case_upper_head_seat_z'],hood,bore_r+.05)
    upper=upper.fuse(plug,tol=1e-5).clean()
    bore=cyl(x,y,F['case_upper_head_seat_z'],hood+.3,bore_r).rotate((x,y,0),(x,y,1),F['CASE9_bore_seam_rotation_deg'])
    upper=upper.cut(bore).clean()
    front_cut=box(x-outer_r-.3,y,front_z,x+outer_r+.3,y+outer_r+.01,hood+.3)
    upper=upper.cut(front_cut).clean()
    # The old collar tips stood above the hood's existing R1 front edge.
    # Trim them to that same quarter-circle envelope before rounding the rim.
    cr=F['CASE9_follow_hood_radius'];cy=y-cr;cz=hood-cr
    cap=(cq.Workplane('YZ',origin=(x-outer_r-.3,0,0)).moveTo(cy,hood)
      .threePointArc((cy+cr/math.sqrt(2),cz+cr/math.sqrt(2)),(y,cz))
      .lineTo(y,hood+.6).lineTo(cy,hood+.6).close().extrude(2*(outer_r+.3))).val()
    upper=upper.cut(cap).clean()
    upper=round_edges(upper,'CASE9 complete open-pocket rim: front, both uprights and top',F['CASE9_complete_rim_radius'],
      lambda e,b:b.xmin>=x-bore_r-.01 and b.xmax<=x+bore_r+.01 and b.ymin>=y-bore_r-.01 and b.ymax<=y+bore_r+.01 and b.zmin>=front_z-.01 and b.zmax<=hood+.01)
    # Blend the small meeting edges between the upright and floor fillets.
    junctions=[row['edge'].hashCode() for row in rim_edges(upper,(x,y),bore_r,front_z,hood) if row['normal_jump_deg']>1]
    assert len(junctions)==4,'Inspect unexpected CASE9 rim junctions'
    upper=round_edges(upper,'CASE9 lower rim junction transitions',F['CASE9_junction_radius'],lambda e,b:e.hashCode() in junctions)
    # Standardize the fillet intersection curves through STEP before later
    # Boolean clearance checks and section cuts. Preserve the one-solid volume.
    stabilized_path=ROOT/'.work/upper-rim-standardized.step';before_volume=upper.Volume()
    cq.exporters.export(upper,str(stabilized_path));upper=cq.importers.importStep(str(stabilized_path)).val()
    assert upper.isValid() and len(upper.Solids())==1 and abs(upper.Volume()-before_volume)<1e-3
assert upper.isValid() and len(upper.Solids())==1, 'Right-side support union must be one valid solid'
add('02_upper_shell',upper,(.78,.81,.84))

print('Reference envelopes and native LED2 geometry',flush=True)
pcb=box(0,0,-B['thickness'],100,130,0,.25)
for x,y in mounts:pcb=pcb.cut(cyl(x,y,-1.8,.1,1.7 if [x,y] in M['lcd'] else 1.6))
add('REF_base_PCB',pcb.clean(),(.13,.36,.24),True)
pa,pb,pc,pd=LCD['pcb_bbox'];lp=box(pa,pb,16,pc,pd,17.6,1.5)
for x,y in M['lcd']:lp=lp.cut(cyl(x,y,15.9,17.7,1.5))
add('REF_LCD_PCB',lp.clean(),(.12,.36,.23),True)
ga,gb,gc,gd=LCD['glass_bbox'];add('REF_LCD_body',box(ga,gb,17.6,gc,gd,D['glass_top_z']-1.05,.4),(.25,.28,.30),True);add('REF_touch_glass',box(ga,gb,D['glass_top_z']-1.05,gc,gd,D['glass_top_z'],.4),(.055,.075,.09),True)
a,b,c,d=LCD['lens_window_bbox'];add('REF_visible_screen',box(a,b,D['glass_top_z']+.001,c,d,D['glass_top_z']+.025,.2),(.12,.27,.33),True)
a,b,c,d=P['core']['bbox'];core=box(a,b,6,c,d,7.6,2)
for x,y in M['core']:core=core.cut(cyl(x,y,5.9,7.8,1.5))
add('REF_core_PCB',core.clean(),(.12,.30,.23),True);add('REF_core_components',box(22,40,7.6,57,77,P['core']['max_component_top_z'],1),(.12,.15,.17),True)
a,b,c,d=LCD['header_bbox'];add('REF_unused_LCD_header',box(a,b,16-LCD['header_protrusion'],c,d,16,.1),(.26,.27,.28),True)
for ref,bounds in {'J1':[85.87,4.15,0,100.13,13.15,11.0],'J2':[10.48,109.05,0,26.52,130.53,13.84],'J3':[41.53,122.51,0,50.47,130,3.25],'J4':[67.46,126.25,0,72.54,128.75,8.5],'J5':[52.62,122.37,0,64.33,129.53,8.7],'J6':[28.65,.7,0,41.35,9.54,2.54]}.items():add('REF_'+ref,box(*bounds,.15),(.56,.58,.60) if ref in ['J2','J3'] else (.15,.19,.21),True)
for ref in ['SW1','SW2','SW3','SW4']:
    x,y=P['controls'][ref];power=ref=='SW1';h=4.25 if power else 6;bh=8.5 if power else 3.5
    add('REF_'+ref+'_body',box(x-h,y-h,0,x+h,y+h,bh,.3),(.09,.11,.12),True)
    act=box(x-1.95,y-1.9,bh,x+1.95,y+1.9,S['power_height'],.1) if power else cyl(x,y,bh,S['momentary_height'],S['momentary_diameter']/2)
    add('REF_'+ref+'_actuator',act,(.85,.86,.83) if power else (.09,.11,.12),True)
x,y=P['controls']['LED1'];lt=S['LED1_top_z'];led=fuse([cyl(x,y,.2,.8,1.95),cyl(x,y,.7,lt-1.5,1.5),cq.Solid.makeSphere(1.5,cq.Vector(x,y,lt-1.5))]);add('REF_LED1',led,(.85,.035,.025),True)
x,y=P['controls']['LED2'];led2=cq.importers.importStep(str(ROOT/'reference/LED2_REFERENCE.step')).val().translate((x,y,S['LED2_top_z']-11.7));add('REF_LED2',led2,(.73,.76,.72),True)
# Four female-female spacers, secured by separate upper and lower screws.
for i,(x,y) in enumerate(M['lcd'],1):
    depth=LCD['standoff_thread_depth_model'];post=hexprism(x,y,0,16,5.5).cut(cyl(x,y,16-depth,16.1,1.5),cyl(x,y,-.1,depth,1.5))
    add(f'REF_standoff16_{i}',post,(.69,.52,.22),True)
    seat=ft-M['front_head_recess'];screw=fuse([cyl(x,y,seat-F['LCD_upper_screw_length'],seat,1.5),cyl(x,y,seat,seat+F['head_height'],F['head_diameter']/2)])
    add(f'REF_lid_screw_{i}',screw,(.64,.66,.68),True)
    seat=F['LCD_lower_head_seat_z'];screw=fuse([cyl(x,y,seat,seat+F['LCD_lower_screw_length'],1.5),cyl(x,y,seat-F['head_height'],seat,F['head_diameter']/2)])
    add(f'REF_bottom_LCD_screw_{i}',screw,(.64,.66,.68),True)
for i,(x,y) in enumerate(M['case'],1):
    seat=F['case_upper_head_seat_z'];add(f'REF_case_lid_screw_{i}',fuse([cyl(x,y,seat-F['case_upper_screw_length'],seat,1.5),cyl(x,y,seat,seat+F['head_height'],F['head_diameter']/2)]),(.64,.66,.68),True)
for i,(x,y) in enumerate(M['required_nut_positions'],1):add(f'REF_base_nut_{i}',hexprism(x,y,M['nut_top_z']-2.4,M['nut_top_z'],5.5).cut(cyl(x,y,-6,0,1.5)),(.66,.67,.64),True)

print('Check shell clearance, stock actuator travel and direct visibility',flush=True)
report={'revision':P['revision'],'readiness':P['readiness'],'printed_parts':2,'errors':[],'solid_checks':{},'intersections':[],'actuator_checks':[],'LED_visibility_checks':[],'derived':D,'hardware':P['required_hardware'],'rounding_operations':ROUND_OPS,'physical_fit_verified':False}
report['CASE9_rim_audit']=rim_report(upper)
if report['CASE9_rim_audit']['sampled_edges']<10 or report['CASE9_rim_audit']['max_adjacent_normal_jump_deg']>.1:report['errors'].append('CASE9 exposed rim retains a sharp junction')
def overlap(a,b):
    aa=bb(a);ab=bb(b)
    if any(aa[i+3]<=ab[i]+1e-6 or ab[i+3]<=aa[i]+1e-6 for i in range(3)):return 0.0
    return a.intersect(b).Volume()
for n,s in (PARTS|REFS).items():report['solid_checks'][n]={'valid':s.isValid(),'solid_count':len(s.Solids()),'volume_mm3':s.Volume(),'bounds_mm':bb(s)}
v=overlap(lower,upper);report['intersections'].append({'a':'lower','b':'upper','volume_mm3':v})
if v>1e-4:report['errors'].append('Upper/lower shell overlap')
for n,s in PARTS.items():
    for ref,shape in REFS.items():
        vol=overlap(s,shape);report['intersections'].append({'a':n,'b':ref,'volume_mm3':vol})
        if vol>1e-4:report['errors'].append(f'{n} / {ref}: {vol:.6f} mm3')
for ref in ['SW1','SW2','SW3','SW4']:
    x,y=P['controls'][ref];power=ref=='SW1';height=S['power_height'] if power else S['momentary_height'];travel=S['power_travel_max'] if power else S['momentary_travel_max'];collisions=[]
    for k in range(9):
        t=travel*k/8;act=REFS['REF_'+ref+'_actuator'].translate((0,0,-t));finger=cq.Solid.makeSphere(S['finger_probe_radius'],cq.Vector(x,y,height-t+S['finger_probe_radius']),angleDegrees1=-90,angleDegrees2=90)
        for label,shape in [('actuator',act),('8mm-radius fingertip proxy',finger)]:
            vol=overlap(upper,shape)
            if vol>1e-4:collisions.append({'state':k,'object':label,'volume_mm3':vol})
    row={'ref':ref,'free_actuator_top_z':height,'pressed_top_z':height-travel,'travel_checked_mm':travel,'deck_z':deck,'protrusion_above_local_deck_free_mm':height-deck,'protrusion_pressed_mm':height-travel-deck,'collisions':collisions}
    if power:row.update({'POWER_guard_top_z':pg['top_z'],'protrusion_above_guard_free_mm':height-pg['top_z'],'protrusion_above_guard_pressed_mm':height-travel-pg['top_z']})
    if ref=='SW2':row['RESET_guard_recess_free_mm']=guard['top_z']-height;row['RESET_guard_recess_pressed_mm']=guard['top_z']-(height-travel)
    report['actuator_checks'].append(row)
    if collisions:report['errors'].append(ref+' contact/finger proxy collides')
for ref in ['LED1','LED2']:
    x,y=P['controls'][ref];z=S[ref+'_top_z']+.05;collisions=[]
    for angle,az in [(0,0)]+[(S['direct_LED_sightline_angle_deg'],a) for a in [0,90,180,270]]:
        ang=math.radians(angle);phi=math.radians(az);direction=cq.Vector(math.sin(ang)*math.cos(phi),math.sin(ang)*math.sin(phi),math.cos(ang));length=(ft+8-z)/math.cos(ang)
        ray=cq.Solid.makeCylinder(.08,length,cq.Vector(x,y,z),direction);vol=overlap(upper,ray)
        if vol>1e-4:collisions.append({'tilt_deg':angle,'azimuth_deg':az,'volume_mm3':vol})
    localrim=wf if ref=='LED1' else deck
    report['LED_visibility_checks'].append({'ref':ref,'top_z':S[ref+'_top_z'],'local_rim_z':localrim,'nominal_head_protrusion_mm':S[ref+'_top_z']-localrim,'sightline_tilt_checked_deg':S['direct_LED_sightline_angle_deg'],'collisions':collisions})
    if collisions:report['errors'].append(ref+' direct sightline blocked')
report['clearances_mm']={'screen_PCB_to_RJ45_nominal':16-13.84,'unused_LCD_header_to_bare_SWD_nominal':16-8.5-2.54,'LCD_PCB_edge_to_step_wall':sx-C['wall']-LCD['pcb_bbox'][2],'DC_body_to_hood_inside':hood-S['deck_thickness']-11.0,'glass_to_upper_face_inside':C['glass_gap']}
report['clearances_mm'].update({'momentary_body_to_relief_roof':S['momentary_body_relief_top_z']-3.5,'momentary_relief_remaining_panel_thickness':deck-S['momentary_body_relief_top_z'],'LED1_tip_above_deck':S['LED1_top_z']-deck,'lower_seam_to_deck_inside':db-seam})
if min(report['clearances_mm'][k] for k in ['momentary_body_to_relief_roof','lower_seam_to_deck_inside'])<.3:report['errors'].append('Insufficient low-deck clearance margin')
if report['clearances_mm']['momentary_relief_remaining_panel_thickness']<1.5:report['errors'].append('Momentary switch relief roof too thin')
upper_tip=ft-M['front_head_recess']-F['LCD_upper_screw_length'];lower_tip=F['LCD_lower_head_seat_z']+F['LCD_lower_screw_length']
report['fastener_checks']={'LCD_upper_thread_engagement_mm':16-upper_tip,'LCD_lower_thread_engagement_mm':lower_tip,'screw_tip_separation_in_16mm_post_mm':upper_tip-lower_tip,'required_effective_thread_depth_each_end_mm':LCD['standoff_min_effective_thread_depth_required'],'actual_thread_depth_verified':False,'LCD_bottom_head_recess_from_case_bottom_mm':F['LCD_lower_head_seat_z']-F['head_height']-C['bottom_z'],'CASE_screw_tip_z':F['case_upper_head_seat_z']-F['case_upper_screw_length'],'CASE_screw_extension_past_nut_mm':M['nut_top_z']-2.4-(F['case_upper_head_seat_z']-F['case_upper_screw_length']),'CASE9_access_sleeve_wall_mm':(F['CASE9_access_sleeve_outer_diameter']-F['head_clearance'])/2,'driver_access':[]}
if max(16-upper_tip,lower_tip)+.5>LCD['standoff_min_effective_thread_depth_required']:report['errors'].append('Spacer screw engagement exceeds required effective thread depth')
if upper_tip-lower_tip<1:report['errors'].append('Opposing spacer screws too close')
report['fastener_checks'].update({'CASE9_access_style':F['CASE9_access_style'],'CASE9_front_rim_z':F['CASE9_front_rim_z'],'CASE9_front_wall_height_reduction_mm':F['CASE9_access_sleeve_top_z']-F['CASE9_front_rim_z'],'CASE9_front_mouth_radius_mm':F['CASE9_front_rim_radius']})
# Straight driver probes start above each head, so they do not include the head.
for i,(x,y) in enumerate(M['case'],9):
    probe=cyl(x,y,F['case_upper_head_seat_z']+F['head_height']+.05,ft+8,F['driver_probe_diameter']/2);vol=overlap(upper,probe)
    report['fastener_checks']['driver_access'].append({'ref':'CASE'+str(i),'probe_diameter_mm':F['driver_probe_diameter'],'shell_collision_mm3':vol})
    if vol>1e-4:report['errors'].append('CASE driver access blocked')
# Hardware-to-electronics and mating spacers are checked separately from shells.
report['hardware_intersections']=[]
hardware=[n for n in REFS if 'screw' in n];others=[n for n in REFS if 'screw' not in n]
for n in hardware:
    for other in others:
        vol=overlap(REFS[n],REFS[other])
        if vol>1e-4:report['hardware_intersections'].append({'a':n,'b':other,'volume_mm3':vol})
if report['hardware_intersections']:report['errors'].append('Hardware intersects reference assembly')
report['passed_geometry']=not report['errors']
(ROOT/'.work/fit_pre_export.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Export two shells and reference assemblies',flush=True)
assy=cq.Assembly(name=P['revision']+'_shells');fit=cq.Assembly(name=P['revision']+'_fit_reference')
meshes={};report['STL_normalization']={}
for name,s in PARTS.items():
    cq.exporters.export(s,str(ROOT/'STEP'/(name+'.step')))
    printing=s.rotate((0,0,0),(1,0,0),180) if name=='02_upper_shell' else s
    b=printing.BoundingBox();printing=printing.translate((-b.xmin,-b.ymin,-b.zmin));cq.exporters.export(printing,str(ROOT/'STL'/(name+'.stl')),tolerance=.035,angularTolerance=.12)
    report['STL_normalization'][name]=normalize_stl(ROOT/'STL'/(name+'.stl'))
    assy.add(s,name=name,color=cq.Color(*COLORS[name]));fit.add(s,name=name,color=cq.Color(*COLORS[name]))
for n,s in REFS.items():fit.add(s,name=n,color=cq.Color(*COLORS[n]))
assy.export(str(ROOT/'STEP/00_shells_assembly.step'));fit.export(str(ROOT/'STEP/00_fit_reference_assembly.step'))
for n,s in (PARTS|REFS).items():
    vs,fs=s.tessellate(.05,.16);meshes[n]={'v':[v.toTuple() for v in vs],'f':fs,'color':COLORS[n],'bounds':bb(s)}
(ROOT/'.work/meshes.json').write_text(json.dumps(meshes,separators=(',',':')))
sections={}
for label,y in [('POWER',30),('RESET',57),('LED1',43),('LED2',106),('LCD_POST',9.9),('CASE9',19),('CASE10',75),('CASE11',106)]:
    clip=box(-5,y-.15,-10,105,y+.15,32);items={}
    for n,s in (PARTS|REFS).items():
        b=bb(s)
        if b[1]>y+.15 or b[4]<y-.15:continue
        q=s.intersect(clip)
        if q.Volume()<1e-7:continue
        vs,fs=q.tessellate(.04,.16);items[n]={'v':[v.toTuple() for v in vs],'f':fs,'color':COLORS[n],'bounds':bb(q)}
    sections[label]=items
# Same-size CAD crops for the LED1 before/after comparison.
before=cq.importers.importStep(str(ROOT/'reference/LED1_S1_before_patch.step')).val();clip=box(82,35.5,1.5,97,50.5,11)
after=upper.intersect(clip);details={}
for label,shape in [('before',before),('after',after)]:
    items={}
    for name,part,color in [('upper_patch',shape,COLORS['02_upper_shell']),('LED1',REFS['REF_LED1'],COLORS['REF_LED1'])]:
        vs,fs=part.tessellate(.025,.10);items[name]={'v':[v.toTuple() for v in vs],'f':fs,'color':color,'bounds':bb(part)}
    details[label]=items
(ROOT/'.work/bowl-detail-meshes.json').write_text(json.dumps(details,separators=(',',':')))
report['LED1_bowl_profile']={'style':S['LED1_well_style'],'mouth_diameter_mm':2*r1,'bore_diameter_mm':2*r0,'lower_transition_z':wf,'deck_z':deck,'LED_height_preserved':True,'deck_height_mm':deck,'control_points_rz':[[r0,wf],[r0,wf+bv],[r1-th,deck],[r1,deck]],'bore_tangent_vertical':True,'deck_tangent_horizontal':True}
(ROOT/'.work/section-meshes.json').write_text(json.dumps(sections,separators=(',',':')))
report['geometry_binding']={'parameters_sha256':hashlib.sha256((ROOT/'parameters.json').read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'exports':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder,suffix in [('STEP','*.step'),('STL','*.stl')] for p in (ROOT/folder).glob(suffix)}}
report['geometry_binding']['support_sources']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['source/normalize_stl.py','source/rim_audit.py']}
(ROOT/'fit-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(ROOT/'.work/resolved-parameters.json').write_text(json.dumps(P|{'derived':D},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed_geometry':report['passed_geometry'],'errors':report['errors'],'printed_parts':2,'actuator_checks':report['actuator_checks'],'LED_visibility_checks':report['LED_visibility_checks']},ensure_ascii=False,indent=2),flush=True)
