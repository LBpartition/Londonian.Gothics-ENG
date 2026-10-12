from PIL import Image, ImageDraw
from pathlib import Path
c=Path('captures')
imgs=[('orig 14',sorted((c/'test01_option2').glob('option2_*.png'))[0]),('orig 14',c/'test01_dress/dress_f000634.png')]
for a in (12,11):
    imgs.append((f'adv {a}',sorted((c/f'test02_adv{a}_option').glob('option2_*.png'))[0]))
    imgs.append((f'adv {a}',sorted((c/f'test02_adv{a}_dress').glob('dress_*.png'))[0]))
W=Image.new('RGB',(256*6,384+14),'white');d=ImageDraw.Draw(W)
for i,(l,p) in enumerate(imgs):
    W.paste(Image.open(p).convert('RGB'),(256*i,14)); d.text((256*i+4,1),l,fill='black')
W.save(c/'test02_compare.png')
