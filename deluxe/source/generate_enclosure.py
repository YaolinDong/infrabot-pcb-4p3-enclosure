# SPDX-License-Identifier: MIT
"""R8 16 mm screen enclosure; CadQuery 2.8, dimensions in mm.

Source design only. Does not edit the EasyEDA project. parameters.json owns the
fit assumptions; inspect fit-check.json and print the coupon before full shells.
"""
from pathlib import Path
import argparse,json,math,hashlib,time
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'parameters.json').read_text());C=P['case'];K=P['keys'];M=P['mounts'];LP=P['lightpipes'];B=P['board'];D=P['derived']
assert B['size']==[100,130] and P['lcd']['standoff']==16.0, 'This template is specific to R8 and 16 mm standoffs'
# Recompute dependent heights after a user edits the measured glass height.
D['glass_top_z']=P['lcd']['glass_top_z_measured'] if P['lcd']['glass_top_z_measured'] is not None else sum(P['lcd'][k] for k in ['standoff','pcb_thickness','lcm_thickness','touch_thickness','total_mount_adhesive_allowance'])
D['face_bottom_z']=D['glass_top_z']+C['glass_gap'];D['face_top_z']=D['face_bottom_z']+C['face_thickness'];D['flange_top_z']=D['face_bottom_z']-K['flange_top_gap'];D['flange_bottom_z']=D['flange_top_z']-K['flange_thickness'];D['retainer_top_z']=D['flange_bottom_z']-K['momentary_stroke'];D['retainer_bottom_z']=D['retainer_top_z']-K['retainer_thickness'];D['external_case_size_mm']=[100+2*C['edge_margin'],130+2*C['edge_margin'],D['face_top_z']-C['bottom_z']]
for name in ['STEP','STL','preview','.work']:(ROOT/name).mkdir(exist_ok=True)
PARTS={};REFS={};COLORS={};NOTES={};MESH={}

def box(x0,y0,z0,x1,y1,z1,r=0):
    assert x1>x0 and y1>y0 and z1>z0
    w=cq.Workplane('XY').workplane(offset=z0).center((x0+x1)/2,(y0+y1)/2).box(x1-x0,y1-y0,z1-z0,centered=(True,True,False))
    if r:w=w.edges('|Z').fillet(r)
    return w.val()

def cyl(x,y,z0,z1,r):return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,y,z0))
def hexprism(x,y,z0,z1,af):return cq.Workplane('XY',origin=(x,y,z0)).polygon(6,af/math.cos(math.pi/6)).extrude(z1-z0).val()
def flat_x_hex(x,y,z0,z1,af):return hexprism(x,y,z0,z1,af).rotate((x,y,0),(x,y,1),30)
def fuse(shapes):return shapes[0].fuse(*shapes[1:]).clean() if len(shapes)>1 else shapes[0]
def cut(s,tools):return s.cut(*tools).clean() if tools else s

def ring_box(x0,y0,z0,x1,y1,z1,wall,r):return box(x0,y0,z0,x1,y1,z1,r).cut(box(x0+wall,y0+wall,z0-.1,x1-wall,y1-wall,z1+.1,max(.2,r-wall))).clean()
def text_shape(label,x,y,z,size=2.8,depth=.35,rot=90):
    s=cq.Workplane('XY').text(label,size,depth,combine=False,font='DejaVu Sans',kind='bold').val()
    return s.rotate((0,0,0),(0,0,1),rot).translate((x,y,z))

def add(name,s,color,note='',reference=False):
    assert s.isValid(),name+' invalid';assert s.Volume()>0,name+' empty'
    if not reference and len(s.Solids())!=1:
        print('DISCONNECTED',name,[(round(z.Volume(),6),[round(t,4) for t in bb(z)]) for z in s.Solids()],flush=True)
        raise ValueError(name+' must be one printable solid')
    dest=REFS if reference else PARTS;dest[name]=s;COLORS[name]=color;NOTES[name]=note

def bb(s):
    b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]

def port_tools():
    a=[]
    for p in P['ports']:
        lo,hi=p['span'];z0,z1=p['z']
        if p['side']=='+Y':a.append(box(lo,129.1,z0,hi,140,z1,.6))
        elif p['side']=='-Y':a.append(box(lo,-10,z0,hi,2,z1,.6))
        else:a.append(box(98.8,lo,z0,110,hi,z1,.6))
    return a

