# SPDX-License-Identifier: MIT
"""Build a local image gallery and contact sheet from verified C3 CAD renders."""
from pathlib import Path
import html,math,json
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];out=R/'preview'
items=[('assembled.png','装好后的外观'),('front.png','正面：键帽与指示灯'),('ports.png','另一角度：DC 与 SWD'),('exploded.png','装配爆炸图'),('exploded_reverse.png','反向装配爆炸图'),('dimensions.png','尺寸与高度基准'),('side_ETH_USB_CAN.png','网口、USB、CAN 侧面'),('side_DC.png','DC 电源侧面'),('side_SWD.png','SWD 侧面'),('side_vents.png','散热孔侧面'),('lower_inside.png','底壳内部支撑'),('lower_bottom.png','底部 M3 螺母槽'),('upper_inside.png','上壳内部总装'),('upper_bosses.png','上壳内部 M3 固定柱'),('retainer_M3.png','固定板与四颗 M3×5'),('nut_install_steps.png','免攻牙安装三步骤'),('nut_pocket_empty.png','侧插螺母槽与承力台阶'),('nut_insert_1.png','第一步：放入螺母'),('nut_insert_2.png','第二步：平推到位'),('nut_insert_3.png','第三步：盖板拧螺丝'),('keys_top.png','四个独立键帽'),('keys_sockets.png','键帽底部套孔'),('lightpipes_detail.png','两根独立导光柱'),('section_POWER.png','POWER 按键剖面'),('section_RESET.png','RESET 按键剖面'),('section_STATUS.png','状态灯导光柱剖面'),('section_M3.png','M3 固定点剖面'),('fit_coupon.png','轴套与 M3 孔试装块'),('fit_template.png','1 mm 薄前面板模板')]
assert all((out/name).is_file() for name,_ in items)
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';titlefont=ImageFont.truetype(font,30);label=ImageFont.truetype(font,19);small=ImageFont.truetype(font,13)
cols=4;tw,th=390,295;margin=25;rows=math.ceil(len(items)/cols);im=Image.new('RGB',(cols*tw+2*margin,rows*th+120),(245,247,248));draw=ImageDraw.Draw(im)
draw.text((margin,17),'InfraBot 外壳 C3 · 全 M3 · 免攻牙 · 图片总览',font=titlefont,fill=(28,51,65));draw.text((margin,62),f'共 {len(items)} 个视图；打开同目录 index.html 可点击查看大图。尺寸与实际配合仍以试装核验为准。',font=label,fill=(68,84,94))
html_cards=[]
for i,(name,caption) in enumerate(items):
 x=margin+(i%cols)*tw;y=110+(i//cols)*th;pic=Image.open(out/name).convert('RGB');pic.thumbnail((tw-16,th-65));draw.rectangle((x,y,x+tw-16,y+th-17),fill='white',outline=(218,225,230));im.paste(pic,(x+(tw-16-pic.width)//2,y+(th-65-pic.height)//2))
 draw.text((x+10,y+th-60),f'{i+1:02d}  {caption}',font=label,fill=(28,51,65));draw.text((x+10,y+th-33),name,font=small,fill=(89,103,112))
 html_cards.append(f'<a class="tile" href="{name}" target="_blank"><img src="{name}" loading="lazy" alt="{html.escape(caption)}"><div><strong>{i+1:02d} · {html.escape(caption)}</strong><small>{name}</small></div></a>')
im.save(out/'00_overview.png')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>InfraBot C3 全 M3 · 免攻牙 外壳预览</title><style>body{margin:0;background:#f3f5f6;color:#20394b;font:16px system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:26px;margin:0 0 10px}p{color:#536570;line-height:1.6}nav{display:flex;gap:24px;margin:18px 0}a{color:#245e7a}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:18px}.tile{display:flex;flex-direction:column;text-decoration:none;background:white;border:1px solid #d6dfe4}.tile img{width:100%;height:235px;object-fit:contain}.tile div{padding:12px 15px}.tile strong{display:block;font-size:16px}.tile small{display:block;color:#60727d;margin-top:5px}footer{margin-top:26px;color:#60727d}</style><main><h1>InfraBot 外壳 C3 · 全 M3 · 免攻牙</h1><p>16 mm 屏幕铜柱，138.4 × 108.4 × 34.55 mm 试装壳体。点击任一图片查看大图。剖面来自真实 CAD 切片；电子参考体与玻璃总高度含未实测假设。</p><nav><a href="00_overview.png">总览大图</a><a href="../README.md">装配说明</a><a href="../STEP/00_enclosure_assembly.step">总装 STEP</a></nav><div class="grid">'''+''.join(html_cards)+'''</div><footer>先打印轴套/M3 试装块与薄前面板模板，再打印整壳。C1/C2 归档保留为历史版，当前目录为 C3。</footer></main></html>'''
(out/'index.html').write_text(page)
(out/'README.md').write_text('# C3 外壳图片\n\n先打开 [可点击图片目录](index.html) 或 [总览图](00_overview.png)。\n\n'+ '\n'.join(f'- [{caption}]({name})' for name,caption in items)+'\n')
(out/'image-list.json').write_text(json.dumps([{'file':n,'caption':t} for n,t in items],ensure_ascii=False,indent=2)+'\n')
print(len(items),'views + 1 overview PNG')
