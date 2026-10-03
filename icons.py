from PIL import Image,ImageDraw,ImageFont
import glob
FC="/tmp/ptn.ttf"; FL="/tmp/ptn_lat.ttf"
BG=(85,70,138); INK=(236,232,246); DARK=(22,21,29)
def emblem(size,pad_ratio,bg=None,round_=False):
    S=1024; im=Image.new("RGBA",(S,S),(0,0,0,0) if bg is None else bg+(255,))
    if round_:
        im=Image.new("RGBA",(S,S),(0,0,0,0)); ImageDraw.Draw(im).ellipse([0,0,S,S],fill=BG+(255,))
    layer=Image.new("RGBA",(S,S),(0,0,0,0)); ld=ImageDraw.Draw(layer)
    m=int(S*pad_ratio); box=[m,m,S-m,S-m]; w=max(6,int(S*0.035))
    ld.rounded_rectangle(box,radius=int(S*0.05),outline=INK,width=w)
    g=int(S*0.04); ld.rounded_rectangle([box[0]+g,box[1]+g,box[2]-g,box[3]-g],radius=int(S*0.04),outline=INK,width=max(4,w//2))
    inner=box[2]-box[0]; cx=S//2
    ld.text((cx,box[1]+inner*0.44),"С",font=ImageFont.truetype(FC,int(inner*0.66)),fill=INK,anchor="mm")
    ld.text((cx,box[1]+inner*0.8),"2096",font=ImageFont.truetype(FL,int(inner*0.2)),fill=INK,anchor="mm")
    layer=layer.rotate(6,resample=Image.BICUBIC,center=(cx,cx)); im.alpha_composite(layer)
    return im.resize((size,size),Image.LANCZOS)
res="android/app/src/main/res"
for d,(s,fg) in {"mdpi":(48,108),"hdpi":(72,162),"xhdpi":(96,216),"xxhdpi":(144,324),"xxxhdpi":(192,432)}.items():
    emblem(s,0.2,bg=BG).save(f"{res}/mipmap-{d}/ic_launcher.png")
    emblem(s,0.22,round_=True).save(f"{res}/mipmap-{d}/ic_launcher_round.png")
    emblem(fg,0.3).save(f"{res}/mipmap-{d}/ic_launcher_foreground.png")
open(f"{res}/values/ic_launcher_background.xml","w").write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#55468A</color>\n</resources>\n')
for f in glob.glob(f"{res}/drawable*/splash.png"):
    W,H=Image.open(f).size
    im=Image.new("RGB",(W,H),DARK); e=emblem(int(min(W,H)*0.42),0.18)
    im.paste(e,((W-e.width)//2,(H-e.height)//2-int(H*0.04)),e)
    d=ImageDraw.Draw(im)
    d.text((W//2,(H+e.height)//2),"Сумрак",font=ImageFont.truetype(FC,max(14,int(min(W,H)*0.08))),fill=(200,192,230),anchor="mt")
    im.save(f)
emblem(512,0.2,bg=BG).save("/home/claude/s/icon_preview.png")
emblem(512,0.3).save("/home/claude/s/icon_fg_preview.png")
Image.open(f"{res}/drawable-port-xhdpi/splash.png").resize((360,640)).save("/home/claude/s/splash_preview.png")