print('Building lower shell',flush=True)
margin=C['edge_margin'];outer=(-margin,-margin,100+margin,130+margin);x0,y0,x1,y1=outer;floor_top=C['bottom_z']+C['floor'];seam=C['seam_z'];fb=D['face_bottom_z'];ft=D['face_top_z']
lower=box(x0,y0,C['bottom_z'],x1,y1,seam,C['corner_radius']);lower=lower.cut(box(x0+C['wall'],y0+C['wall'],floor_top,x1-C['wall'],y1-C['wall'],seam+.2,C['corner_radius']-C['wall']))
mounts=M['lcd']+M['core']+M['case'];bosses=[];holes=[]
for x,y in mounts:
    bosses.extend([cyl(x,y,floor_top-.1,M['boss_neck_bottom_z'],M['boss_lower_diameter']/2),cyl(x,y,M['boss_neck_bottom_z']-.1,-B['thickness'],M['boss_neck_diameter']/2)])
    holes.extend([cyl(x,y,C['bottom_z']-.2,.3,M['screw_clearance']/2),hexprism(x,y,C['bottom_z']-.2,M['nut_top_z'],M['nut_af'])])
lower=fuse([lower]+bosses);lower=cut(lower,holes+port_tools())
# Low side vents on the side opposite the front controls. No claim of IP sealing.
vents=[box(-5.5,y,-4.8,0,y+9,-2.8,.6) for y in [25,41,57,73,89,105]]
lower=cut(lower,vents)
# Four shallow pockets for optional adhesive rubber feet, away from captive nuts.
for x,y in [(7,22),(7,108),(92,8),(92,123)]:lower=lower.cut(cyl(x,y,C['bottom_z']-.1,C['bottom_z']+.7,3.5))
add('01_lower_shell',lower,(.18,.22,.27),'Print bottom flat. M3 nuts load from the underside; retain with tape/adhesive after test fitting.')

print('Building upper shell',flush=True)
upper=box(x0,y0,seam,x1,y1,ft,C['corner_radius']);upper=upper.cut(box(x0+C['wall'],y0+C['wall'],seam-.2,x1-C['wall'],y1-C['wall'],fb,C['corner_radius']-C['wall']))
lipouter=[x0+C['wall']+C['lip_clearance'],y0+C['wall']+C['lip_clearance'],x1-C['wall']-C['lip_clearance'],y1-C['wall']-C['lip_clearance']]
lip=ring_box(lipouter[0],lipouter[1],seam-C['lip_depth'],lipouter[2],lipouter[3],seam+.25,C['lip_wall'],.8)
bridge=ring_box(x0,y0,seam,x1,y1,seam+1.2,C['wall']+C['lip_clearance']+C['lip_wall'],C['corner_radius'])
upper=fuse([upper,lip,bridge])
# Left two cover screws also secure the LCD PCB to its 16 mm brass standoffs.
for x,y in M['top_lcd_fasteners']:upper=upper.fuse(cyl(x,y,P['lcd']['standoff']+P['lcd']['pcb_thickness'],fb+.1,2.9))
# The two right cover posts stop 0.3 mm above the base PCB. CASE9 has no upper post.
for x,y in M['top_case_fasteners']:upper=upper.fuse(cyl(x,y,.3,fb+.1,3.0))
# C3: ordinary M3 hex nuts load through an underside bay, then slide along +Y.
# A lower ledge, not friction or glue, takes the tightening load.
RF=K['retainer_fastener'];NW,NY=RF['boss_size_xy_mm']
NUT_FLOOR=D['retainer_top_z']+RF['bearing_floor_mm'];NUT_ROOF=NUT_FLOOR+RF['pocket_height_mm']
HEAD_SEAT=D['retainer_bottom_z']+RF['head_recess_mm']
for x,y in K['retainer_screws']:
    upper=upper.fuse(box(x-NW/2,y-NY/2,D['retainer_top_z'],x+NW/2,y+NY/2,fb+.1,.4))
upper=upper.clean();e=P['lcd']['window_extra_each_side'];a,b,c,d=P['lcd']['lens_window_bbox'];window=[a-e,b-e,c+e,d+e]
upper=upper.cut(box(window[0],window[1],fb-.2,window[2],window[3],ft+.2,1.0)).clean()
# Front window entry chamfer keeps the screen edge reachable by a finger.
edges=[ed for ed in upper.Edges() if abs(ed.BoundingBox().zmin-ft)<1e-5 and abs(ed.BoundingBox().zmax-ft)<1e-5 and window[0]-.1<=ed.Center().x<=window[2]+.1 and window[1]-.1<=ed.Center().y<=window[3]+.1]
if edges:upper=cq.Workplane(obj=upper).newObject(edges).chamfer(.8).val()
tools=port_tools()
for ref in ['SW1','SW2','SW3','SW4']:
    x,y=P['controls'][ref];h=K['opening_size']/2;tools.append(box(x-h,y-h,fb-.2,x+h,y+h,ft+.2,K['cap_corner']+.2))
