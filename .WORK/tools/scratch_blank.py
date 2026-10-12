import sys; sys.path.insert(0,'tools')
from pathlib import Path
d=Path('extracted/data/data/font.NCGR').read_bytes()
import struct
# find CHAR section
i=d.find(b'RAHC'); size=struct.unpack_from('<I',d,i+4)[0]
tiles=d[i+0x20:i+size]
n=len(tiles)//128
blank=[g for g in range(n) if not any(tiles[g*128:(g+1)*128])]
print('glyphs',n,'blank',[hex(b) for b in blank])
