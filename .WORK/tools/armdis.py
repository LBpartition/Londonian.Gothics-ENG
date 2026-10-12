import capstone,sys
d=open('extracted/arm9.bin','rb').read()
md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
s,e=int(sys.argv[1],16),int(sys.argv[2],16)
for ins in md.disasm(d[s:e],0x02000000+s):
    print(f"{ins.address-0x02000000:06X} {ins.mnemonic:8} {ins.op_str}")