for ref in ['LED1','LED2']:
    x,y=P['controls'][ref];tools.append(cyl(x,y,fb-.2,ft+.2,LP['hole_diameter']/2))
for x,y in M['top_lcd_fasteners']+M['top_case_fasteners']:
    tools.extend([cyl(x,y,-.1,ft+.2,M['screw_clearance']/2),cyl(x,y,ft-M['front_head_recess'],ft+.2,M['front_head_diameter']/2)])
for x,y in K['retainer_screws']:
    af=RF['pocket_af_mm']
    pocket=flat_x_hex(x,y,NUT_FLOOR,NUT_ROOF,af)
    entry=box(x-af/2,y-NY/2-.15,NUT_FLOOR,x+af/2,y+.05,NUT_ROOF)
    # The nut is partly recessed into the face thickness. This open-bottom bay
    # lets it be raised from the shell interior before sliding into the ledge.
    bay=box(x-NW/2,y-12,D['retainer_top_z']-2,x+NW/2,y-NY/2+.1,NUT_ROOF)
    tools.extend([pocket,entry,bay,cyl(x,y,D['retainer_top_z']-.1,NUT_ROOF,RF['plate_clearance_diameter_mm']/2)])
upper=cut(upper,tools)
upper=cut(upper,[text_shape('INFRABOT',70.5,62,ft-.35,2.6,.5),text_shape('PWR',84.1,43,ft-.35,1.6,.5),text_shape('STATUS',84.1,106,ft-.35,1.45,.5)])
add('02_upper_shell',upper,(.78,.81,.84),'Print front face down. Glass datum is assumed: do not compress the LCD to make the cover close.')

print('Building keys and removable travel limiter',flush=True)
rt=D['retainer_top_z'];rb=D['retainer_bottom_z'];left,bottom,right,top=K['retainer_plate_bounds'];ret=box(left,bottom,rb,right,top,rt,1)
for ref in ['SW1','SW2','SW3','SW4']:
    x,y=P['controls'][ref]
    if ref=='SW1':ret=ret.cut(box(x-10.3,y-10.3,rb-.1,x+10.3,y+10.3,rt+.1,1.8))
    else:ret=ret.cut(cyl(x,y,rb-.1,rt+.1,K['retainer_stem_hole']/2))
x,y=P['controls']['SW1'];stop_z=D['flange_bottom_z']-K['power_stroke']
power_floor=box(x-11.3,y-11.3,stop_z-2,x+11.3,y+11.3,stop_z,1.8).cut(cyl(x,y,stop_z-2.1,stop_z+.1,K['retainer_stem_hole']/2))
power_walls=ring_box(x-11.3,y-11.3,stop_z-.1,x+11.3,y+11.3,rt,.9999,1.8)
ret=fuse([ret,power_floor,power_walls])
for ref in ['LED1','LED2']:
    x,y=P['controls'][ref];seat=fb-.45-LP['flange_thickness']-.2
    ret=ret.fuse(cyl(x,y,rt-.1,seat,2.65))
    ret=ret.cut(cyl(x,y,stop_z-2.2,fb+.1,LP['hole_diameter']/2))
for x,y in M['top_case_fasteners']:ret=ret.cut(cyl(x,y,stop_z-2.2,rt+.2,3.3))
for x,y in K['retainer_screws']:
    ret=ret.cut(cyl(x,y,rb-.2,rt+.2,RF['plate_clearance_diameter_mm']/2))
    ret=ret.cut(cyl(x,y,rb-.2,HEAD_SEAT,RF['head_recess_diameter_mm']/2))
