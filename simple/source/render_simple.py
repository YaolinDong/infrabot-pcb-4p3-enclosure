# SPDX-License-Identifier: MIT
"""Render actual generated CAD tessellations with a depth buffer (no AI imagery)."""
from pathlib import Path
import json,math
import numpy as np
import cadquery as cq
from numba import njit
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];mesh=json.loads((ROOT/'.work/meshes.json').read_text());OUT=ROOT/'preview';OUT.mkdir(exist_ok=True)
PARAMS=json.loads((ROOT/'parameters.json').read_text());REV=PARAMS['revision'].split('_')[-1];DECK=PARAMS['simple_controls']['deck_z']
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
# Resolve the new sub-millimetre fillets smoothly in every view.
for name in ['01_lower_shell','02_upper_shell']:
    shape=cq.importers.importStep(str(ROOT/'STEP'/(name+'.step'))).val();vs,fs=shape.tessellate(.015,.07)
    mesh[name]['v']=[v.toTuple() for v in vs];mesh[name]['f']=fs
@njit(cache=True)
def raster(xy,z,faces,colors,depths,width,height):
    pixels=np.empty((height,width,3),dtype=np.uint8);pixels[:]=242
    zb=np.full((height,width),-1e30)
    for i in range(len(faces)):
        ids=faces[i];x0,y0=xy[ids[0]];x1,y1=xy[ids[1]];x2,y2=xy[ids[2]]
        den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(den)<1e-10:continue
        xmin=max(0,int(math.floor(min(x0,x1,x2))));xmax=min(width-1,int(math.ceil(max(x0,x1,x2))))
        ymin=max(0,int(math.floor(min(y0,y1,y2))));ymax=min(height-1,int(math.ceil(max(y0,y1,y2))))
        for y in range(ymin,ymax+1):
            for x in range(xmin,xmax+1):
                a=((y1-y2)*(x+.5-x2)+(x2-x1)*(y+.5-y2))/den;b=((y2-y0)*(x+.5-x2)+(x0-x2)*(y+.5-y2))/den;c=1-a-b
                if a>=-1e-7 and b>=-1e-7 and c>=-1e-7:
                    zz=a*z[ids[0]]+b*z[ids[1]]+c*z[ids[2]]
                    if zz>zb[y,x]:zb[y,x]=zz;pixels[y,x]=colors[i]
    return pixels,zb

def view(filename,selection,u,w,title,subtitle,shifts=None,frame_bounds=None):
    vertices=[];faces=[];cols=[];n=0
    for name in selection:
        m=mesh[name];v=np.asarray(m['v'],float);f=np.asarray(m['f'],np.int32)
        if shifts:v=v+np.asarray(shifts.get(name,[0,0,0]))
        vertices.append(v);faces.append(f+n);cols.extend([m['color']]*len(f));n+=len(v)
    v=np.vstack(vertices);f=np.vstack(faces);col=np.asarray(cols);u=np.array(u);w=np.array(w);depth=np.cross(u,w);q=np.column_stack([v@u,v@w,v@depth]);lo=q[:,:2].min(0);hi=q[:,:2].max(0)
    if frame_bounds is not None:lo,hi=map(np.asarray,frame_bounds)
    scale=min(1700/(hi[0]-lo[0]),1300/(hi[1]-lo[1]));width=int((hi[0]-lo[0])*scale)+120;height=int((hi[1]-lo[1])*scale)+175
    xy=(q[:,:2]-lo)*scale;xy[:,0]+=60;xy[:,1]=height-70-xy[:,1]
    tri=v[f];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
    light=depth+np.array([-.25,-.35,.7]);light/=np.linalg.norm(light);shade=.58+.42*np.abs(normal@light)
    rgb=(np.clip(col*shade[:,None]+.035,0,1)*255).astype(np.uint8)
    pixels,zb=raster(xy,q[:,2],f,rgb,depth,width,height)
    if filename in ['front.png','upper_inside.png','lower_bottom.png']:
        from scipy.ndimage import maximum_filter
        shadow=(zb>-1e20)&(maximum_filter(zb,size=7)-zb>.16)
        if filename=='lower_bottom.png':shadow |= (zb>-1e20)&(zb.max()-zb>.16)
        pixels[shadow]=(pixels[shadow]*.72).astype(np.uint8)
    im=Image.fromarray(pixels);draw=ImageDraw.Draw(im);font=ImageFont.truetype(FONT,23);small=ImageFont.truetype(FONT,15)
    draw.text((30,18),title,font=font,fill='#203a4a');draw.text((30,height-39),subtitle,font=small,fill='#4c5d66');im.save(OUT/filename);print(filename,im.size,flush=True)

