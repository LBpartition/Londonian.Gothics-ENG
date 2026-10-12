from PIL import Image
W=Image.open('captures/test02_compare.png')
rows=[]
for i in range(3):
    a=W.crop((256*i*2+40,14+90,256*i*2+220,14+150)); b=W.crop((256*(i*2+1)+30,14+340,256*(i*2+1)+230,14+384))
    rows+= [a.resize((a.width*3,a.height*3),Image.NEAREST), b.resize((b.width*3,b.height*3),Image.NEAREST)]
H=sum(r.height for r in rows); out=Image.new('RGB',(max(r.width for r in rows),H),'white'); y=0
for r in rows: out.paste(r,(0,y)); y+=r.height
out.save('captures/test02_zoom.png')