ret=ret.clean();add('03_key_retainer',ret,(.32,.37,.42),'M3 x 5 button-head screws into side-loaded hex nuts; D3.4 clearance, 0.2 mm shallow head seats; no tapping. Limits momentary keys to 0.55 mm and power to 3.3 mm; verify actual switch travel.')
key_names=[('SW1','04_key_POWER','POWER',(.28,.32,.37)),('SW2','05_key_RESET','RESET',(.55,.59,.62)),('SW3','06_key_STOP','STOP',(.76,.10,.12)),('SW4','07_key_RESUME','RESUME',(.14,.50,.28))]
for ref,name,label,color in key_names:
    x,y=P['controls'][ref];power=ref=='SW1';switch_height=K['power_height'] if power else K['momentary_height'];engagement=2.0 if power else K['engagement'];depth=engagement+.1
    z0=switch_height-engagement;top=ft+(K['power_protrusion'] if power else K['reset_protrusion'] if ref=='SW2' else K['momentary_protrusion']);h=K['cap_size']/2;f=K['flange_size']/2
    cap=fuse([box(x-h,y-h,D['flange_bottom_z'],x+h,y+h,top,K['cap_corner']),box(x-f,y-f,D['flange_bottom_z'],x+f,y+f,D['flange_top_z'],K['cap_corner']+.5),cyl(x,y,z0,D['flange_bottom_z']+.1,K['stem_diameter']/2)])
    if power:
        sx,sy=K['power_socket'];socket=box(x-sx/2,y-sy/2,z0-.1,x+sx/2,y+sy/2,z0+depth,.15)
    else:socket=cyl(x,y,z0-.1,z0+depth,K['momentary_socket_diameter']/2)
    cap=cut(cap,[socket,text_shape(label,x,y,top-.4,2.7,.6)]);add(name,cap,color,'Socket clearance is a prototype fit. Free-state roof is nominally 0.10 mm above the actuator.')

print('Building light pipes',flush=True)
for ref,name in [('LED1','08_lightpipe_PWR'),('LED2','09_lightpipe_STATUS')]:
    x,y=P['controls'][ref];start=LP[ref+'_top_z']+LP['air_gap'];r0=LP[ref+'_collector_diameter']/2;r1=LP['shaft_diameter']/2;end=ft+LP['front_protrusion'];fh=LP['flange_thickness'];flange_top=fb-.25
    cone=cq.Solid.makeCone(r0,r1,LP['cone_height'],cq.Vector(x,y,start));shaft=cyl(x,y,start+LP['cone_height']-.05,end,r1);flange=cyl(x,y,flange_top-fh,flange_top,LP['flange_diameter']/2)
    s=fuse([cone,shaft,flange]);add(name,s,(.3,.72,.84),'Optical part: clear resin or machined transparent material; ordinary opaque FDM plastic will not guide light. Polish both ends.')

print('Building fitting coupon',flush=True)
# Independent 78 x 40 mm low-cost test part: key opening, LED hole, actuator
# sockets in three clearances and M3 nut trap and side-loading nut-pocket test. Coordinates unrelated to board.
coupon=box(0,0,0,78,40,2.4,2)
coupon=cut(coupon,[box(4,4,-.1,22.6,22.6,2.5,1.8),cyl(31,10,-.1,2.5,1.7),hexprism(43,10,-.1,2.5,M['nut_af'])])
for i,dia in enumerate([6.6,6.8,7.0]):
    x=12+i*17;y=32;coupon=coupon.fuse(cyl(x,y,2.3,6.0,4.7));coupon=coupon.cut(cyl(x,y,3.3,6.1,dia/2));coupon=coupon.cut(text_shape(f'{dia:.1f}',x,26.6,2.05,2,.5,0))
for i,gap in enumerate([.2,.3,.4]):
    x=59+i*7;y=10;coupon=coupon.fuse(box(x-3,y-3,2.3,x+3,y+3,6,.5));coupon=coupon.cut(box(x-(3.9+gap)/2,y-(3.8+gap)/2,3.3,x+(3.9+gap)/2,y+(3.8+gap)/2,6.1,.1))
# Same hex/entry clearance as the enclosure, open on its front side. The
# coupon checks free insertion and anti-rotation, not final screw engagement.
coupon=coupon.fuse(box(60,22,2.3,75,38,6.85,1))
coupon=cut(coupon,[flat_x_hex(67.5,29,3.2,6.0,RF['pocket_af_mm']),box(67.5-RF['pocket_af_mm']/2,21.9,3.2,67.5+RF['pocket_af_mm']/2,29.1,6.0),cyl(67.5,29,-.1,6.0,1.7)])
coupon=coupon.cut(text_shape('M3 NUT',67.5,35.2,6.5,1.6,.6,0))
add('10_fit_coupon',coupon.clean(),(.68,.70,.72),'Test only: sockets 6.6/6.8/7.0 mm and power clearances 0.2/0.3/0.4 mm. Do not force a tight coupon onto a switch. M3 test block: slide-in AF5.9 x H2.8 pocket; test nut insertion, without forcing a screw to the roof.')

