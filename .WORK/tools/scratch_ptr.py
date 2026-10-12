import struct
d=open('extracted/arm9.bin','rb').read()
for name,t in [('OPTION',0x0204C3F0),('MSGSPD',0x0204C438),('BACKL',0x0204C450),('DRESSNAME',0x02048000),('DESC',0x02048290),('DRESSMAKE',0x0204BA78)]:
    hits=[hex(i) for i in range(0,len(d)-3,4) if struct.unpack_from('<I',d,i)[0]==t]
    print(name,hits)
# also nearby pointers into option table region
near=[(hex(i),hex(struct.unpack_from('<I',d,i)[0])) for i in range(0,len(d)-3,4) if 0x0204C3E0<=struct.unpack_from('<I',d,i)[0]<0x0204C530]
print('near option',near)