printed=list(n for n in mesh if not n.startswith('REF_'));refs=[n for n in mesh if n.startswith('REF_')];all_parts=printed+refs
u=(-.5,.8660254,0);w=(-.6123724,-.3535534,.7071068)
view('assembled.png',all_parts,u,w,f'InfraBot SIMPLE {REV} | exactly two printed shells',f'Control deck Z={DECK:g} mm | 16 mm LCD standoffs | stock actuators and direct LEDs')
view('front.png',all_parts,(0,1,0),(-1,0,0),'Front view | original switches and LEDs','Near-flush PWR LED at Z5.5; integral POWER and RESET guards')
view('ports.png',all_parts,(.5,.8660254,0),(-.6123724,.3535534,.7071068),'Opposite corner | DC and SWD access','DC connector has an integral raised hood; actual cable housings still require test fitting')
view('lower_inside.png',['01_lower_shell'],u,w,f'{REV} lower shell | R1 bottom rim, S4 seam and mounting posts','4 round lower screw pockets for female-female spacers; only 3 CASE nuts; CORE fasteners optional')
view('lower_bottom.png',['01_lower_shell'],(0,1,0),(1,0,0),'Bottom view | 4 spacer screws and 3 CASE nuts','Round pockets: M3x10 upward into spacers | hex pockets: CASE nuts | CORE pockets optional')
view('upper_inside.png',['02_upper_shell'],(.5,.8660254,0),(.5,-.2886751,-.8164966),'Upper shell inside | one integral part','4 LCD supports + 3 CASE supports; continuously rounded CASE9 pocket near DC; no loose printed parts')
view('upper_outside.png',['02_upper_shell'],u,w,'Upper shell only | stepped operating terrace','Two-piece enclosure; stock 17 mm momentary actuators, 14.1 mm power actuator')
for name,axis in [('side_ETH_USB_CAN.png',(-1,0,0)),('side_DC.png',(0,1,0)),('side_SWD.png',(1,0,0)),('side_vents.png',(0,-1,0))]:
    view(name,all_parts,axis,(0,0,1),name.replace('.png','').replace('_',' '),'Simplified electronic envelopes; no cable overmould guarantees')
shifts={}
for n in all_parts:
    dz=45 if n=='02_upper_shell' or n.startswith(('REF_lid_screw','REF_case_lid_screw')) else 0 if n=='01_lower_shell' or n.startswith(('REF_base_nut','REF_bottom_LCD_screw')) else 4
    if n.startswith(('REF_LCD','REF_touch','REF_visible','REF_unused')):dz=18
    if n.startswith('REF_core'):dz=10
    shifts[n]=[0,0,dz]
view('exploded.png',all_parts,u,w,'Exploded assembly | two shell parts','11 screws: 4 M3x12 + 7 M3x10 | 3 M3 nuts | 4 female-female 16 mm spacers')
full=mesh
for name,items in json.loads((ROOT/'.work/section-meshes.json').read_text()).items():
    mesh=items
    frame=([.4,-9.2],[11.4,26]) if name=='LCD_POST' else ([91,-9.2],[102,15]) if name.startswith('CASE') else None
    note='Top M3x12 / bottom M3x10' if name=='LCD_POST' else 'M3x10 / lower M3 nut' if name.startswith('CASE') else 'Nominal geometry; actual assembly still requires checking'
    view('section_'+name+'.png',list(items),(1,0,0),(0,0,1),'CAD section | '+name,note,frame_bounds=frame)
mesh=full
# Reference hardware changes as well as the two shell shapes.
saved=mesh;fontpath='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
large=ImageFont.truetype(fontpath,32);label_font=ImageFont.truetype(fontpath,25)
def same_frame(datasets,u,w):
    points=np.vstack([np.asarray(m['v']) for ds in datasets for m in ds.values()]);q=np.column_stack([points@u,points@w]);return q.min(0),q.max(0)
def item(shape,color):
    vs,fs=shape.tessellate(.015,.07);return {'v':[v.toTuple() for v in vs],'f':fs,'color':color}
baseline={n:m for n,m in saved.items() if n.startswith('REF_')}
for n,path in [('01_lower_shell','reference/lower_S7_before_full_rim.step'),('02_upper_shell','reference/upper_S7_before_full_rim.step')]:baseline[n]=item(cq.importers.importStep(str(ROOT/path)).val(),saved[n]['color'])
frame=same_frame([baseline,saved],np.asarray(u),np.asarray(w))
for tag,items in [('before',baseline),('after',saved)]:
    mesh=items;view('fasteners_'+tag+'.png',list(items),u,w,('S7 | sharp CASE9 upright and upper edges' if tag=='before' else f'{REV} | continuously rounded CASE9 pocket'),'Same scale and camera | original PCB, 16 mm spacing and rounded exterior',frame_bounds=frame)
