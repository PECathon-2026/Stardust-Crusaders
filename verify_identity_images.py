"""Real OCR regression: pixels only, no known-secret hints; requires fixture asset server."""
import asyncio, json, io
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from backend.privacy import Detector
from backend.browser import Browser
from backend.fixtures import fixture
ROOT=Path(__file__).resolve().parent

async def main():
    d=Detector();d.initialize();assert all(d.status.values()),d.status
    b=Browser(d);rows=[]
    annotations=json.loads((ROOT/'docs/identity-image-annotations.json').read_text())
    try:
        await b.open('http://127.0.0.1:8766/scenario/authentication')
        for width in [1050,1280]:
            for layout in [0,1]:
                await b.page.set_viewport_size({'width':width,'height':1000})
                page,_,_=fixture('authentication',11,layout)
                await b.page.set_content(page)
                await b.page.evaluate("async()=>{await Promise.all([...document.images].map(i=>i.decode()))}")
                text = await b.page.inner_text('body')
                assert not any(a['value'] in text for a in annotations)
                preview=await b.capture(known=(),mode='baseline')
                mask=Image.new('1',(width,1000));draw=ImageDraw.Draw(mask)
                for m in preview['masks']:
                    if m['source']=='ocr':draw.rectangle((m['x']-3,m['y']-3,m['x']+m['width']+3,m['y']+m['height']+3),fill=1)
                pixels=np.asarray(mask)
                for a in annotations:
                    rect=await b.page.locator('img[src$="'+a['image']+'"]').bounding_box()
                    x1,y1,x2,y2=a['bounds'];sx=rect['width']/a['size'][0];sy=rect['height']/a['size'][1]
                    left,top,right,bottom=round(rect['x']+x1*sx),round(rect['y']+y1*sy),round(rect['x']+x2*sx),round(rect['y']+y2*sy)
                    rate=float(pixels[top:bottom,left:right].mean())
                    rows.append({'viewport_width':width,'layout':layout,'kind':a['kind'],'ocr_coverage':round(rate,4),'passed':rate>=.98})
                all_masks=Image.new('1',(width,1000));all_draw=ImageDraw.Draw(all_masks)
                for m in preview['masks']:
                    all_draw.rectangle((m['x']-3,m['y']-3,m['x']+m['width']+3,m['y']+m['height']+3),fill=1)
                all_pixels=np.asarray(all_masks)
                portraits=b.page.locator('.identity-portrait')
                assert await portraits.count()==2
                for i in range(2):
                    r=await portraits.nth(i).bounding_box()
                    x,y,right,bottom=round(r['x']),round(r['y']),round(r['x']+r['width']),round(r['y']+r['height'])
                    rate=float(all_pixels[y:bottom,x:right].mean())
                    rows.append({'viewport_width':width,'layout':layout,'kind':'PRIVATE_PORTRAIT','coverage':round(rate,4),'passed':rate>=.98})
                if width==1050 and layout==0:
                    (ROOT/'docs/identity-images-original.png').write_bytes(await b.page.screenshot())
                    (ROOT/'docs/identity-images-sanitized.png').write_bytes(b.png)
                print(json.dumps(rows[-4:]),flush=True)
        report={'scope':'Synthetic clean card scans at two viewport widths and two layouts. Identifier coverage uses OCR masks only; portraits use explicit private-region masks. Known-value hints empty. Not a guarantee for arbitrary photographs.','cases':rows,'passed':all(r['passed'] for r in rows)}
        (ROOT/'docs/identity-image-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        assert report['passed'], 'OCR did not cover all annotated identifier pixels'
    finally:await b.close()
if __name__=='__main__':asyncio.run(main())
