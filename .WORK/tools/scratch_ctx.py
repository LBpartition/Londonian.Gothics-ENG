import struct
d=open('extracted/arm9.bin','rb').read()
ctx=struct.unpack_from('<I',d,0x3F6C4)[0]; print('desc ctx',hex(ctx))
lits=[o for o in range(0,len(d)-3,4) if struct.unpack_from('<I',d,o)[0]==ctx]
print('lits',[hex(x) for x in lits])
