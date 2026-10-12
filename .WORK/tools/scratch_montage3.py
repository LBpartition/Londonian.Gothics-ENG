from PIL import Image, ImageDraw
from pathlib import Path
c=Path('captures'); ims=[]
for g in (1,2):
    ims.append(Image.open(sorted((c/f'test03_g{g}_option').glob('option2_*.png'))[0]).convert('RGB'))
    ims.append(Image.open(sorted((c/f'test03_g{g}_dress').glob('dress_*.png'))[0]).convert('RGB'))
W=Image.new('RGB',(256*4,384),'white')
for i,im in enumerate(ims): W.paste(im,(256*i,0))
W.save(c/'test03_compare.png')
rows=[]
for i in range(2):
    a=ims[i*2].crop((30,10,230,180)); b=ims[i*2+1].crop((0,0,256,40)); e=ims[i*2+1].crop((30,320,240,384))
    for x in (a,b,e): rows.append(x.resize((x.width*2,x.height*2),Image.NEAREST))
H=sum(r.height for r in rows); Z=Image.new('RGB',(max(r.width for r in rows),H),'white');y=0
for r in rows: Z.paste(r,(0,y)); y+=r.height
Z.save(c/'test03_zoom.png')
