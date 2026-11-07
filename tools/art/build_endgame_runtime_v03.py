"""独立后台烘焙并导出终局旗舰三段生产候选；不启动游戏或改用户场景。"""

import argparse
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode=True
import bpy
from mathutils import Matrix

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art/models/aemusa_endgame_runtime_v03'
EXPORT=OUT/'export'
SOURCE=ROOT/'art/models/aemusa_endgame_refinement_v02/endgame_refinement_v02.blend'
PREPARED=ROOT/'runtime-backups/aef03_bake_ready.blend'
ADDON=Path('C:/Users/Admin/AppData/Roaming/Blender Foundation/Blender/5.1/extensions/user_default')
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_milestone4_surface as pipeline
import build_milestone4_graybox as geometry
import build_endgame_flagship_blockout as blockout


def bake():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene=bpy.data.scenes['终局旗舰_结构样稿'];bpy.context.window.scene=scene
    star=bpy.data.objects['星空缺口_空间带占位']
    for obj in scene.objects:obj.hide_render=obj!=star
    star.hide_set(False);star.hide_render=False
    bpy.ops.object.select_all(action='DESELECT');star.select_set(True);bpy.context.view_layer.objects.active=star
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.1519,island_margin=.035)
    bpy.ops.object.mode_set(mode='OBJECT')
    img=bpy.data.images.new('aef03_star_diffuse_bake',width=1024,height=1024,alpha=True)
    img.colorspace_settings.name='sRGB'
    mat=star.data.materials[0];node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img
    mat.node_tree.nodes.active=node
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1
    scene.render.bake.margin=12;scene.render.bake.use_clear=True
    bpy.ops.object.bake(type='EMIT')
    img.filepath_raw=str(EXPORT/'aef03_star_diffuse.png');img.file_format='PNG';img.save()
    for obj in scene.objects:obj.hide_render=False
    scene.render.engine='BLENDER_EEVEE'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(PREPARED))
    print('ENDGAME_STAR_BAKED '+str(img.filepath_raw),flush=True)


def runtime_material(prefix, texture_dir=None):
    """导出器沿节点连接读取三张DDS；解包预览与既有已验证流程一致。"""
    mat=bpy.data.materials.new(prefix+'_pdx');mat['shader']='PdxMeshShip';mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    diff,prop,normal=[nodes.new('ShaderNodeTexImage') for _ in range(3)]
    for n,suffix in ((diff,'diffuse'),(prop,'properties'),(normal,'normal')):
        n.image=bpy.data.images.load(str((texture_dir or EXPORT)/(prefix+'_'+suffix+'.dds')),check_existing=True)
        if suffix!='diffuse':n.image.colorspace_settings.name='Non-Color'
    links.new(diff.outputs['Color'],bsdf.inputs['Base Color'])
    split=nodes.new('ShaderNodeSeparateColor');links.new(prop.outputs['Color'],split.inputs[0])
    links.new(split.outputs['Blue'],bsdf.inputs['Metallic'])
    rough=nodes.new('ShaderNodeMath');rough.operation='SUBTRACT';rough.inputs[0].default_value=1
    links.new(prop.outputs['Alpha'],rough.inputs[1]);links.new(rough.outputs[0],bsdf.inputs['Roughness'])
    channels=nodes.new('ShaderNodeSeparateColor');links.new(normal.outputs['Color'],channels.inputs[0])
    combine=nodes.new('ShaderNodeCombineColor');combine.inputs['Blue'].default_value=1
    links.new(channels.outputs['Green'],combine.inputs['Red'])
    flip=nodes.new('ShaderNodeMath');flip.operation='SUBTRACT';flip.inputs[0].default_value=1
    links.new(normal.outputs['Alpha'],flip.inputs[1]);links.new(flip.outputs[0],combine.inputs['Green'])
    nm=nodes.new('ShaderNodeNormalMap');links.new(combine.outputs[0],nm.inputs['Color']);links.new(nm.outputs[0],bsdf.inputs['Normal'])
    links.new(diff.outputs['Color'],bsdf.inputs['Emission Color']);links.new(channels.outputs['Blue'],bsdf.inputs['Emission Strength'])
    return mat


def part_for(name):
    if name.startswith('星空') or name.startswith('主轴'):
        return 'mid'
    return 'stern' if '_后' in name or name.startswith('推进') else 'bow'


def style_for(name):
    if '指示' in name and name.startswith('推进'):return 'cyan'
    if name.startswith(('主轴','星空边界','内缘刻度')):return 'gold'
    if name.startswith('悬隔内衬'):return 'inner'
    if name.startswith('悬隔外壳'):return 'silver'
    return 'navy'


