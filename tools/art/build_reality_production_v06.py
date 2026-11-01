"""后台整理私人旗舰/基线枢纽的五部件生产候选，不安装或改变运行玩法。"""

import argparse
import json
import math
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_central_court_surface_v02 as common
import build_central_court_surface_v03 as refinement
import build_milestone4_surface as pipeline

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'art/models/milestone4_surface_v02'
MATERIAL = ROOT / 'art/models/central_court_readability_v05'
OUT = ROOT / 'art/models/aemusa_reality_production_v06'
EXPORT = OUT / 'export'
PARTS = ('flagship_bow', 'flagship_mid', 'flagship_stern', 'baseline_base', 'baseline_active')


def mesh_data_checks(new, old, ship):
    """只做既定坐标转换；逐三角形证明没有重塑现有造型或改动UV。"""
    new_meshes, old_meshes = new.findall('./object/*/mesh'), old.findall('./object/*/mesh')
    assert len(new_meshes) == len(old_meshes) == 1
    a, b = new_meshes[0].attrib, old_meshes[0].attrib
    assert len(a['tri']) == len(b['tri'])
    sign = (-1, 1, -1) if ship else (1, 1, 1)
    maximum = {'position':0.0, 'normal':0.0, 'uv':0.0}
    for ia, ib in zip(a['tri'], b['tri']):
        for channel in ('p', 'n'):
            error=max(abs(a[channel][ia*3+k] - b[channel][ib*3+k]*sign[k]) for k in range(3))
            maximum['position' if channel=='p' else 'normal']=max(maximum['position' if channel=='p' else 'normal'],error)
            # 转180度后Blender重算法线，圆角处分量约有1.5e-5的浮点差异。
            assert error < (1e-5 if channel=='p' else 5e-5), (channel,error)
        error=max(abs(a['u0'][ia*2+k] - b['u0'][ib*2+k]) for k in range(2))
        maximum['uv']=max(maximum['uv'],error)
        assert error < 1e-5
    old_locs = {n.tag:n.attrib for n in old.findall('./locator/*')}
    new_locs = {n.tag:n.attrib for n in new.findall('./locator/*')}
    assert old_locs.keys() == new_locs.keys()
    for name, data in old_locs.items():
        assert all(abs(new_locs[name]['p'][k] - data['p'][k]*sign[k]) < 1e-5 for k in range(3))
    return maximum


