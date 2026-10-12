from PIL import Image
from pathlib import Path
im=Image.open(sorted(Path('captures/test04_dress').glob('dress_*.png'))[0]).convert('RGB')
for y0,y1 in ((336,352),(356,372)):
    xs=[x for y in range(y0,y1) for x in range(256) if min(im.getpixel((x,y)))>200]
    print(y0,min(xs),max(xs))
# frame inner edge detail on row 345 orig
o=Image.open('captures/route_dress/dress_f000634.png').convert('RGB')
print([ (x,o.getpixel((x,345))) for x in range(196,212)])
