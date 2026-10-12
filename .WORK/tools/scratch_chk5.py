from PIL import Image
from pathlib import Path
im=Image.open(sorted(Path('captures/test05_dress').glob('dress2_*.png'))[0]).convert('RGB')
for y0,y1 in ((336,352),(356,372)):
    xs=[x for y in range(y0,y1) for x in range(256) if min(im.getpixel((x,y)))>200]
    print('line ink x',min(xs),max(xs),'OK' if max(xs)<=200 else 'OVERFLOW')
im.crop((0,192,256,384)).resize((512,384),Image.NEAREST).save('captures/test05_zoom.png')