def export():
    bpy.ops.wm.open_mainfile(filepath=str(PREPARED))
    source_scene=bpy.data.scenes['终局旗舰_结构样稿'];bpy.context.window.scene=source_scene
    for c in source_scene.collection.children:c.hide_viewport=False;c.hide_render=False
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    scene=bpy.data.scenes.new('终局旗舰_运行材质预览')
    blockout.configure_scene(scene)
    groups={p:bpy.data.collections.new('aef03_'+p) for p in ('bow','mid','stern')}
    for c in groups.values():scene.collection.children.link(c)
    pipeline.ROOT=ROOT;pipeline.EXPORT=EXPORT
    pipeline.STYLES=('navy','navy_light','silver','silver_shadow','inner','gold','cyan','socket')
    atlas=runtime_material('aef03_hull');stars=runtime_material('aef03_star')
    state=json.loads((ROOT/'art/models/aemusa_endgame_refinement_v02/blockout_manifest.json').read_text(encoding='utf-8'))
    locators={r['id']:r for r in state['locators']}
    rotation=Matrix.Rotation(math.pi,4,'Z')
    # 灰模曾用小炮座和短亮条标出每个T位。成品只导出各站的发射定位器。
    mount_guides = {f'{prefix}_{key}' for key in locators for prefix in ('发射接口', '接口指示')}
    omitted_guides = []
    for c in ('实体舰体','中央星空_视觉占位'):
        for obj in list(bpy.data.collections[c].objects):
            if obj.type not in ('MESH','CURVE'):continue
            if obj.name in mount_guides:
                omitted_guides.append(obj.name)
                continue
            mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(deps));mesh.transform(obj.matrix_world)
            new=bpy.data.objects.new('prod_'+obj.name,mesh)
            part=part_for(obj.name);groups[part].objects.link(new)
            if obj.name=='星空缺口_空间带占位':
                assert mesh.uv_layers.active
                mesh.materials.clear();mesh.materials.append(stars)
                for face in mesh.polygons:face.material_index=0
            else:
                role=style_for(obj.name)
                pipeline.map_style(new,role,atlas)
                # 大转折面保留少量本色明暗，不烘焙固定场景灯光。
            mesh.transform(rotation);mesh.update()
    for key,row in locators.items():
        p=row['position'];part='bow' if p[1]>0 else 'stern'
        geometry.locator(groups[part],key,(-p[0],-p[1],p[2]),(0,0,0))
    # 保留旧6L设计的挂点别名，旧模板留在源码中，不强行改写存档实例。
    aliases={'bow':['t_gun_01','t_gun_05'],'mid':['t_gun_03','t_gun_07','t_gun_11'],'stern':['t_gun_04']}
    for part,keys in aliases.items():
        for i,key in enumerate(keys,1):
            x,y,z=locators[key]['position'];geometry.locator(groups[part],f'large_gun_{i:02d}',(-x,-y,z))
    for i,x in enumerate((-2.0,2.0),1):geometry.locator(groups['stern'],f'engine_large_{i:02d}',(-x,45.3,0),(0,0,math.pi))
    bpy.context.window.scene=scene
    for old in list(bpy.data.scenes):
        if old!=scene:bpy.data.scenes.remove(old)
    if hasattr(bpy.data,'orphans_purge'):bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
    sys.path.insert(0,str(ADDON))
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    native=json.loads((ROOT/'reports/central_court_engine_space_2026-11-01.json').read_text(encoding='utf-8'))
    byfile={Path(r['file']).name:r for r in native}
    nativegun=byfile['mammalian_01_battleship_bow_XL1.mesh']['locators']['xl_gun_01']['q']
    nativeengine=byfile['mammalian_01_battleship_stern_L1.mesh']['locators']['engine_medium_01']['q']
    records=[];settings=[]
    for part,group in groups.items():
        record=pipeline.export_group(group,export_meshfile,read_meshfile)
        tree=read_meshfile(str(ROOT/record['mesh']))
        sub=[]
        for shape in tree.findall('./object/*'):
            for index,mesh in enumerate(shape.findall('mesh')):
                material=mesh.find('material')
                if material is not None:sub.append({'shape':shape.tag,'index':index,'material':material.attrib})
        for locator in tree.findall('./locator/*'):
            if 'gun_' in locator.tag:
                assert abs(sum(a*b for a,b in zip(locator.attrib['q'],nativegun)))>.9999
            if locator.tag.startswith('engine_'):
                assert abs(sum(a*b for a,b in zip(locator.attrib['q'],nativeengine)))>.9999
            if locator.tag in locators:
                x,y,z=locators[locator.tag]['position']
                assert all(abs(a-b)<1e-4 for a,b in zip(locator.attrib['p'],[-x,z,-y])),locator.tag
        record['submeshes']=sub;record['native_orientation_verified']=True;records.append(record)
    gfx=['# 原创终局旗舰v03运行候选，所有贴图使用独立名称。','objectTypes = {']
    for record in records:
        gfx += ['    pdxmesh = {',f'        name = "{record["part"]}_mesh"',f'        file = "gfx/models/aemusa_endgame_v03/{record["part"]}.mesh"','        scale = 1.0']
        for sub in record['submeshes']:
            mat=sub['material']
            gfx += ['        meshsettings = {',f'            name = "{sub["shape"]}"',f'            index = {sub["index"]}',
                    f'            texture_diffuse = "{mat["diff"][0]}"',f'            texture_normal = "{mat["n"][0]}"',
                    f'            texture_specular = "{mat["spec"][0]}"','            shader = "PdxMeshShip"','        }']
        gfx += ['    }']
    gfx+=['}'];(EXPORT/'_aef03_meshes.gfx').write_text('\n'.join(gfx)+'\n',encoding='utf-8')
    lines=['# 终局旗舰显示实体；先做静态显示候选，游戏观察尚未执行。','entity = {','    name = "aef03_root_entity"','    scale = 1.0']
    for i in range(1,4):lines += [f'    locator = {{ name = "part{i}" position = {{ 0 0 0 }} }}']
    for i,z in enumerate((-36,-10,12,35),1):lines += [f'    locator = {{ name = "target_locator_{i}" position = {{ 0 0 {z} }} }}']
    lines += ['    default_state = "idle"','    state = { name = "idle" state_time = 5 }','    state = { name = "moving" state_time = 5 }',
              '    state = { name = "death" state_time = 5 looping = no','        event = { time = 0 node = "part2" particle = "large_player_ship_explosion_particle" trigger_once = yes }','    }',
              '    game_data = { size = 25 emissive_recolor_crunch = 0 }','}']
    for part in groups:
        lines += ['entity = {',f'    name = "aef03_{part}_entity"',f'    pdxmesh = "aef03_{part}_mesh"','    default_state = "idle"']
        for state,particle in [('idle','generic_big_2_5_exhaust_circle_idle'),('moving','generic_big_3_exhaust_circle_moving')]:
            lines += [f'    state = {{ name = "{state}" state_time = 5']
            if part=='stern':
                for i in (1,2):lines += [f'        event = {{ time = 0 node = "engine_large_{i:02d}" particle = "{particle}" trigger_once = yes keep_particle = yes }}']
            lines += ['    }']
        lines += ['    state = { name = "death" state_time = 5 looping = no }','    game_data = { emissive_recolor_crunch = 0 }','}']
    lines += ['entity = {','    name = "aef03_preview_entity"','    clone = "aef03_root_entity"']
    for i,part in enumerate(groups,1):lines += [f'    attach = {{ part{i} = "aef03_{part}_entity" }}']
    lines += ['}'];(EXPORT/'_aef03_entities.asset').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # 导出完转回作者方向保存；PDX文件保持已核验的原生朝向。
    for group in groups.values():
        for obj in group.objects:
            if obj.type=='MESH':obj.data.transform(rotation);obj.data.update()
            elif obj.type=='EMPTY':obj.location.x*=-1;obj.location.y*=-1
    blockout.area(scene,'运行材质主光',(-35,30,65),28000,55)
    blockout.area(scene,'运行材质轮廓光',(35,-40,25),18000,45)
    cam=blockout.camera(scene,'运行材质斜视',(-95,108,68),(0,0,0),112,78,(1400,980))
    detail=blockout.camera(scene,'运行材质星空近景',(-28,14,27),(0,-5.4,0),29,22,(1400,1060))
    scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=1400,980
    bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
    blend=OUT/'endgame_runtime_v03.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.wm.open_mainfile(filepath=str(blend));scene=bpy.context.scene
    (OUT/'previews').mkdir(exist_ok=True)
    for name,camname in [('runtime_material_oblique','运行材质斜视'),('runtime_star_detail','运行材质星空近景')]:
        scene.camera=bpy.data.objects[camname];scene.render.filepath=str(OUT/'previews'/(name+'.png'))
        bpy.ops.render.render(write_still=True)
    result={'status':'exported_readback_pass_runtime_not_started','source':blend.relative_to(ROOT).as_posix(),
            'parts':records,'textures_manifest':(OUT/'textures_manifest.json').relative_to(ROOT).as_posix(),
            'source_reopened':True,'T_locator_count':sum(len([n for n in r['locators'] if n.startswith('t_gun_')]) for r in records),
            'omitted_authoring_mount_guides':sorted(omitted_guides),
            'native_materials_baked':True,'emission_recolor_crunch':0,'automatic_lod':False,'runtime_status':'not_started','game_operated':False}
    assert result['T_locator_count']==16
    (OUT/'production_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ENDGAME_EXPORT_READY '+json.dumps({'parts':[(r['part'],r['triangles']) for r in records],'T_locators':16},ensure_ascii=False),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=['bake','export'],required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not bpy.app.background or bpy.data.filepath:raise RuntimeError('必须独立后台factory-startup运行。')
    EXPORT.mkdir(parents=True,exist_ok=True);PREPARED.parent.mkdir(exist_ok=True)
    bake() if args.mode=='bake' else export()


if __name__=='__main__':main()