def definitions(records):
    gfx = ['# v06私人旗舰/基线枢纽离线候选；原生方向，未安装。', 'objectTypes = {']
    for record in records:
        name = record['part']
        gfx += ['    pdxmesh = {', f'        name = "{name}_mesh"',
                f'        file = "gfx/models/aemusa_reality_production_v06/{name}.mesh"', '        scale = 1.0']
        for index, shape in enumerate(record['shape_names']):
            gfx += ['        meshsettings = {', f'            name = "{shape}"', f'            index = {index}',
                    '            texture_diffuse = "cc_surface_v05_diffuse.dds"',
                    '            texture_normal = "cc_surface_v05_normal.dds"',
                    '            texture_specular = "cc_surface_v05_properties.dds"',
                    '            shader = "PdxMeshShip"', '        }']
        gfx += ['    }']
    gfx += ['}']
    (EXPORT / '_reality_production_v06_meshes.gfx').write_text('\n'.join(gfx)+'\n', encoding='utf-8')
    entities = ['# 私人旗舰/基线枢纽独立样品，未注册到当前舰种或巨构。',
                'entity = {', '    name = "arfv06_flagship_root_entity"', '    scale = 1.0']
    for part in ('part1','part2','part3'):
        entities += [f'    locator = {{ name = "{part}" position = {{ 0 0 0 }} }}']
    for i,z in enumerate((-16,-5,6,16),1):
        entities += [f'    locator = {{ name = "target_locator_{i}" position = {{ 0 0 {z} }} }}']
    entities += ['    default_state = "idle"', '    state = { name = "idle" state_time = 5 }',
                 '    state = { name = "moving" state_time = 5 }',
                 '    state = { name = "death" state_time = 5 looping = no',
                 '        event = { time = 0 node = "part2" particle = "large_player_ship_explosion_particle" trigger_once = yes }',
                 '    }', '    game_data = { size = 10 emissive_recolor_crunch = 5.0 }', '}']
    for part in PARTS:
        name = 'arfv06_' + part
        entities += ['entity = {', f'    name = "{name}_entity"', f'    pdxmesh = "{name}_mesh"', '    default_state = "idle"']
        for state, particle in (('idle','generic_big_2_5_exhaust_circle_idle'),('moving','generic_big_3_exhaust_circle_moving')):
            entities += [f'    state = {{ name = "{state}" state_time = 5']
            if part == 'flagship_stern':
                for index in (1,2):
                    entities += [f'        event = {{ time = 0 node = "engine_large_0{index}" particle = "{particle}" keep_particle = yes trigger_once = yes }}']
            entities += ['    }']
        entities += ['    state = { name = "death" state_time = 5 looping = no }','}']
    entities += ['entity = {', '    name = "arfv06_preview_flagship_entity"',
                 '    clone = "arfv06_flagship_root_entity"',
                 '    attach = { part1 = "arfv06_flagship_bow_entity" }',
                 '    attach = { part2 = "arfv06_flagship_mid_entity" }',
                 '    attach = { part3 = "arfv06_flagship_stern_entity" }', '}']
    (EXPORT / '_reality_production_v06_entities.asset').write_text('\n'.join(entities)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdx-addon-root', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('只允许独立后台factory-startup，禁止用户交互场景。')
    sys.path.insert(0,args.pdx_addon_root)
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    EXPORT.mkdir(parents=True,exist_ok=True)
    for suffix in ('diffuse','normal','properties'):
        filename = f'cc_surface_v05_{suffix}.dds'
        shutil.copy2(MATERIAL/'export'/filename,EXPORT/filename)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'reality_assets_surface_v02.blend'))
    bpy.context.preferences.filepaths.save_version=0
    collections={part:bpy.data.collections['reality_'+part] for part in PARTS}
    for obj in list(bpy.data.objects):
        if obj.type in ('CAMERA','LIGHT'):
            bpy.data.objects.remove(obj,do_unlink=True)
    common.EXP=EXPORT
    material=common.texture_material('cc_surface_v05')
    material.name='现实恒定舰与基线枢纽_共享工程材质v06'
    refinement.shared_specular_proxy(material)
    for part,c in collections.items():
        c.name='arfv06_'+part
        c.hide_viewport=c.hide_render=False
        for obj in c.objects:
            if obj.type=='MESH':
                obj.data.materials.clear(); obj.data.materials.append(material)
                assert all(0<=v<=1 for loop in obj.data.uv_layers.active.data for v in loop.uv)
    scene,camera=common.render_setup()
    # 原文件活动集合可能是舰段；预览灯光/相机必须置于场景根，避免随部件隐藏或被LOD复制。
    for obj in list(scene.objects):
        if obj.type in ('CAMERA','LIGHT'):
            if obj.name not in scene.collection.objects:
                scene.collection.objects.link(obj)
            for c in list(obj.users_collection):
                if c != scene.collection:
                    c.objects.unlink(obj)
    scene.name='现实恒定旗舰与基线枢纽生产候选v06'
    previews=OUT/'previews'; previews.mkdir(parents=True,exist_ok=True)
    images=[]
    for stem,parts,target,offset,scale in (
        ('flagship_oblique',('flagship_bow','flagship_mid','flagship_stern'),(0,-.5,0),(34,43,36),53),
        ('flagship_side',('flagship_bow','flagship_mid','flagship_stern'),(0,-.5,0),(48,9,12),49),
        ('baseline_base',('baseline_base',),(0,0,.5),(30,35,30),34),
        ('baseline_active',('baseline_active',),(0,0,.5),(30,35,30),34)):
        show={collections[p].name for p in parts}
        for c in bpy.data.collections:
            c.hide_render=c.name not in show
        refinement.camera_view(scene,camera,target,offset,scale)
        scene.render.filepath=str(previews/(stem+'.png'))
        bpy.ops.render.render(write_still=True)
        images.append((previews/(stem+'.png')).relative_to(ROOT).as_posix())
    for c in bpy.data.collections:
        c.hide_render=c.hide_viewport=c.name not in {collections[p].name for p in ('flagship_bow','flagship_mid','flagship_stern')}
    refinement.camera_view(scene,camera,(0,-.5,0),(34,43,36),53)
    bpy.data.orphans_purge(do_recursive=True)
    assert len(bpy.data.libraries)==0
    for image in bpy.data.images:
        if image.filepath.lower().endswith('.dds'):image.pack()
    blend=OUT/'reality_production_v06.blend'
    names={p:c.name for p,c in collections.items()}
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    assert len(bpy.data.libraries)==0
    assert len([i for i in bpy.data.images if i.filepath.lower().endswith('.dds') and i.packed_file])==3
    collections={p:bpy.data.collections[n] for p,n in names.items()}
    native=json.loads((ROOT/'reports/central_court_engine_space_2026-11-01.json').read_text(encoding='utf-8'))
    native={Path(row['file']).name:row for row in native}
    gun_q=native['mammalian_01_battleship_bow_XL1.mesh']['locators']['xl_gun_01']['q']
    engine_q=native['mammalian_01_battleship_stern_L1.mesh']['locators']['engine_medium_01']['q']
    pipeline.EXPORT,pipeline.ROOT=EXPORT,ROOT
    records=[]
    for part in PARTS:
        c=collections[part]; c.hide_viewport=c.hide_render=False
        ship=part.startswith('flagship')
        if ship:
            for obj in c.objects:
                if obj.type=='MESH':
                    obj.data.transform(Matrix.Rotation(math.pi,4,'Z'));obj.data.update()
                elif obj.type=='EMPTY':
                    obj.location.x*=-1;obj.location.y*=-1
                    obj.rotation_euler=(0,0,math.pi) if obj['pdx_locator_name'].startswith('engine_') else (0,0,0)
        row=pipeline.export_group(c,export_meshfile,read_meshfile)
        pdx=read_meshfile(str(ROOT/row['mesh']))
        old=read_meshfile(str(SOURCE/'export'/('reality_'+part+'.mesh')))
        comparison=mesh_data_checks(pdx,old,ship)
        for loc in pdx.findall('./locator/*'):
            if 'gun_' in loc.tag:
                assert abs(sum(a*b for a,b in zip(loc.attrib['q'],gun_q)))>.9999
            if loc.tag.startswith('engine_'):
                assert abs(sum(a*b for a,b in zip(loc.attrib['q'],engine_q)))>.9999
        z=[x for m in pdx.findall('./object/*/mesh') for x in m.attrib['p'][2::3]]
        if part=='flagship_bow':assert max(z)<0
        if part=='flagship_stern':assert min(z)>0
        row.update(lod=0,source_geometry_and_uv_preserved=True,native_orientation_checked=ship,
                   comparison_max_error=comparison,normal_tolerance=5e-5,position_uv_tolerance=1e-5)
        records.append(row)
        for level,ratio in ((1,.5),(2,.23)):
            lod=common.simplified(c,level,ratio)
            child=pipeline.export_group(lod,export_meshfile,read_meshfile)
            assert child['triangles']<row['triangles'] and child['locators']==row['locators']
            child.update(lod=level,automatic_lod_switching=False,source_part=row['part'])
            records.append(child)
    hub=[]
    for part in ('baseline_base','baseline_active'):
        data=read_meshfile(str(EXPORT/f'arfv06_{part}.mesh'))
        hub.append({n.tag:n.attrib for n in data.findall('./locator/*')})
    assert hub[0]==hub[1]
    definitions(records)
    result={'date':'2026-11-01','source_base':'88071a1','status':'draft_pending_human_review',
       'runtime_installed':False,'formal_appearance_approved':False,'game_operated':False,
       'source':'art/models/milestone4_surface_v02/reality_assets_surface_v02.blend',
       'source_blend':blend.relative_to(ROOT).as_posix(),'source_reopened':True,'packed_dds':3,
       'source_geometry_and_uv_preserved':True,'authoring_axes':'+Y forward, +Z up',
       'export_axes':'native PDX -Z forward; ship geometry/positions turned, guns and engines match native',
       'meshes':records,'previews':images,'hub_stage_locator_transforms_identical':True,
       'material_source':'art/models/central_court_readability_v05/export; 3 shared 2048x1024 BC3 files, 12 mips',
       'root_assembly':'zero part1/2/3, four native-name targets, six original L weapon locators',
       'particles':'native names referenced only; engine/death appearance not runtime verified',
       'automatic_lod_switching':False,'old_stage9_or_tower_assets_used':False,
       'personal_identity':'one private reality flagship and two-stage crisis baseline hub; separate from public cruiser/worldformer',
       'user_live_blender_scene_modified':False,'gameplay_changed':False}
    (OUT/'production_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('REALITY_V06_OK five native meshes + ten independent LOD alternatives, source reopened, six original L guns retained',flush=True)


if __name__=='__main__':main()
