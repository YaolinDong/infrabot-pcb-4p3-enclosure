# SPDX-License-Identifier: MIT
"""Reference dimensions and mounting plan for the two-part simple enclosure."""
from pathlib import Path
import json,html,math
import ezdxf
R=Path(__file__).resolve().parents[1];p=json.loads((R/'.work/resolved-parameters.json').read_text());d=p['derived'];s=p['simple_controls'];m=p['mounts'];margin=p['case']['edge_margin'];out=R/'preview'
rev=p['revision'].split('_')[-1];deck=s['deck_z'];th=s['deck_thickness'];face=d['face_top_z'];inside=d['face_bottom_z']
font='Noto Sans CJK SC,sans-serif'
def txt(a,x,y,t,size=20,color='#244151',anchor='start'):a.append(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{html.escape(str(t))}</text>')
def start(w,h):return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>']
def rect(a,x,y,w,h,fill,stroke,dash=''):a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="1.5" stroke-dasharray="{dash}"/>')
# Human-view map: +Y right, +X down. Green = female-female spacers; orange = the three required nuts.
a=start(1250,1000);txt(a,35,42,f'{rev} 简版 · 7 个固定点（从 PCB 元件面看）',28);txt(a,35,75,'只需上下壳两件；绿点为 16 mm 铜柱，橙点为右侧上壳螺丝，灰点仅作支承。',19)
scale=5.6;ox,oy=60,120;xy=lambda x,y:(ox+(y+margin)*scale,oy+(x+margin)*scale)
rect(a,ox,oy,(130+2*margin)*scale,(100+2*margin)*scale,'#f0f4f6','#2e5366')
xx,yy=xy(0,0);rect(a,xx,yy,130*scale,100*scale,'none','#93a4af','6 4')
a0,b0,c0,d0=p['lcd']['pcb_bbox'];xx,yy=xy(a0,b0);rect(a,xx,yy,(d0-b0)*scale,(c0-a0)*scale,'#e4eef2','#8ba6b7','5 4')
for label,points,color in [('LCD',m['lcd'],'#2a9062'),('CASE',m['case'],'#bd772c'),('CORE',m['core'],'#9da7ad')]:
 for i,(x,y) in enumerate(points):
  xx,yy=xy(x,y);a.append(f'<circle cx="{xx}" cy="{yy}" r="{3*scale}" fill="white" stroke="{color}" stroke-width="4"/>');text=label+str(i+1 if label!='CASE' else i+9);txt(a,xx+22,yy+6,text,16,color)
for ref in ['SW1','SW2','SW3','SW4','LED1','LED2']:
 x,y=p['controls'][ref];xx,yy=xy(x,y);a.append(f'<circle cx="{xx}" cy="{yy}" r="8" fill="#4d6674"/>');txt(a,xx,yy-16,ref,14,anchor='middle')
for y,t in [(160,'4 × M3×12：共用屏幕/上壳固定'),(205,'7 × M3×10：底面 4 + CASE 3'),(250,'3 × M3 六角螺母：只在 CASE'),(295,'4 × M3、16 mm 双通铜柱'),(360,'CORE 灰点不要求装螺母/螺丝'),(405,'S8：11 颗螺丝，3 颗螺母')]:txt(a,870,y,t,18)
txt(a,60,790,'底壳实际有 11 个支承位置；默认只用其中 7 个固定，另外 4 个继续托住 PCB。',20)
txt(a,60,835,'装三颗螺母 → 底面四颗螺丝固定 PCB 和双通铜柱 → 装模块与屏幕 → 上方七颗螺丝合壳。',18)
txt(a,60,885,'铜柱下端由 M3×10 从底面锁入；不在塑料上攻牙。CASE9 是 DC 旁前侧敞开、孔沿圆润的低沉孔。',19)
txt(a,60,940,'此图为顶视定位参考；从底壳外侧装螺母时，注意左右方向翻转。',18,'#9b552e');a.append('</svg>');(out/'mounting-plan.svg').write_text(''.join(a))
# Side height sketch, controls use their real unextended actuators.
a=start(1400,850);txt(a,35,42,f'{rev} 简版 · 高低台阶与原件露出高度',29);txt(a,35,76,'以底板顶面 Z=0 为基准。16 mm 铜柱保持不变；屏幕总高度仍为暂定值。',20)
base=650;sc=10;xx=lambda x:55+(x+margin)*10;zz=lambda z:base-z*sc
rect(a,xx(-margin),zz(-6.6),(100+2*margin)*10,2.4*sc,'#435462','#435462')
rect(a,xx(0),zz(0),100*10,1.6*sc,'#438367','#438367')
rect(a,xx(2.9),zz(17.6),69.2*10,1.6*sc,'#438367','#438367');rect(a,xx(3.95),zz(d['glass_top_z']),67.1*10,(d['glass_top_z']-17.6)*sc,'#b3c6d1','#66879b')
rect(a,xx(-margin),zz(face),(s['step_x']+margin)*10,2.4*sc,'#aebec8','#758f9e')
rect(a,xx(s['step_x']-2.4),zz(inside),2.4*10,(inside-(deck-th))*sc,'#aebec8','#758f9e')
rect(a,xx(s['step_x']),zz(deck),(100+margin-s['step_x'])*10,2*sc,'#aebec8','#758f9e')
rect(a,xx(86.25),zz(17),6.5*10,(17-3.5)*sc,'#263238','#263238')
txt(a,1110,180,f'屏幕面板 Z={face:.2f}',18);txt(a,1110,225,'原轻触按杆 Z=17.00',18);txt(a,1110,270,f'低台阶 Z={deck:.2f}',18);txt(a,1110,315,'板顶 Z=0',18);txt(a,1110,360,'底壳底 Z=−9.00',18)
txt(a,55,160,'整壳：138.4 × 108.4 × 34.55 mm（宽×高×最大厚度）',22)
txt(a,55,200,f'STOP / RESUME：原按杆高出台阶约 {s["momentary_height"]-deck:.1f} mm；POWER 高出护座约 3.9 mm。',19)
txt(a,55,235,'RESET 的一体护圈顶面 Z=18，原按杆低于护圈 1 mm；无独立键帽。',19)
txt(a,55,275,'LED1：灯顶约 Z=5.50，与低台阶基本齐平；LED2：灯顶约 Z=11.70。',19)
txt(a,55,315,'POWER 护座 Z=10.2；接缝 Z=3。沿用外沿 R0.8–1、台阶底 R1.5、RESET 口沿 R0.4。',18)
txt(a,55,770,'上壳为一个完整打印件。台阶、护座、护圈需由打印方合理加支撑；清理后验证孔位和按压。',19,'#9b552e');a.append('</svg>');(out/'dimensions.svg').write_text(''.join(a))
doc=ezdxf.new('R2010');doc.units=ezdxf.units.MM;sp=doc.modelspace()
for name,col in [('OUTLINE',7),('SCREEN_FACE',4),('CONTROL_DECK',3),('MOUNTS',2),('NOTES',7)]:doc.layers.new(name,dxfattribs={'color':col})
def line_rect(bounds,layer):
 x0,y0,x1,y1=bounds;sp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],close=True,dxfattribs={'layer':layer})