template=upper.intersect(box(x0-1,y0-1,ft-1,x1+1,y1+1,ft+.1)).clean()
add('11_front_fit_template',template,(.68,.70,.72),'1 mm front-face template for checking the actual LCD window and control XY before full-shell printing.')

print('Building reference-only assembly envelopes',flush=True)
pcb=box(0,0,-B['thickness'],100,130,0,.25)
for x,y in mounts:pcb=pcb.cut(cyl(x,y,-1.8,.1,1.6 if [x,y] not in M['lcd'] else 1.7))
add('REF_base_PCB',pcb.clean(),(.13,.36,.24),'Nominal 1.6 mm PCB. Does not replace native R8 PCB reference.',True)
a,b,c,d=P['lcd']['pcb_bbox'];lcd=box(a,b,16,c,d,17.6,1.5)
for x,y in M['lcd']:lcd=lcd.cut(cyl(x,y,15.9,17.7,1.5))
add('REF_LCD_PCB',lcd.clean(),(.12,.36,.23),'XY from Wildfire module drawing; nominal 1.6 mm thickness.',True)
ga,gb,gc,gd=P['lcd']['glass_bbox'];glass=box(ga,gb,D['glass_top_z']-1.05,gc,gd,D['glass_top_z'],.4)
add('REF_touch_glass',glass,(.055,.075,.09),'Lens 105.4 x 67.1; height and registration pending measurement.',True)
a,b,c,d=P['lcd']['lens_window_bbox'];add('REF_visible_screen',box(a,b,D['glass_top_z']+.001,c,d,D['glass_top_z']+.025,.2),(.12,.27,.33),'Visible-area proxy, not the actual display content.',True)
add('REF_LCD_body',box(ga,gb,17.6,gc,gd,D['glass_top_z']-1.05,.4),(.25,.28,.30),'LCM + adhesive thickness envelope, assumed.',True)
a,b,c,d=P['core']['bbox'];core=box(a,b,P['core']['pcb_bottom_z'],c,d,P['core']['pcb_bottom_z']+P['core']['pcb_thickness'],2)
for x,y in M['core']:core=core.cut(cyl(x,y,5.9,7.8,1.5))
add('REF_core_PCB',core.clean(),(.12,.30,.23),'XY drawing-derived; Z stack assumed.',True)
add('REF_core_components',box(22,40,7.6,57,77,P['core']['max_component_top_z'],1),(.12,.15,.17),'Conservative core component proxy; real populated header heights unverified.',True)
a,b,c,d=P['lcd']['header_bbox'];add('REF_unused_LCD_header',box(a,b,16-P['lcd']['header_protrusion'],c,d,16,.1),(.26,.27,.28),'Unused 2x19 header projection; 8.5 mm protrusion is unverified on this module.',True)
for i,(x,y) in enumerate(M['lcd'],1):
    standoff=hexprism(x,y,0,16,5.5).cut(cyl(x,y,-.1,16.1,1.5));add('REF_standoff16_'+str(i),standoff,(.69,.52,.22),'Required 16 mm brass body, M3 male-female. Threads simplified.',True)
# Major connectors: physical model dimensions and conservative plug access.
for ref,bounds in {'J1':[85.87,4.15,0,100.13,13.15,11.0],'J2':[10.48,109.05,0,26.52,130.53,13.84],'J3':[41.53,122.51,0,50.47,130,3.25],'J5':[52.62,122.37,0,64.33,129.53,8.7],'J6':[28.65,.7,0,41.35,9.54,2.54]}.items():
    add('REF_'+ref,box(*bounds,.15),(.56,.58,.60) if ref in ['J2','J3'] else (.15,.19,.21),'Approximate connector envelope from native models/drawings; actual plug housing not supplied.',True)
for ref in ['SW1','SW2','SW3','SW4']:
    x,y=P['controls'][ref];power=ref=='SW1';h=4.25 if power else 6;body_h=8.5 if power else 3.5;body=box(x-h,y-h,0,x+h,y+h,body_h,.3)
    if power:act=box(x-1.95,y-1.9,body_h,x+1.95,y+1.9,K['power_height'],.1)
    else:act=cyl(x,y,body_h,K['momentary_height'],3.25)
    add('REF_'+ref,fuse([body,act]),(.10,.12,.14),'Selected-part actuator height; native generic short switch model is intentionally not used.',True)
