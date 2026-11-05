"""跨文件核对16T设计、供能、真实PDX定位器与运行贴图；不替代游戏验收。"""

import json
import math
from pathlib import Path
import re
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('F:/steam/steamapps/common/Stellaris')
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(ROOT/'tools/art'))
from check_mod import parse,scalar
from inspect_external_mesh_counts import load_reader


def load(path):return parse(path.read_text(encoding='utf-8-sig'))
def blocks(path,key):return [e.value for e in load(path) if e.key==key and isinstance(e.value,list)]
def children(block,key):return [e.value for e in block if e.key==key and isinstance(e.value,list)]


def main():
    sections={scalar(b,'key'):b for b in blocks(ROOT/'mod/common/section_templates/aemusa_reality_flagship_sections.txt','ship_section_template')}
    designs=blocks(ROOT/'mod/common/global_ship_designs/aemusa_reality_flagship_designs.txt','ship_design')
    assert len(designs)==1
    design=designs[0]
    assert scalar(design,'ship_size')=='aemusa_reality_flagship'
    weapons={scalar(b,'key'):b for b in blocks(ROOT/'mod/common/component_templates/aemusa_endgame_flagship_components.txt','weapon_component_template')}
    powercores={scalar(b,'key'):b for b in blocks(ROOT/'mod/common/component_templates/aemusa_endgame_flagship_components.txt','utility_component_template')}
    weapon=weapons['AEMUSA_ENDGAME_T_BEAM'];reactor=powercores['AEMUSA_ENDGAME_REACTOR']
    assert scalar(weapon,'size')=='titanic'
    for component in (weapon,reactor):
        assert scalar(children(component,'potential')[0],'is_ship_size')=='aemusa_reality_flagship'
    native_slots={e.key:e.value for e in load(GAME/'common/component_slot_templates/00_component_slots_fixed.txt') if isinstance(e.value,list)}
    assert scalar(native_slots['invisible_titanic_fixed'],'size')=='titanic'
    assert scalar(native_slots['invisible_titanic_fixed'],'is_fixed')=='yes'
    component_counts={};binding=[]
    for block in children(design,'section'):
        template=scalar(block,'template');section=sections[template]
        assert scalar(section,'ship_size')=='aemusa_reality_flagship'
        assert scalar(section,'fits_on_slot')==scalar(block,'slot')
        slots={scalar(s,'name'):s for s in children(section,'component_slot')}
        for fitted in children(block,'component'):
            name=scalar(fitted,'slot');key=scalar(fitted,'template');component_counts[key]=component_counts.get(key,0)+1
            if name.startswith('TITANIC_GUN_'):
                assert key=='AEMUSA_ENDGAME_T_BEAM'
                assert scalar(slots[name],'template')=='invisible_titanic_fixed'
                binding.append({'section':template,'entity':scalar(section,'entity'),'slot':name,'locator':scalar(slots[name],'locatorname')})
            else:
                kind,index=name.rsplit('_',1)
                countkey={'LARGE_UTILITY':'large_utility_slots','AUX_UTILITY':'aux_utility_slots'}[kind]
                assert 1<=int(index)<=int(scalar(section,countkey))
        assert len(slots)==len([e for e in children(block,'component') if scalar(e,'slot').startswith('TITANIC_GUN_')])
    assert len(binding)==16 and len({b['locator'] for b in binding})==16
    assert component_counts['AEMUSA_ENDGAME_T_BEAM']==16
    legacy={p:sections['AEMUSA_REALITY_FLAGSHIP_'+p] for p in ('BOW','MID','STERN')}
    assert [len(children(legacy[p],'component_slot')) for p in ('BOW','MID','STERN')]==[2,3,1]
    required=[e.value for e in design if e.key=='required_component']
    assert 'AEMUSA_ENDGAME_REACTOR' in required and len(required)==5
    for key in required:component_counts[key]=component_counts.get(key,0)+1
    # 解析当前实际配置的原生组件供能，包含盾、辅助与航行核心，不只算主炮。
    registry={**weapons,**powercores};variables={}
    for f in (GAME/'common/scripted_variables').glob('*.txt'):
        for m in re.finditer(r'(?m)^\s*(@[\w]+)\s*=\s*([-+]?\d+(?:\.\d+)?)',f.read_text(encoding='utf-8-sig')):variables[m.group(1)]=float(m.group(2))
    needed=set(component_counts)-set(registry)
    for f in (GAME/'common/component_templates').glob('*.txt'):
        text=f.read_text(encoding='utf-8-sig')
        if not any('"'+key+'"' in text for key in needed):continue
        data=parse(text)
        for e in data:
            if e.key.startswith('@') and isinstance(e.value,str):
                try:variables[e.key]=float(e.value)
                except ValueError:pass
            if e.key.endswith('component_template') and isinstance(e.value,list):
                key=scalar(e.value,'key')
                if key in needed:registry[key]=e.value
    assert set(component_counts)<=set(registry),set(component_counts)-set(registry)
    power=[]
    for key,count in component_counts.items():
        raw=scalar(registry[key],'power') or '0'
        value=variables[raw] if raw.startswith('@') else float(raw)
        power.append({'component':key,'count':count,'power_each':value,'power_total':value*count})
    total=sum(x['power_total'] for x in power);assert total>=0,total
    # 逐实体连接到真实已安装PDX，而不是只读构建脚本的预期列表。
    dest=ROOT/'mod/gfx/models/aemusa_endgame_v03'
    entities={scalar(b,'name'):b for b in blocks(dest/'_aef03_entities.asset','entity')}
    reader=load_reader(Path('C:/Users/Admin/AppData/Roaming/Blender Foundation/Blender/5.1/extensions/user_default/io_pdx_mesh'))
    parts={};total_tri=0
    for part in ('bow','mid','stern'):
        path=dest/('aef03_'+part+'.mesh');tree=reader(str(path))
        locs={n.tag:n.attrib for n in tree.findall('./locator/*')}
        mats=[];tris=0
        for node in tree.findall('./object/*/mesh'):
            positions=node.attrib.get('p',[]);indices=node.attrib.get('tri',[])
            assert len(indices)%3==0 and len(positions)%3==0
            assert all(math.isfinite(v) for v in positions)
            assert not indices or (min(indices)>=0 and max(indices)<len(positions)//3)
            assert 'u0' in node.attrib and len(node.attrib['u0'])==len(positions)//3*2
            assert all(math.isfinite(v) and -1e-5<=v<=1.00001 for v in node.attrib['u0'])
            assert 'n' in node.attrib and len(node.attrib['n'])==len(positions)
            assert all(math.isfinite(v) for v in node.attrib['n'])
            material=node.find('material')
            if material is not None:
                mats.append(material.attrib)
                for channel in ('diff','spec','n'):assert (dest/material.attrib[channel][0]).is_file()
            tris+=len(indices)//3
        assert scalar(entities['aef03_'+part+'_entity'],'pdxmesh')=='aef03_'+part+'_mesh'
        assert scalar(children(entities['aef03_'+part+'_entity'],'game_data')[0],'emissive_recolor_crunch')=='0'
        assert path.read_bytes()==(ROOT/'art/models/aemusa_endgame_runtime_v03/export'/path.name).read_bytes()
        parts[part]={'locators':locs,'triangles':tris,'material_count':len(mats)};total_tri+=tris
    for b in binding:
        part=b['entity'].removeprefix('aef03_').removesuffix('_entity')
        assert b['locator'] in parts[part]['locators'],b
    for p,section in legacy.items():
        part={'BOW':'bow','MID':'mid','STERN':'stern'}[p]
        for s in children(section,'component_slot'):assert scalar(s,'locatorname') in parts[part]['locators']
    assert len([n for p in parts.values() for n in p['locators'] if n.startswith('t_gun_')])==16
    textures=[]
    for f in dest.glob('*.dds'):
        data=f.read_bytes();assert data[:4]==b'DDS ' and data[84:88]==b'DXT5'
        height,width=struct.unpack_from('<II',data,12);mips=struct.unpack_from('<I',data,28)[0]
        assert mips==int(math.log2(max(width,height)))+1
        assert len(list((ROOT/'mod').rglob(f.name)))==1,f.name
        textures.append({'file':f.name,'dimensions':[width,height],'mips':mips})
    assert len(textures)==6
    for name in ('cc_surface_v05_diffuse.dds','cc_surface_v05_normal.dds','cc_surface_v05_properties.dds'):
        assert len(list((ROOT/'mod').rglob(name)))==1,name
    for f in [ROOT/'mod/common/component_templates/aemusa_endgame_flagship_components.txt',ROOT/'mod/common/component_sets/aemusa_endgame_flagship_sets.txt',ROOT/'mod/common/section_templates/aemusa_reality_flagship_sections.txt']:
        assert not f.read_bytes().startswith(b'\xef\xbb\xbf')
    result={'date':'2026-11-06','status':'pass','real_T_slots':len(binding),'binding':binding,
            'legacy_six_L_templates_retained':True,'legacy_locators_resolved':True,
            'power_breakdown':power,'power_surplus':total,'native_components_resolved':True,
            'pdx_parts':{k:{'triangles':v['triangles'],'material_count':v['material_count'],'locator_count':len(v['locators'])} for k,v in parts.items()},
            'total_triangles':total_tri,'uv_and_normals_present_and_finite':True,'textures':textures,'emission_recolor_disabled':True,
            'known_legacy_DDS_duplicates_resolved':True,'runtime_status':'not_started','game_operated':False}
    (ROOT/'reports/flagship_v03_preflight_2026-11-06.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ENDGAME_PREFLIGHT_PASS '+json.dumps({'T_slots':16,'power_surplus':total,'triangles':total_tri,'DDS':6,'legacy_compatibility':'static_pass'},ensure_ascii=False))


if __name__=='__main__':main()
