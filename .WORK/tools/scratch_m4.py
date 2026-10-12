from PIL import Image
from pathlib import Path
c=Path('captures')
a=Image.open(sorted((c/'test04_option').glob('option2_*.png'))[0]).convert('RGB')
b=Image.open(sorted((c/'test04_dress').glob('dress_*.png'))[0]).convert('RGB')
W=Image.new('RGB',(512,384)); W.paste(a,(0,0)); W.paste(b,(256,0)); W=W.resize((1024,768),Image.NEAREST); W.save(c/'test04_compare.png')