for ref,rad in [('LED1',1.5),('LED2',2.5)]:
    x,y=P['controls'][ref];top=LP[ref+'_top_z'];add('REF_'+ref,cyl(x,y,top-4.2,top,rad),(.75,.10,.10) if ref=='LED1' else (.55,.60,.62),'LED envelope; STATUS height depends on lead forming.',True)

for i,(x,y) in enumerate(K['retainer_screws'],1):
    add(f'REF_retainer_M3_head_{i}',cyl(x,y,HEAD_SEAT-RF['head_height_mm'],HEAD_SEAT,RF['head_diameter_mm']/2),(.62,.64,.65),'Conservative cylinder for M3 button head; threaded shaft not modelled.',True)

for i,(x,y) in enumerate(K['retainer_screws'],1):
    add(f'REF_retainer_M3_shank_{i}',cyl(x,y,HEAD_SEAT,HEAD_SEAT+RF['length_mm'],1.5),(.62,.64,.65),'M3 shank/nominal thread envelope; printed holes have clearance, metal nut supplies the thread.',True)

for i,(x,y) in enumerate(K['retainer_screws'],1):
    nut=flat_x_hex(x,y,NUT_FLOOR,NUT_FLOOR+RF['nut_thickness_mm'],RF['nut_af_mm']).cut(cyl(x,y,NUT_FLOOR-.1,NUT_FLOOR+RF['nut_thickness_mm']+.1,1.5))
    add(f'REF_retainer_M3_nut_{i}',nut,(.72,.67,.47),'Standard M3 hex nut, AF5.5 x H2.4. Thread simplified; lower ledge carries tensile load.',True)

# Actual CAD slice solids, for inspection views only; never print these.
section_meshes={}
for section_name,y in [('RESET',57),('POWER',30),('STATUS',106),('M3',17)]:
    clip=box(-5,y-.15,-10,105,y+.15,31);items={}
    for name,solid in (PARTS|REFS).items():
        if name in ['10_fit_coupon','11_front_fit_template']:continue
        bounds=bb(solid)
        if bounds[1]>y+.15 or bounds[4]<y-.15:continue
        sliced=solid.intersect(clip)
        if sliced.Volume()<=1e-7:continue
        vs,fs=sliced.tessellate(.04,.16);items[name]={'v':[v.toTuple() for v in vs],'f':fs,'color':COLORS[name],'bounds':bb(sliced)}
    section_meshes[section_name]=items
detail={};clip=box(70,4,16.5,81,23,26)
for name in ['02_upper_shell','03_key_retainer','REF_retainer_M3_head_1','REF_retainer_M3_shank_1','REF_retainer_M3_nut_1']:
    shape=(PARTS|REFS)[name].intersect(clip)
    if shape.Volume()>1e-7:
        vs,fs=shape.tessellate(.035,.14);detail[name]={'v':[v.toTuple() for v in vs],'f':fs,'color':COLORS[name],'bounds':bb(shape)}
(ROOT/'.work/nut-detail-meshes.json').write_text(json.dumps(detail,separators=(',',':')))
(ROOT/'.work/section-meshes.json').write_text(json.dumps(section_meshes,separators=(',',':')))

print('Exporting STEP/STL and tessellation data',flush=True)
assembly=cq.Assembly(name=P['revision']+'_enclosure');fit=cq.Assembly(name=P['revision']+'_fit_reference')
for name,s in PARTS.items():
    cq.exporters.export(s,str(ROOT/'STEP'/(name+'.step')))
    if name=='02_upper_shell' or name.startswith(('04_','05_','06_','07_')):printing=s.rotate((0,0,0),(1,0,0),180)
    else:printing=s
    z=printing.BoundingBox().zmin;printing=printing.translate((0,0,-z));bbp=printing.BoundingBox();printing=printing.translate((-bbp.xmin,-bbp.ymin,0))
    cq.exporters.export(printing,str(ROOT/'STL'/(name+'.stl')),tolerance=.035,angularTolerance=.12)
    if name not in ['10_fit_coupon','11_front_fit_template']:
        assembly.add(s,name=name,color=cq.Color(*COLORS[name]));fit.add(s,name=name,color=cq.Color(*COLORS[name]))
