"""Build reproducible synthetic document scans; no real identity or government artwork."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent

def main():
    annotations=[]
    for key,title,number,kind,tint in [
        ('aadhaar','AADHAAR FORMAT','2345 6789 0123','IN_AADHAAR','#eaf1e9'),
        ('pan','PAN FORMAT','ABCDE1234F','IN_PAN','#e7eef6')]:
        im=Image.new('RGB',(760,310),'#f4f3ed');d=ImageDraw.Draw(im)
        font=lambda size:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',size)
        d.rounded_rectangle((10,10,750,300),radius=18,fill=tint,outline='#687d80',width=2)
        d.text((32,27),'SYNTHETIC SAMPLE - NOT VALID ID',font=font(29),fill='#9c2929')
        d.text((32,78),title+' / OCR DEMO',font=font(30),fill='#173b40')
        d.text((32,127),'Fictional identity • privacy test only',font=font(24),fill='#465d65')
        box=d.textbbox((32,180),number,font=font(52))
        d.text((32,180),number,font=font(52),fill='#111111')
        d.text((32,258),'No official logo, signature or machine-readable code',font=font(21),fill='#465d65')
        name='synthetic-'+key+'.png';im.save(ROOT/'assets'/name)
        annotations.append({'image':name,'kind':kind,'value':number,'bounds':list(box),'size':[760,310]})
    (ROOT/'docs'/'identity-image-annotations.json').write_text(json.dumps(annotations,indent=2),encoding='utf-8')
if __name__=='__main__': main()
