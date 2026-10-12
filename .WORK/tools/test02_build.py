import sys,struct
from pathlib import Path
sys.path.insert(0,'tools')
import test01_build as t
src=Path('builds/test01/TEST01-option-font-ruler.nds').read_bytes()
for adv in (12,11):
    r=bytearray(src)
    for o in (0x29FEC,0x2A104,0x2A230,0x2A348):
        p=0x4000+o; w=struct.unpack_from('<I',r,p)[0]
        assert w&0xFFF==14, hex(w)
        struct.pack_into('<I',r,p,(w&~0xFFF)|adv)
    out=Path(f'builds/test02/TEST02-adv{adv}.nds'); out.parent.mkdir(exist_ok=True); out.write_bytes(r); print(out)