comparison=Image.new('RGB',(2400,1250),'white');dr=ImageDraw.Draw(comparison)
dr.text((35,20),'S7 → S8：孔口、两侧竖边、顶部缺口连续圆角，去掉两个尖角',font=large,fill='#203a4a')
for i,(file,caption) in enumerate([('fasteners_before.png','S7：仍有锐边'),('fasteners_after.png',f'{REV}：连续 R0.4 圆角及局部过渡')]):
    pic=Image.open(OUT/file).convert('RGB');pic.thumbnail((1140,1030));x=30+i*1200;comparison.paste(pic,(x+(1140-pic.width)//2,110+(1030-pic.height)//2));dr.text((x,1170),caption,font=label_font,fill='#203a4a')
comparison.save(OUT/'fasteners_compare.png')
# Show exact CAD sections for both fastener paths.
guide=Image.new('RGB',(2100,1650),'white');dr=ImageDraw.Draw(guide)
dr.text((35,20),'S8 固定剖面：铜柱与螺丝不变，CASE9 圆角不改变螺丝承压结构',font=large,fill='#203a4a')
for i,(name,title,note) in enumerate([('LCD_POST','屏幕固定柱','上 M3×12；下 M3×10'),('CASE9','CASE9（后侧剖面）','M3×10；前侧已敞开降低'),('CASE10','CASE10 / CASE11','M3×10；螺丝头低于操作面')]):
    x=35+i*690;dr.text((x,90),title,font=label_font,fill='#203a4a');pic=Image.open(OUT/('section_'+name+'.png')).convert('RGB');pic.thumbnail((640,1280));guide.paste(pic,(x+(640-pic.width)//2,150+(1280-pic.height)//2));dr.text((x,1460),note,font=label_font,fill='#203a4a')
dr.text((35,1530),'铜柱底面不放螺母；只有 CASE9/10/11 各一颗 M3 螺母。全部塑料孔免攻牙。',font=label_font,fill='#203a4a')
dr.text((35,1580),'铜柱两端有效螺纹深度需至少 5 mm；实际铜柱和打印件仍需试装核对。',font=label_font,fill='#735136');guide.save(OUT/'fastener_stack_guide.png')
# Close-up comparison uses real cropped CAD and identical POWER/fastener geometry.
clip=cq.Workplane('XY',origin=(92,17.5,3)).box(26,43,12,centered=(True,True,False)).val()
patches={}
for tag,path in [('before','reference/upper_S7_before_full_rim.step'),('after','STEP/02_upper_shell.step')]:
    items={'upper':item(cq.importers.importStep(str(ROOT/path)).val().intersect(clip),saved['02_upper_shell']['color'])}
    items.update({n:m for n,m in saved.items() if n.startswith('REF_SW1')})
    F=PARAMS['fasteners'];xx,yy=PARAMS['mounts']['case'][0]
    items['CASE9_head']=item(cq.Solid.makeCylinder(F['head_diameter']/2,F['head_height'],cq.Vector(xx,yy,F['case_upper_head_seat_z'])),(.64,.66,.68));patches[tag]=items
frame=same_frame(patches.values(),np.asarray(u),np.asarray(w))
for tag,items in patches.items():
    mesh=items;view('CASE9_'+tag+'.png',list(items),u,w,('S7 | sharp rim junctions' if tag=='before' else f'{REV} | continuous R0.4 rim and R0.1 lower transitions'),'Same scale and camera | M3x10 screw bearing remains at Z3.5',frame_bounds=frame)
comparison=Image.new('RGB',(2200,1180),'white');dr=ImageDraw.Draw(comparison);dr.text((30,20),'电源旁 CASE9：补全竖边、顶沿和底部交接的圆角',font=large,fill='#203a4a')
for i,(file,caption) in enumerate([('CASE9_before.png','S7：竖边和顶部仍有锐边'),('CASE9_after.png',f'{REV}：R0.4 连续圆角，交接处再平顺处理')]):
    pic=Image.open(OUT/file).convert('RGB');pic.thumbnail((1040,940));x=30+i*1090;comparison.paste(pic,(x+(1040-pic.width)//2,110+(940-pic.height)//2));dr.text((x,1100),caption,font=label_font,fill='#203a4a')
comparison.save(OUT/'CASE9_compare.png')
mesh=saved
clip=cq.Workplane('XY',origin=(89.5,43,1.5)).box(15,15,9.5,centered=(True,True,False)).val()
mesh={'upper':item(cq.importers.importStep(str(ROOT/'STEP/02_upper_shell.step')).val().intersect(clip),saved['02_upper_shell']['color']),'LED1':saved['REF_LED1']}
view('LED1_after.png',list(mesh),u,w,f'{REV} | near-flush LED1, deck Z5.5','Original LED mounting height; 4.4 mm bore and smoothly rounded mouth')
mesh=saved
import hashlib
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT/'.work/render-record.json').write_text(json.dumps({'revision':json.loads((ROOT/'parameters.json').read_text())['revision'],'geometry_binding':json.loads((ROOT/'fit-check.json').read_text())['geometry_binding'],'renderer_sha256':sha(Path(__file__)),'images':{p.name:sha(p) for p in OUT.glob('*.png') if p.name not in ['00_overview.png','dimensions.png','mounting-plan.png']}},indent=2)+'\n')