for name,s in REFS.items():fit.add(s,name=name,color=cq.Color(*COLORS[name]))
assembly.export(str(ROOT/'STEP/00_enclosure_assembly.step'));fit.export(str(ROOT/'STEP/00_fit_reference_assembly.step'))
# Neutral mesh cache for independent PNG rendering; excludes the native PCB source.
for name,s in (PARTS|REFS).items():
    vertices,faces=s.tessellate(.055,.18);MESH[name]={'v':[v.toTuple() for v in vertices],'f':faces,'color':COLORS[name],'bounds':bb(s)}
(ROOT/'.work/meshes.json').write_text(json.dumps(MESH,separators=(',',':')))

print('Checking solids, mechanical interference and moving envelopes',flush=True)
report={'revision':P['revision'],'readiness':P['readiness'],'derived':D,'solid_checks':{},'intersections':[],'errors':[],'assumptions':{'lcd':P['lcd']['unverified'],'core':P['core']['status'],'key_fit':K['status'],'lightpipes':LP['status']}}
for name,s in (PARTS|REFS).items():report['solid_checks'][name]={'valid':s.isValid(),'solid_count':len(s.Solids()),'volume_mm3':s.Volume(),'bounds_mm':bb(s)}

def intersect(name1,s1,name2,s2):
    a=bb(s1);b=bb(s2)
    if any(a[i+3]<=b[i]+1e-6 or b[i+3]<=a[i]+1e-6 for i in range(3)):return 0.0
    return s1.intersect(s2).Volume()
checks=[('01_lower_shell','02_upper_shell'),('01_lower_shell','REF_base_PCB'),('02_upper_shell','03_key_retainer'),('02_upper_shell','REF_LCD_PCB'),('02_upper_shell','REF_touch_glass'),('02_upper_shell','REF_LCD_body'),('03_key_retainer','REF_LCD_PCB')]
for shell in ['01_lower_shell','02_upper_shell','03_key_retainer']:
    checks += [(shell,ref) for ref in REFS if ref.startswith('REF_J') or ref.startswith('REF_SW') or ref.startswith('REF_LED') or ref.startswith('REF_core') or ref=='REF_unused_LCD_header']
for a,b in checks:
    volume=intersect(a,(PARTS|REFS)[a],b,(PARTS|REFS)[b]);report['intersections'].append({'a':a,'b':b,'overlap_mm3':volume})
    if volume>1e-4:report['errors'].append(f'{a} / {b}: {volume:.6f} mm3')
movings=[n for n in PARTS if n.startswith(('04_','05_','06_','07_','08_','09_'))]
for name in movings:
    travel=K['power_stroke'] if name.startswith('04_') else K['momentary_stroke'] if name.startswith(('05_','06_','07_')) else .2
    for state,dz in [('rest',0),('pressed',-travel)]:
        s=PARTS[name].translate((0,0,dz))
        for other in ['01_lower_shell','02_upper_shell','03_key_retainer']+[n for n in movings if n!=name]:
            vol=intersect(name,s,other,PARTS[other]);report['intersections'].append({'a':name,'state':state,'b':other,'overlap_mm3':vol})
            if vol>1e-4:report['errors'].append(f'{name} {state} / {other}: {vol:.6f} mm3')