line_rect([-margin,-margin,100+margin,130+margin],'OUTLINE');line_rect([6.55,17,63.45,115],'SCREEN_FACE')
sp.add_line((s['step_x'],-margin),(s['step_x'],130+margin),dxfattribs={'layer':'CONTROL_DECK'})
for ref in ['SW1','SW2','SW3','SW4','LED1','LED2']:
 x,y=p['controls'][ref]
 if ref=='SW1':line_rect([x-5,y-5,x+5,y+5],'CONTROL_DECK')
 else:
  dia=s['reset_guard']['inner_diameter'] if ref=='SW2' else s['LED1_hole_diameter'] if ref=='LED1' else s['LED2_hole_diameter'] if ref=='LED2' else s['momentary_hole_diameter'];sp.add_circle((x,y),dia/2,dxfattribs={'layer':'CONTROL_DECK'})
for x,y in m['lcd']+m['case']:sp.add_circle((x,y),1.7,dxfattribs={'layer':'MOUNTS'})
for i,t in enumerate([f'{rev} SIMPLE TWO-PIECE / mm / TOP VIEW IN PCB COORDINATES',f'SCREEN FACE Z{face:g} / CONTROL DECK Z{deck:g} / NO PRINTED KEYCAPS OR LIGHTPIPES','11 M3 SCREWS +3 NUTS +4 FEMALE-FEMALE SPACERS16; ACTUAL LCD HEIGHT TBD','DXF FOR REFERENCE ONLY; USE STEP SOLIDS FOR 3D PRINTING']):sp.add_text(t,dxfattribs={'height':1.7,'insert':(0,-9-i*4),'layer':'NOTES'})
doc.saveas(R/'STEP/layout_reference_mm.dxf')
# Render the dimension sheets as PNGs as part of the repeatable workflow.
import subprocess
for filename in ['dimensions','mounting-plan']:
    subprocess.run(['/usr/bin/python3','-c',"import gi,sys;gi.require_version('Rsvg','2.0');from gi.repository import Rsvg;import cairo;h=Rsvg.Handle.new_from_file(sys.argv[1]);d=h.get_dimensions();s=cairo.ImageSurface(cairo.FORMAT_ARGB32,d.width,d.height);h.render_cairo(cairo.Context(s));s.write_to_png(sys.argv[2])",str(out/(filename+'.svg')),str(out/(filename+'.png'))],check=True)
print('Simple dimensions, PNGs and mounting plan written')
