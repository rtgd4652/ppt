"""把公共图集原样放入上半部，新增只供私人中央模块使用的低强度材料格。"""

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare_central_court_surface_v02 import dds_with_mips

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'art/models/aemusa_reality_refinement_v07/export'
OUT=ROOT/'art/models/aemusa_reality_identity_v08'
PERSONAL=(
    ('personal_dark',(39,24,40),(0,78,8,92),0),
    ('personal_wine',(79,30,53),(0,82,10,99),0),
    ('personal_gold',(158,127,78),(0,92,76,100),0),
    ('personal_signal',(158,67,108),(0,70,8,92),16),
)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pillow-dir',type=Path,default=ROOT/'temp/cc_surface_v02_deps')
    args=parser.parse_args()
    sys.path.insert(0,str(args.pillow_dir.resolve()))
    from PIL import Image,ImageDraw
    export=OUT/'export'
    export.mkdir(parents=True,exist_ok=True)
    maps={}
    for name,fill in (('diffuse',(24,38,48,255)),('properties',(0,80,6,92)),('normal',(128,128,0,128))):
        original=Image.open(SOURCE/('cc_surface_v05_'+name+'.dds')).convert('RGBA')
        image=Image.new('RGBA',(2048,2048),fill)
        image.paste(original,(0,0))
        assert image.crop((0,0,2048,1024)).tobytes()==original.tobytes()
        maps[name]=image
    # 第三排才是个人层；第四排保持备用公共底色，不映射到任何几何。
    for index,(role,color,properties,emission) in enumerate(PERSONAL):
        rect=(index*512,1024,index*512+511,1535)
        ImageDraw.Draw(maps['diffuse']).rectangle(rect,fill=(*color,255))
        ImageDraw.Draw(maps['properties']).rectangle(rect,fill=properties)
        ImageDraw.Draw(maps['normal']).rectangle(rect,fill=(128,128,emission,128))
    outputs=[]
    for name,img in maps.items():
        png=export/('reality_identity_v08_'+name+'.png')
        img.save(png)
        outputs.append(dds_with_mips(img,export/('reality_identity_v08_'+name+'.dds'),Image))
    report={'date':'2026-11-03','status':'draft_pending_human_review',
        'source':'art/models/aemusa_reality_refinement_v07/export/cc_surface_v05_*.dds',
        'style':'docs/art/characters/AEMUSA_STYLE.md, sections 4-9',
        'public_tiles_preserved_before_compression':True,
        'dds_note':'重新BC3编码，不能声称原公共DDS逐字节一致；其他四个部件仍直接使用旧DDS',
        'private_tiles':[{'index':i+8,'role':r,'rgb':c,'properties':p,'emission':e} for i,(r,c,p,e) in enumerate(PERSONAL)],
        'scope':'only flagship_mid; common hull/pods/hub have no personal colors',
        'original_game_reference_images_copied':False,'outputs':outputs}
    (OUT/'material_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('IDENTITY_V08_TEXTURES_OK three BC3 2048-square maps, 12 mips, four private tiles')


if __name__=='__main__':main()
