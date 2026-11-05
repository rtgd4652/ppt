"""将本轮原创图集与Blender星空烘焙转为独立BC3 DDS，不复制原作媒体。"""

import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art/models/aemusa_endgame_runtime_v03'
EXPORT=OUT/'export'
sys.path.insert(0,str(ROOT/'temp/cc_surface_v02_deps'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from PIL import Image,ImageDraw
from prepare_central_court_surface_v02 import dds_with_mips


def main():
    EXPORT.mkdir(parents=True,exist_ok=True)
    # 材质颜色按当前候选重新建立；法线/属性为数据贴图，不是图像风格重绘。
    palette=[('navy',(39,50,78),(0,72,25,95),0),
             ('navy_light',(55,70,101),(0,80,35,105),0),
             ('silver',(184,198,218),(0,105,75,115),0),
             ('silver_shadow',(128,148,179),(0,85,55,105),0),
             ('inner',(18,27,46),(0,60,20,90),0),
             ('gold',(192,167,112),(0,95,70,110),72),
             ('cyan',(100,179,197),(0,70,25,100),90),
             ('socket',(10,16,29),(0,55,15,80),0)]
    atlas={key:Image.new('RGBA',(1024,512)) for key in ('diffuse','normal','properties')}
    for index,(_,rgb,properties,emission) in enumerate(palette):
        x=(index%4)*256;y=(index//4)*256
        bounds=(x,y,x+255,y+255)
        ImageDraw.Draw(atlas['diffuse']).rectangle(bounds,fill=(*rgb,255))
        # Stellaris解包：G=X、A=-Y、B=发光；R为保留通道。
        ImageDraw.Draw(atlas['normal']).rectangle(bounds,fill=(0,128,emission,128))
        ImageDraw.Draw(atlas['properties']).rectangle(bounds,fill=properties)
    records=[]
    for suffix,img in atlas.items():
        img.save(EXPORT/f'aef03_hull_{suffix}.png')
        records.append(dds_with_mips(img,EXPORT/f'aef03_hull_{suffix}.dds',Image))
    star=Image.open(EXPORT/'aef03_star_diffuse.png').convert('RGBA')
    assert star.size==(1024,1024)
    star.putalpha(255)
    # 星空用完全发光的独立材质；实体设置关闭帝国色重染。
    maps={'diffuse':star,'normal':Image.new('RGBA',star.size,(0,128,255,128)),
          'properties':Image.new('RGBA',star.size,(0,15,0,20))}
    for suffix,img in maps.items():
        img.save(EXPORT/f'aef03_star_{suffix}.png')
        records.append(dds_with_mips(img,EXPORT/f'aef03_star_{suffix}.dds',Image))
    (OUT/'textures_manifest.json').write_text(json.dumps({'status':'dds_ready_runtime_unobserved',
        'origin':'原创材质分区及v02程序化星空的Blender EMIT烘焙','textures':records,
        'palette_roles':[p[0] for p in palette],'emission_recolor_crunch_required':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ENDGAME_DDS_READY '+json.dumps(records,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
