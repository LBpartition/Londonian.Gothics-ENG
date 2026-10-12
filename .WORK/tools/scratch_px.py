import sys; sys.path.insert(0,'tools')
import ndsbuild, test01_build as t1
rom=t1.ORIG.read_bytes(); fid=ndsbuild.file_ids_by_path(rom)["data/font.NCGR"]
f=ndsbuild.get_file(rom,fid)
for g in (0xAD,0xA1,0xB0,0xD4):
    px=t1.glyph_tiles(f[0x30+g*128:0x30+(g+1)*128])
    print(hex(g)); print('\n'.join(''.join('.123456789ABCDEF'[v] for v in r) for r in px))
