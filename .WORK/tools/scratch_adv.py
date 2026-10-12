import capstone,struct
d=open('extracted/arm9.bin','rb').read()
md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
# find all ARM 'add rX, rX, #imm' with imm in 8..16 near a ldrh within 0x200 bytes and a cmp to 0xffff literal
hits=[]
for o in range(0,len(d)-4,4):
    w=struct.unpack_from('<I',d,o)[0]
    # ADD Rd,Rn,#imm : cond 1110 001 0100 S Rn Rd rot imm8
    if (w & 0x0FF00000)==0x02800000 and (w>>28)==0xE:
        rn=(w>>16)&15; rd=(w>>12)&15; imm=w&0xFFF
        if rn==rd and imm in (0xc,0xd,0xe,0xf,0x10):
            hits.append((o,rd,imm))
# filter to functions with bl to sprite func 0x2029cb4 within +-0x200
def bls(o):
    r=[]
    for p in range(max(0,o-0x200),o+0x200,4):
        w=struct.unpack_from('<I',d,p)[0]
        if (w>>24)==0xEB:
            off=w&0xFFFFFF
            if off&0x800000: off-=0x1000000
            r.append(p+8+off*4)
    return r
for o,rd,imm in hits:
    t=bls(o)
    if 0x29cb4 in t or 0x2A1C4 in t: print(hex(o),'r%d'%rd,imm)
