# SPDX-License-Identifier: MIT
"""Dimensions and nominal height stack for the R8 S16 fit prototype."""
import json,math,html
from pathlib import Path
import ezdxf
R=Path(__file__).resolve().parents[1];p=json.loads((R/'.work/resolved-parameters.json').read_text());c=p['case'];d=p['derived'];m=p['mounts'];margin=c['edge_margin'];W,H=100+2*margin,130+2*margin
out=R/'preview';doc=ezdxf.new('R2010');doc.units=ezdxf.units.MM
for name,col in [('CASE',7),('PCB_REFERENCE',8),('WINDOW_BOTTOM',4),('WINDOW_TOP',5),('GLASS_REFERENCE',8),('KEY_OPENINGS',1),('LIGHTPIPES',3),('COVER_SCREWS',2),('PCB_MOUNTS',8),('RETAINER_M3',6),('NOTES',7)]:doc.layers.new(name,dxfattribs={'color':col})
sp=doc.modelspace()
def rect(x0,y0,x1,y1,r,layer):
 b=math.tan(math.pi/8);pts=[(x0+r,y0,0),(x1-r,y0,b),(x1,y0+r,0),(x1,y1-r,b),(x1-r,y1,0),(x0+r,y1,b),(x0,y1-r,0),(x0,y0+r,b)];sp.add_lwpolyline(pts,format='xyb',close=True,dxfattribs={'layer':layer})
rect(-margin,-margin,100+margin,130+margin,c['corner_radius'],'CASE');rect(0,0,100,130,.25,'PCB_REFERENCE')
a,b,cc,dd=p['lcd']['glass_bbox'];rect(a,b,cc,dd,.4,'GLASS_REFERENCE');a,b,cc,dd=p['lcd']['lens_window_bbox'];e=p['lcd']['window_extra_each_side'];window=[a-e,b-e,cc+e,dd+e];rect(*window,1,'WINDOW_BOTTOM');rect(window[0]-.8,window[1]-.8,window[2]+.8,window[3]+.8,1.8,'WINDOW_TOP')
for ref in ['SW1','SW2','SW3','SW4']:
 x,y=p['controls'][ref];h=p['keys']['opening_size']/2;rect(x-h,y-h,x+h,y+h,p['keys']['cap_corner']+.2,'KEY_OPENINGS')
 sp.add_text(ref,dxfattribs={'height':1.5,'insert':(x-7,y),'rotation':90,'layer':'NOTES'})
for ref in ['LED1','LED2']:
 x,y=p['controls'][ref];sp.add_circle((x,y),p['lightpipes']['hole_diameter']/2,dxfattribs={'layer':'LIGHTPIPES'})
for x,y in m['lcd']+m['core']+m['case']:sp.add_circle((x,y),1.6,dxfattribs={'layer':'PCB_MOUNTS'})
for x,y in m['top_lcd_fasteners']+m['top_case_fasteners']:
 sp.add_circle((x,y),1.7,dxfattribs={'layer':'COVER_SCREWS'});sp.add_circle((x,y),3.1,dxfattribs={'layer':'COVER_SCREWS'})
for x,y in p['keys']['retainer_screws']:
 sp.add_circle((x,y),1.7,dxfattribs={'layer':'RETAINER_M3'});rect(x-3.7,y-4.5,x+3.7,y+4.5,.4,'RETAINER_M3');rect(x-3.7,y-12,x+3.7,y-4.4,.2,'RETAINER_M3')
for i,t in enumerate(['R8 S16 C3 NUT / mm / PCB X100 Y130','CASE X108.4 Y138.4; SHELL HEIGHT 34.55 (EXCLUDING KEY PROTRUSION)','SCREEN STANDOFF BODY 16; GLASS Z22.65 ASSUMED; MEASURE BEFORE FULL PRINT','WINDOW BOTTOM 56.9 x98.0; TOP CHAMFER +0.8 EACH SIDE','REFERENCE DXF: USE STEP SOLIDS FOR PRODUCTION; ACTUAL FIT NOT YET VERIFIED']):sp.add_text(t,dxfattribs={'height':1.7,'insert':(-margin,-10-i*4),'layer':'NOTES'})
doc.saveas(R/'STEP/layout_reference_mm.dxf')
# Human-view plan: user horizontal axis follows PCB +Y; vertical follows PCB +X.
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1050" viewBox="0 0 1500 1050"><rect width="100%" height="100%" fill="white"/>'];scale=5.5;ox,oy=50,100
xy=lambda x,y:(ox+(y+margin)*scale,oy+(x+margin)*scale)
def text(x,y,t,size=18,color='#263e4b',anchor='start'):
 s.append(f'<text x="{x}" y="{y}" font-family="Noto Sans CJK SC,sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}">{html.escape(str(t))}</text>')
def planrect(bounds,fill,stroke,dash='',radius=0):
 a,b,cc,dd=bounds;xx,yy=xy(a,b);s.append(f'<rect x="{xx}" y="{yy}" width="{(dd-b)*scale}" height="{(cc-a)*scale}" rx="{radius*scale}" fill="{fill}" stroke="{stroke}" stroke-width="1.4" stroke-dasharray="{dash}"/>')
