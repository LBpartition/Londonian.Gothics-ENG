import struct
d=open('extracted/arm9.bin','rb').read()
lit=0x3FCE0
for s in range(lit-0x1000,lit,4):
    w=struct.unpack_from('<I',d,s)[0]
    if (w&0x0F7F0000)==0x051F0000 and s+8+(w&0xFFF)==lit: print(hex(s))
