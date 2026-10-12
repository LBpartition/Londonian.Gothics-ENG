from PIL import Image
im=Image.open('captures/route_dress/dress_f000634.png').convert('RGB')
W,H=im.size
def gold(p): r,g,b=p; return r>150 and g>110 and b<90
def white(p): return min(p)>200
for y in range(330,384,2):
    row=[im.getpixel((x,y)) for x in range(W)]
    whites=[x for x,p in enumerate(row) if white(p)]
    golds=[x for x,p in enumerate(row) if gold(p)]
    lg=[x for x in golds if x<128]; rg=[x for x in golds if x>128]
    print(y, 'white',(min(whites),max(whites)) if whites else None,'gold inner',(max(lg) if lg else None, min(rg) if rg else None))
