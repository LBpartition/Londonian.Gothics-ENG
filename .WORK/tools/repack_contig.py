"""Contiguous ndstool-style repack: arm9 @0x4000, arm7/FNT/FAT/banner/files shifted after it (no arm7-at-end relocation)."""
import struct,sys,os
sys.path.insert(0,os.path.dirname(__file__)); import ndsbuild
u=lambda b,o:struct.unpack_from('<I',b,o)[0]
def _fat(b): f=u(b,0x48); return [struct.unpack_from('<II',b,f+i*8) for i in range(u(b,0x4C)//8)]
def repack(O, src):
  a9=src[u(src,0x20):u(src,0x20)+u(src,0x2C)]
  end9=0x4000+len(a9)+12
  delta=(end9-u(O,0x30)+0x3FFF)//0x4000*0x4000 if end9>u(O,0x30) else 0
  r=bytearray(b'\xFF'*len(O)); r[:0x4000]=src[:0x4000]
  r[0x4000:end9]=a9+O[0x4000+u(O,0x2C):0x4000+u(O,0x2C)+12]
  for off,sz in ((0x30,0x3C),(0x40,0x44),(0x48,0x4C)):
    s=u(O,off); r[s+delta:s+delta+u(O,sz)]=O[s:s+u(O,sz)]; struct.pack_into('<I',r,off,s+delta)
  b=u(O,0x68); r[b+delta:b+delta+0x840]=O[b:b+0x840]; struct.pack_into('<I',r,0x68,b+delta)
  sf=_fat(src); of=_fat(O); fo=u(r,0x48); cur=0
  for i in sorted(range(len(of)),key=lambda i:of[i][0]):
    s,e=sf[i]; d=src[s:e]; ns=(max(cur,of[i][0]+delta)+0x1FF)//0x200*0x200
    r[ns:ns+len(d)]=d; struct.pack_into('<II',r,fo+i*8,ns,ns+len(d)); cur=ns+len(d)
  assert cur<=len(r)
  struct.pack_into('<I',r,0x80,max(cur,u(O,0x80)))
  struct.pack_into('<H',r,0x15E,ndsbuild.crc16_modbus(r[:0x15E])); return bytes(r)