# Check head bearing, standard nut seating and physically accessible insertion.
report['retainer_fastener_checks']=[]
for i,(x,y) in enumerate(K['retainer_screws'],1):
    name=f'REF_retainer_M3_head_{i}';head=REFS[name];nut_name=f'REF_retainer_M3_nut_{i}';nut=REFS[nut_name];shaft=REFS[f'REF_retainer_M3_shank_{i}'];a,b,c,d=K['retainer_plate_bounds']
    bearing_margin=min(x-a,c-x,y-b,d-y)-RF['head_diameter_mm']/2
    row={'index':i,'xy_mm':[x,y],'fixing_method':'SIDE_LOADED_STANDARD_M3_HEX_NUT_NO_TAPPING','head_edge_bearing_margin_mm':bearing_margin,'pocket_side_wall_mm':(NW-RF['pocket_af_mm'])/2,'nut_bearing_floor_mm':RF['bearing_floor_mm'],'pocket_roof_to_front_face_mm':ft-NUT_ROOF,'head_seat_remaining_plate_mm':K['retainer_thickness']-RF['head_recess_mm'],'nominal_nut_thread_engagement_mm':min(RF['nut_thickness_mm'],HEAD_SEAT+RF['length_mm']-NUT_FLOOR),'screw_tip_to_pocket_roof_mm':NUT_ROOF-(HEAD_SEAT+RF['length_mm']),'head_clearances_mm':{}}
    if bearing_margin<.5-1e-6:report['errors'].append(name+' insufficient head bearing')
    if row['screw_tip_to_pocket_roof_mm']<.3-1e-6:report['errors'].append(name+' screw may bottom out')
    if row['nominal_nut_thread_engagement_mm']<RF['nut_thickness_mm']-1e-6:report['errors'].append(name+' does not cover nominal nut thickness')
    for moving_name,moving_solid in [(name,head),(nut_name,nut),(f'REF_retainer_M3_shank_{i}',shaft)]:
        for other in ['01_lower_shell','02_upper_shell','03_key_retainer']+list(REFS):
            if other==moving_name:continue
            vol=intersect(moving_name,moving_solid,other,(PARTS|REFS)[other])
            if vol>1e-4:report['errors'].append(f'{moving_name} / {other}: {vol:.6f} mm3')
        for moving in movings:
            travel=K['power_stroke'] if moving.startswith('04_') else K['momentary_stroke'] if moving.startswith(('05_','06_','07_')) else .2
            for dz in [0,-travel]:
                shape=PARTS[moving].translate((0,0,dz));vol=intersect(moving_name,moving_solid,moving,shape)
                if vol>1e-4:report['errors'].append(f'{moving_name} / {moving}: {vol:.6f} mm3')
    for other in ['REF_LCD_PCB','REF_LCD_body','REF_touch_glass']:row['head_clearances_mm'][other]=head.distance(REFS[other])
    # Insert into the inverted upper shell before installing keys/retainer:
    # lift into the bay, slide +Y, then settle by 0.2 mm onto its bearing ledge.
    collisions=[]
    for k in range(13):
        pose=nut.translate((0,-8.5,-5+5.2*k/12));volume=pose.intersect(upper).Volume()
        if volume>1e-4:collisions.append({'phase':'lift','step':k,'volume':volume})
    for k in range(35):
        pose=nut.translate((0,-8.5+8.5*k/34,.2));volume=pose.intersect(upper).Volume()
        if volume>1e-4:collisions.append({'phase':'slide','step':k,'volume':volume})
    row['insertion_pose_checks']=48;row['insertion_collisions']=collisions
    if collisions:report['errors'].append(nut_name+' insertion path blocked')
    row['downward_0p1mm_bearing_overlap_mm3']=nut.translate((0,0,-.1)).intersect(upper).Volume()
    row['rotation_30deg_blocked_overlap_mm3']=nut.rotate((x,y,0),(x,y,1),30).intersect(upper).Volume()
    row['forward_0p6mm_stop_overlap_mm3']=nut.translate((0,.6,0)).intersect(upper).Volume()
    if min(row['downward_0p1mm_bearing_overlap_mm3'],row['rotation_30deg_blocked_overlap_mm3'],row['forward_0p6mm_stop_overlap_mm3'])<.01:report['errors'].append(nut_name+' capture/anti-rotation ledge ineffective')
    report['retainer_fastener_checks'].append(row)
report['clearances_mm']={'nominal_LCD_PCB_to_RJ45_top':16-13.84,'nominal_unused_LCD_header_to_bare_SWD':16-8.5-2.54,'glass_to_upper_shell_inner_face':C['glass_gap'],'lightpipe_to_LED_nominal':LP['air_gap'],'momentary_actuator_roof_gap':.1,'tongue_radial_clearance':C['lip_clearance'],'key_opening_total_clearance':K['opening_size']-K['cap_size'],'PCB_pin_tip_to_floor_min_assumed':-4-floor_top}
report['geometry_binding']={'parameters_sha256':hashlib.sha256((ROOT/'parameters.json').read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'exports':{f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for folder,suffix in [('STEP','*.step'),('STL','*.stl')] for f in sorted((ROOT/folder).glob(suffix))}}
report['passed_geometry']=not report['errors'] and all(x['valid'] for x in report['solid_checks'].values())
(ROOT/'fit-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(ROOT/'.work/part-notes.json').write_text(json.dumps(NOTES,ensure_ascii=False,indent=2)+'\n');(ROOT/'.work/resolved-parameters.json').write_text(json.dumps(P,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed_geometry':report['passed_geometry'],'errors':report['errors'],'parts':len(PARTS),'case_size':D['external_case_size_mm']},indent=2),flush=True)
