import capstone,struct
d=open('extracted/arm9.bin','rb').read()
md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
lits={}
for o in range(0,len(d)-3,4):
    v=struct.unpack_from('<I',d,o)[0]
    if 0x02048000<=v<0x02048D20: lits.setdefault(v,[]).append(o)
for v,os_ in sorted(lits.items()): print(hex(v),[hex(x) for x in os_])
refs=[]
for lit in [o for os_ in lits.values() for o in os_]:
    for s in range(lit-0x1000,lit,4):
        w=struct.unpack_from('<I',d,s)[0]
        if (w&0x0F7F0000)==0x051F0000:  # ldr rX,[pc,#imm]
            imm=w&0xFFF; 
            if s+8+imm==lit: refs.append((s,lit))
for s,l in refs: print('ref',hex(s),'->lit',hex(l))