def circle(x,y,r,color):
 a,b=xy(x,y);s.append(f'<circle cx="{a}" cy="{b}" r="{r*scale}" fill="white" stroke="{color}" stroke-width="1.5"/>')
text(50,40,'InfraBot R8 · 16 mm 铜柱外壳 C3 / 免攻牙 · 尺寸与高度基准',28)
text(50,72,'试装版：XY 来自工程/厂家图；完整装配 Z 高度未知。全部尺寸单位 mm。',18)
planrect([-margin,-margin,100+margin,130+margin],'#eff3f5','#345063',radius=c['corner_radius']);planrect([0,0,100,130],'none','#a1aeb5','5 5');planrect(p['lcd']['glass_bbox'],'none','#8ba4b4','5 4',.4);planrect(window,'#dce8ef','#39748f',radius=1)
for ref,label,color in [('SW1','POWER','#53616c'),('SW2','RESET','#b7bfc3'),('SW3','STOP','#d44747'),('SW4','RESUME','#56a676')]:
 x,y=p['controls'][ref];planrect([x-9,y-9,x+9,y+9],color,'#3b5663',radius=1.6);a,b=xy(x,y);text(a,b+5,label,16,'white' if ref!='SW2' else '#263e4b','middle');text(a,b+20,f'Y={y:g}',12,'white' if ref!='SW2' else '#263e4b','middle')
for ref,label in [('LED1','PWR'),('LED2','STATUS')]:
 x,y=p['controls'][ref];circle(x,y,1.7,'#267693');a,b=xy(x-5,y);text(a,b,label,12,anchor='middle')
for x,y in m['top_lcd_fasteners']+m['top_case_fasteners']:circle(x,y,3.1,'#a66b2e');circle(x,y,1.7,'#a66b2e')
a,b=xy(35,66);text(a,b-10,'4.3 寸屏幕',26,anchor='middle');text(a,b+20,'窗口 98.0 × 56.9',20,anchor='middle');text(a,b+45,'玻璃参考 105.4 × 67.1',17,anchor='middle')
text(ox+H*scale/2,oy+W*scale+32,'外形宽 138.4  ·  高 108.4（正常看屏幕方向）',19,anchor='middle')
# Height stack at right: separated, labelled blocks with true Z scale.
base_x=950;zscale=12;zero=690
zz=lambda z:zero-z*zscale
for name,z0,z1,color,width in [('底壳底板',-9,-6.6,'#8998a4',410),('底板 PCB',-1.6,0,'#588b6f',360),('核心板参考包络',6,14,'#b9cfc3',240),('16 mm 铜柱',0,16,'#c4a15e',25),('屏幕转接 PCB',16,17.6,'#588b6f',330),('LCM / 胶层参考',17.6,21.6,'#bbc7ce',300),('触摸玻璃',21.6,22.65,'#76a3b5',300),('上壳面板',23.15,25.55,'#8998a4',410)]:
 xx=base_x+(410-width)/2;s.append(f'<rect x="{xx}" y="{zz(z1)}" width="{width}" height="{(z1-z0)*zscale}" fill="{color}" stroke="white"/>')
text(base_x,140,'Z 高度链（底板顶面为 0）',23)
for y,t in [(182,'屏幕铜柱：16.00（用户指定）'),(213,'玻璃表面：22.65（暂定）'),(244,'面板内面：23.15'),(275,'面板外面：25.55'),(306,'底壳外面：−9.00')]:text(base_x,y,t,18)
text(base_x,838,'壳体总厚 34.55；不含突出键帽',18)
text(base_x,868,'POWER 高出面板 3.5；STOP/RESUME 1.0',16)
text(base_x,897,'RESET 低于面板 1.5；灯柱高出 0.3',16)
text(50,785,'固定：左侧两孔穿过屏幕 PCB 锁入 16 mm 铜柱；右侧两孔使用 CASE10/11。',18)
text(50,817,'CASE9 仅把底板锁到底壳；不设上壳立柱。11 处底壳支撑均对应现有安装孔。',18)
text(50,855,'接口：RJ45、USB-C/CAN、DC、SWD；CAN 先接线后合壳。USB 与 CAN 共用开口边界。',17)
text(50,887,'名义净空：网口顶面到屏幕 PCB 2.16；闲置屏幕排针到裸 SWD 4.96。',17)
text(50,931,'先打印 10_fit_coupon 和 11_front_fit_template，验证套孔、屏幕窗口与实际玻璃高度。',19,'#9b542c')
text(50,1005,'C3：内部 M3×5 配侧插六角螺母；槽对边5.9、高2.8，承力底台0.8；免攻牙。',17)
text(50,966,'导光柱需透明材料；外壳不是防水设计。配对插头、核心板最高件和打印公差仍需实装核验。',17)
s.append('</svg>');(out/'dimensions.svg').write_text(''.join(s))
print('Dimension SVG and DXF written')
