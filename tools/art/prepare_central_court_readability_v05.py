"""沿现有RGB和发光遮罩校准涂层高光/金属度；不抬高全舰底色或让装甲发光。"""

import argparse
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_central_court_surface_v02 import dds_with_mips

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'art/models/central_court_surface_candidates_v03'
OUT = ROOT / 'art/models/central_court_readability_v05'
# G须经过原生G²×0.4；降低涂层B，避免过多漫反射能量转进金属反射。
PROPERTIES = {
    'armor': (0, 80, 6, 92), 'plate': (0, 84, 14, 106),
    'silver': (0, 95, 85, 104), 'warm': (0, 78, 4, 86),
    'glass': (0, 110, 2, 148), 'vent': (0, 65, 12, 70),
    'cyan': (0, 65, 18, 94), 'amber': (0, 60, 12, 88),
}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pillow-dir',type=Path,default=ROOT/'temp/cc_surface_v02_deps')
    args=parser.parse_args()
    sys.path.insert(0,str(args.pillow_dir))
    from PIL import Image, ImageDraw
    export=OUT/'export'
    export.mkdir(parents=True,exist_ok=True)
    # 两张原纹理仅换本批文件名，内容逐字节保持；normal.B发光边界不变。
    for suffix in ('diffuse','normal'):
        for extension in ('png','dds'):
            shutil.copy2(SOURCE/'export'/f'cc_surface_v03_{suffix}.{extension}',
                         export/f'cc_surface_v05_{suffix}.{extension}')
    old=json.loads((SOURCE/'surface_manifest.json').read_text(encoding='utf-8'))
    image=Image.new('RGBA',(2048,1024))
    draw=ImageDraw.Draw(image)
    records=[]
    for index,row in enumerate(old['palette']):
        role=row['role']
        value=PROPERTIES[role]
        x,y=index%4*512,index//4*512
        draw.rectangle((x,y,x+511,y+511),fill=value)
        records.append({'role':role,'rgb':row['rgb'],'old_properties':row['properties'],
                        'properties':list(value),'normal_emission_unchanged':row['emission'],
                        'dielectric_spec_remapped':round((value[1]/255)**2*.4,5),
                        'metalness_remapped':round(1-(1-value[2]/255)**2,5)})
    image.save(export/'cc_surface_v05_properties.png')
    texture=dds_with_mips(image,export/'cc_surface_v05_properties.dds',Image)
    result={'date':'2026-11-01','source_base':'2125b28','status':'draft_pending_human_review',
            'rgb_diffuse_bytes_unchanged':True,'normal_and_emission_bytes_unchanged':True,
            'properties_texture':texture,'palette':records,'runtime_installed':False,
            'reference':'docs/art/calibration/CENTRAL_COURT_MATERIAL_CALIBRATION.md',
            'shader_basis':'local 4.5.2 gfx/FX/pdxmesh_ship.fxh; no native media copied'}
    (OUT/'surface_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('CC_READABILITY_V05_TEXTURES_OK diffuse/normal identical, properties calibrated, full mips')


if __name__=='__main__':
    main()
