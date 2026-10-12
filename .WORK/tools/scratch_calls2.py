import struct
d=open('extracted/arm9.bin','rb').read()
targets={0x2E3F0:'getDesc',0x2E438:'getName'}
for o in range(0,len(d)-3,4):
    w=struct.unpack_from('<I',d,o)[0]
    if (w>>24)==0xEB:
        off=w&0xFFFFFF
        if off&0x800000: off-=0x1000000
        t=o+8+off*4
        if t in targets: print(hex(o),targets[t])
