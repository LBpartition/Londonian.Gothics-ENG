import sys,re; sys.path.insert(0,'tools')
import textfit, ndsbuild, font_patch, test01_build as t1
rom=t1.ORIG.read_bytes(); fid=ndsbuild.file_ids_by_path(rom)["data/font.NCGR"]
font=font_patch.patch_font(ndsbuild.get_file(rom,fid)); m=textfit.Metrics(font)
g=open('ref_guide.txt',encoding='utf-8').read()
sec=g[g.index("Alice's Dresses:"):g.index("Crafting the Dresses:")]
ent=re.findall(r'^(\d\d)\. (\S+)\s*: (.*?)(?=^\d\d\. |\Z)',sec,re.S|re.M)
box=textfit.DRESS_DESC
for n,name,desc in ent:
    desc=' '.join(desc.split())
    try: L=textfit.wrap(desc,box,m); r=f'fits {len(L)}'
    except textfit.FitError as e: r='needs '+str(e).split('needs ')[1].split(' ')[0]
    print(n,name.ljust(11),str(m.width(name,box)).rjust(3)+'px',r.ljust(9),desc)
