import capstone,sys
d=open('extracted/arm9.bin','rb').read()
base=0x02000000
lit=0x41764
for mode,name in [(capstone.CS_MODE_ARM,'ARM'),(capstone.CS_MODE_THUMB,'THUMB')]:
    md=capstone.Cs(capstone.CS_ARCH_ARM,mode)
    step=4 if name=='ARM' else 2
    refs=[]
    for start in range(lit-0x1000,lit,step):
        for ins in md.disasm(d[start:start+4],base+start):
            if ins.mnemonic.startswith('ldr') and 'pc' in ins.op_str and '#' in ins.op_str:
                try:
                    imm=int(ins.op_str.split('#')[1].rstrip(']'),0)
                except: continue
                pcv=(base+start+(8 if name=='ARM' else 4))
                if name=='THUMB': pcv&=~3
                if pcv+imm==base+lit: refs.append(hex(start))
            break
    print(name,refs)
