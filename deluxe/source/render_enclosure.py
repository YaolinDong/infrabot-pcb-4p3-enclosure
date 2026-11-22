# SPDX-License-Identifier: MIT
"""Render actual generated CAD tessellations with a depth buffer (no AI imagery)."""
from pathlib import Path
import json,math
import numpy as np
from numba import njit
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];mesh=json.loads((ROOT/'.work/meshes.json').read_text());OUT=ROOT/'preview';OUT.mkdir(exist_ok=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
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

def view(filename,selection,u,w,title,subtitle,shifts=None):
    vertices=[];faces=[];cols=[];n=0
    for name in selection:
        m=mesh[name];v=np.asarray(m['v'],float);f=np.asarray(m['f'],np.int32)
        if shifts:v=v+np.asarray(shifts.get(name,[0,0,0]))
        vertices.append(v);faces.append(f+n);cols.extend([m['color']]*len(f));n+=len(v)
    v=np.vstack(vertices);f=np.vstack(faces);col=np.asarray(cols);u=np.array(u);w=np.array(w);depth=np.cross(u,w);q=np.column_stack([v@u,v@w,v@depth]);lo=q[:,:2].min(0);hi=q[:,:2].max(0)
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
printed=[n for n in mesh if not n.startswith('REF_') and n not in ['10_fit_coupon','11_front_fit_template']];refs=[n for n in mesh if n.startswith('REF_')];all_parts=printed+refs
iso_u=(-.5,.8660254,0);iso_w=(-.5,-.2886751,.8164966)
view('assembled.png',all_parts,iso_u,iso_w,'InfraBot R8 | 16 mm screen standoffs | enclosure C3 / no tapping','CAD fit prototype | nominal shell 138.4 x 108.4 x 34.55 mm | screen Z / actuator fit require measurement')
view('front.png',all_parts,(0,1,0),(-1,0,0),'Front view | POWER / PWR / RESET / STOP / STATUS / RESUME','RESET recessed 1.5 mm | 18 mm keycaps | 3 mm lightpipes | four front cover screws')
view('ports.png',all_parts,(.5,.8660254,0),(-.5,.2886751,.8164966),'Opposite corner | DC and SWD access','DC, SWD and USB/CAN plug housings are not measured; verify with your actual cables')
view('lower_inside.png',['01_lower_shell'],iso_u,iso_w,'Lower shell | mounting posts and captive M3 nuts','11 PCB supports | 4 screen standoffs + 4 optional core-area PCB screws + 3 case positions')
view('upper_inside.png',[n for n in printed if n!='01_lower_shell'],(0,1,0),(1,0,0),'Upper shell inside | removable key travel limiter','M3 x 5 retainer screws | nominal momentary stop 0.55 mm, power stop 3.3 mm; verify actual switching')
shift={}
for n in all_parts:
    dz=0 if n=='01_lower_shell' else 58 if n=='02_upper_shell' else 37 if n=='03_key_retainer' else 77 if n in printed else 4
    if n.startswith(('REF_LCD','REF_touch','REF_visible','REF_unused')):dz=18
    if n.startswith('REF_core'):dz=10
    if n.startswith('REF_retainer_M3_'):dz=37
    shift[n]=[0,0,dz]
view('exploded.png',all_parts,iso_u,iso_w,'Exploded fit assembly | layers separated for clarity','Electronics are dimensioned reference envelopes; enclosure and moving parts are the actual STEP geometry',shift)
view('fit_coupon.png',['10_fit_coupon'],iso_u,iso_w,'Print first | actuator sockets and side-loading M3 nut fit','Round sockets: 6.6 / 6.8 / 7.0 mm | power socket clearance: 0.2 / 0.3 / 0.4 mm')

# Additional requested inspection views from exactly the same C3 geometry.
view('side_ETH_USB_CAN.png',all_parts,(-1,0,0),(0,0,1),'RJ45 / USB-C / CAN side','Actual cable overmoulds remain to be test-fitted; electronics are reference envelopes')
view('side_DC.png',all_parts,(0,1,0),(0,0,1),'DC side','Power inlet stays at the lower-left when facing the screen')
view('side_SWD.png',all_parts,(1,0,0),(0,0,1),'SWD side','Recessed 5 pin right-angle connector opening; verify your mating socket')
view('side_vents.png',all_parts,(0,-1,0),(0,0,1),'Vent side','Vent slots and enclosure seam; no waterproof rating')
view('lower_bottom.png',['01_lower_shell'],(0,1,0),(1,0,0),'Lower shell underside | eleven captive M3 nut pockets','Nut pockets are loaded from outside; four shallow round recesses accept adhesive feet')
view('upper_bosses.png',['02_upper_shell'],(.5,.8660254,0),(.5,-.2886751,-.8164966),'Upper shell inside | M3 retainer posts','Side-loaded standard M3 hex nuts; integrated lower ledges carry load, no tapping')
view('retainer_M3.png',['03_key_retainer']+[n for n in refs if n.startswith('REF_retainer_M3_')],(.5,.8660254,0),(.5,-.2886751,-.8164966),'Retainer underside | four M3 x 5 screws','M3 x 5 into standard hex nuts; shallow 0.2 mm head seats, no printed threads')
view('keys_top.png',[n for n in printed if n.startswith(('04_','05_','06_','07_'))],(0,1,0),(-.5,0,.8660254),'Four custom 18 mm keycaps','POWER / RESET / STOP / RESUME; positions retained at the real PCB spacing')
view('keys_sockets.png',[n for n in printed if n.startswith(('04_','05_','06_','07_'))],(0,1,0),(.5,0,-.8660254),'Keycap underside | actuator sockets and retaining flanges','POWER uses a rectangular socket; the three momentary keys use circular sockets')
view('lightpipes_detail.png',['08_lightpipe_PWR','09_lightpipe_STATUS'],(.8660254,-.5,0),(.25,.4330127,.8660254),'Two clear lightpipes | displayed side by side','Left PWR, right STATUS | positions rearranged for inspection; optical material and LED height require testing',{'08_lightpipe_PWR':[-89.5,-43,0],'09_lightpipe_STATUS':[-75.5,-106,0]})
view('fit_template.png',['11_front_fit_template'],iso_u,iso_w,'1 mm front fit template','Print before full shells to check LCD window and key / lamp XY alignment')
view('exploded_reverse.png',all_parts,(.5,.8660254,0),(-.5,.2886751,.8164966),'Exploded assembly | opposite corner','M3 heads and nominal shanks included for the retainer; electronic reference envelopes are not print parts',shift)
fullmesh=mesh
for label,items in json.loads((ROOT/'.work/section-meshes.json').read_text()).items():
    mesh=items
    view('section_'+label+'.png',list(items),(1,0,0),(0,0,1),'CAD section | '+label,'Actual CAD section at PCB Y='+{'RESET':'57','POWER':'30','STATUS':'106','M3':'17'}[label]+' mm | nominal unmeasured screen Z stack; thread envelope is simplified')
mesh=fullmesh

# Actual local CAD crop shows the loading bay and the captured nut.
saved_mesh=mesh
mesh=json.loads((ROOT/'.work/nut-detail-meshes.json').read_text())
local_u=(1,0,0);local_w=(0,-.6,.8)
view('nut_pocket_empty.png',['02_upper_shell'],local_u,local_w,'C3 nut pocket | underside loading bay','Lift the nut into the open bay, then slide toward the hex seat; lower ledge takes screw tension')
view('nut_insert_1.png',['02_upper_shell','REF_retainer_M3_nut_1'],local_u,local_w,'1 | Place the M3 nut in the loading bay','Upper shell shown from inside; ordinary M3 hex nut AF5.5, height up to 2.4 mm',{'REF_retainer_M3_nut_1':[0,-8.5,.2]})
view('nut_insert_2.png',['02_upper_shell','REF_retainer_M3_nut_1'],local_u,local_w,'2 | Slide to the hexagonal seat','Hex walls stop rotation; the printed lower ledge prevents downward pull-out')
view('nut_insert_3.png',list(mesh),local_u,local_w,'3 | Fit the retainer and tighten M3 x 5','No tapping, heat insert or glue. Thread the metal nut; keep the shell flat during assembly')
mesh=saved_mesh
# A compact Chinese three-step instruction image uses only the CAD views above.
fontpath='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
canvas=Image.new('RGB',(2220,900),'white');paint=ImageDraw.Draw(canvas);big=ImageFont.truetype(fontpath,34);label=ImageFont.truetype(fontpath,24)
paint.text((35,20),'C3 免攻牙固定：放入螺母 → 平推到位 → 装固定板拧螺丝',font=big,fill='#203a4a')
for i,(file,caption) in enumerate([('nut_insert_1.png','① 从装入口放入普通 M3 六角螺母'),('nut_insert_2.png','② 平推到六角定位槽，贴住承力台阶'),('nut_insert_3.png','③ 放好键帽和导光柱，盖板拧 M3×5')]):
    pic=Image.open(OUT/file).convert('RGB');pic.thumbnail((700,650));x=25+i*735;canvas.paste(pic,(x+(700-pic.width)//2,125+(650-pic.height)//2));paint.text((x,795),caption,font=label,fill='#203a4a')
paint.text((35,850),'先装螺母再装固定板；槽内清理支撑残留。螺母共增加 4 颗，全套合计 15 颗。',font=label,fill='#536570');canvas.save(OUT/'nut_install_steps.png')

# Keep final previews tied to the geometry they display.
import hashlib
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT/'.work/render-record.json').write_text(json.dumps({'revision':json.loads((ROOT/'parameters.json').read_text())['revision'],'generator_geometry':json.loads((ROOT/'fit-check.json').read_text())['geometry_binding'],'renderer_sha256':sha(Path(__file__)),'images':{p.name:sha(p) for p in OUT.glob('*.png') if p.name not in ['00_overview.png','dimensions.png']}},indent=2)+'\n')
