"""读取已保存v07，补齐有来源约束的个人接口与公共观测功能；独立后台制作。"""

import argparse
import json
import math
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode=True
import bpy
from mathutils import Matrix,Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_reality_refinement_v07 as shape
import build_central_court_surface_v02 as common
import build_central_court_surface_v03 as surface
import build_milestone4_surface as pipeline

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'art/models/aemusa_reality_refinement_v07'
OUT=ROOT/'art/models/aemusa_reality_identity_v08'
EXPORT=OUT/'export'
PRIVATE_ROLES=('personal_dark','personal_wine','personal_gold','personal_signal')
RETIRED_LABELS=('受控恒定模块','仪器标定面','局部状态读数','分歧仪轨','汇合仪轨','路径读数')
CURRENT_MATERIAL=None
PRIVATE_MATERIAL=None


def style(obj,role):
    # 公共UV继续使用原8格；私人中段才改为4x4图集，私人格不进入枢纽。
    source_role=role if role not in PRIVATE_ROLES else 'armor'
    surface.metric_uv(obj,source_role,CURRENT_MATERIAL)
    uv=obj.data.uv_layers.active
    if CURRENT_MATERIAL==PRIVATE_MATERIAL:
        for loop in uv.data:
            u,v=loop.uv
            if role in PRIVATE_ROLES:
                index=8+PRIVATE_ROLES.index(role)
                loop.uv=((index%4+u*4)/4,(3-index//4+v*2-1)/4)
            else:
                loop.uv=(u,.5+.5*v)
    obj['surface_role']=role
    if role in PRIVATE_ROLES:obj['personal_layer']='aemusa_local_interface_only'
    return obj


def use_material(material):
    global CURRENT_MATERIAL
    CURRENT_MATERIAL=material
    shape.MAT=common.MAT=material
    common.style=style


def path_beams(c,label,points,width,role):
    return [shape.beam(c,label,a,b,width,role) for a,b in zip(points,points[1:])]


def personal_interface(c):
    removed=[]
    for obj in list(c.objects):
        if obj.type=='MESH' and any(x in obj.name for x in RETIRED_LABELS):
            removed.append(obj.name)
            bpy.data.objects.remove(obj,do_unlink=True)
    assert len(removed)==9,removed
    # 两条错层仪轨由两端控制座约束；不闭合为法阵，也不增加主炮或神器本体。
    branches=(
        [(0,-2.45,.65),(-.85,-1.85,.95),(-1.24,-.8,1.45),(-1.18,.15,2.02),(-.55,.85,2.18),(0,1.12,1.95)],
        [(0,-2.45,.65),(.88,-1.75,.84),(1.23,-.65,1.08),(.95,.28,1.47),(.4,.88,1.78),(0,1.12,1.95)])
    for index,points in enumerate(branches):
        path_beams(c,'错层分支承轨',points,.17,'plate')
        # 几段刻度说明局部观察方向；不把整条轨道描成霓虹。
        for a,b in zip(points[1:3],points[2:4]):
            a=Vector(a)+Vector((0,0,.1))
            b=Vector(b)+Vector((0,0,.1))
            path_beams(c,'分支局部刻度',[a,b],.045,'personal_gold')
        for p in (points[1],points[-2]):
            shape.plate(c,'仪轨标定锁座',p,(.35,.45,.17),'personal_dark')
    for y,z in ((-2.45,.64),(1.12,1.95)):
        shape.plate(c,'共同汇接控制座',(0,y,z),(.8,.58,.22),'plate')
        shape.plate(c,'选择读数窗口',(0,y,z+.14),(.4,.28,.055),'personal_wine')
    # 三枚静态观测界面可以逐个辨认；编号只是模型组织，不是新增原作牌面。
    for index,(position,tilt,yaw) in enumerate((
            ((-.62,-1.25,1.4),-.24,-.17),((0,-.25,1.82),-.08,.12),((.57,.62,2.2),.18,.25)),1):
        before=set(c.objects)
        shape.plate(c,'观测界面外壳_'+str(index),(0,0,0),(.58,.93,.07),'personal_wine')
        shape.plate(c,'观测界面深色面_'+str(index),(0,0,.047),(.49,.82,.035),'personal_dark')
        shape.box(c,'局部细金索引',(0,.05,.069),(.035,.37,.016),'personal_gold')
        shape.box(c,'局部读数短线',(.14,-.24,.071),(.13,.035,.018),
                  'personal_signal' if index==2 else 'personal_gold')
        # 自行建模的有限弧形读数，不复制原作图标或标准塔罗图案。
        curve=[(.11*math.cos(a),-.04+.11*math.sin(a),.075) for a in (.3,.85,1.4,1.95,2.5,3.05,3.6)]
        path_beams(c,'局部弧形读数',curve,.018,'personal_gold')
        bpy.context.view_layer.update()
        transform=Matrix.Translation(Vector(position)) @ Matrix.Rotation(yaw,4,'Z') @ Matrix.Rotation(tilt,4,'X')
        for obj in set(c.objects)-before:
            obj.matrix_world=transform @ obj.matrix_world
            obj['interface_plate_index']=index
    # 有人维护的工程入口，位于公共船壳外侧，不改变角色身份或剧情。
    for side in (-1,1):
        shape.plate(c,'中段维护舱口',(side*4.43,-3.6,.2),(.06,.7,.85),'plate')
        shape.box(c,'维护入口读数',(side*4.48,-3.85,.25),(.025,.09,.12),'amber')
    return removed


def common_hub_interfaces(base,active):
    original=set(base.objects)
    for arm in range(4):
        before=set(base.objects)
        for side in (-1,1):
            shape.beam(base,'可检修资料通路',(side*.58,3.6,.25),(side*.58,8.35,.25),.09,'plate')
            shape.box(base,'通路绝缘联接',(side*.58,6.45,.25),(.21,.32,.2),'silver')
            shape.plate(base,'中央设备检修面',(side*1.35,2.44,.5),(.66,.43,.08),'warm')
        shape.plate(base,'观测头安装接口',(0,11.2,2.52),(1.8,.8,.15),'plate')
        shape.turn_objects(base,before,arm*math.pi/2)
    for obj in set(base.objects)-original:
        obj['shared_base_key']='v08_'+obj.name
        duplicate=obj.copy()
        duplicate.data=obj.data.copy()
        active.objects.link(duplicate)


def hub_observation(c):
    for arm in range(4):
        before=set(c.objects)
        for side in (-1,1):
            shape.beam(c,'短观测支撑',(side*.62,11.2,2.54),(side*.62,11.2,3.28),.14,'plate')
            shape.plate(c,'观测头屏蔽壳',(side*.42,11.31,3.11),(.68,.45,.7),'armor')
            shape.plate(c,'双端标定孔口',(side*.42,11.56,3.12),(.46,.05,.4),'glass')
            shape.box(c,'孔口短护唇',(side*.42,11.58,3.37),(.62,.16,.08),'silver')
            shape.plate(c,'中枢分区资料抽屉',(side*.83,2.48,1.07),(.63,.18,.68),'armor')
            shape.box(c,'资料检修锁',(side*.83,2.59,1.23),(.23,.04,.07),'silver')
        shape.beam(c,'观测头共同承梁',(-.72,11.2,3.46),(.72,11.2,3.46),.14,'plate')
        shape.box(c,'观测状态读数',(0,11.51,2.79),(.18,.045,.07),'cyan')
        shape.turn_objects(c,before,arm*math.pi/2)


def support_observation_mounts(base,active):
    """安装板必须连接两侧承架；两阶段共享横梁，不能无约束悬空。"""
    # 断点载入时枢纽集合可能被隐藏；先启用依赖图，避免读取到未更新的旋转矩阵。
    base.hide_viewport=active.hide_viewport=False
    bpy.context.view_layer.update()
    for arm in range(4):
        key='v08_observation_mount_support_'+str(arm)
        expected=Matrix.Rotation(arm*math.pi/2,3,'Z') @ Vector((1,0,0))
        matches=[[o for o in c.objects if o.get('shared_base_key')==key] for c in (base,active)]
        if all(len(items)==1 for items in matches):
            if all(abs((items[0].matrix_world.to_3x3() @ Vector((0,0,1))).normalized().dot(expected))>.9999 for items in matches):
                continue
            for items in matches:bpy.data.objects.remove(items[0],do_unlink=True)
            matches=[[],[]]
        assert all(not items for items in matches),'两阶段安装梁不一致，不能重复添加。'
        before=set(base.objects)
        obj=shape.beam(base,'观测安装板承梁',(-1.48,11.2,2.43),(1.48,11.2,2.43),.15,'plate')
        shape.turn_objects(base,before,arm*math.pi/2)
        assert abs((obj.matrix_world.to_3x3() @ Vector((0,0,1))).normalized().dot(expected))>.9999
        obj['shared_base_key']=key
        clone=obj.copy()
        clone.data=obj.data.copy()
        active.objects.link(clone)


def definitions(records):
    # 根实体/已有动画引用沿v06；实际材质与子网格名读取新导出，不猜测。
    import build_reality_production_v06 as old
    old.EXPORT=EXPORT
    old.definitions(records)
    old_entity=EXPORT/'_reality_production_v06_entities.asset'
    (EXPORT/'_reality_identity_v08_entities.asset').write_text(
        old_entity.read_text(encoding='utf-8').replace('v06','v08'),encoding='utf-8')
    old_entity.unlink()
    (EXPORT/'_reality_production_v06_meshes.gfx').unlink()
    gfx=['# v08静态候选，公共层与个人接口分开使用贴图；未安装。','objectTypes = {']
    for row in records:
        name=row['part']
        gfx+=['    pdxmesh = {',f'        name = "{name}_mesh"',
              f'        file = "gfx/models/aemusa_reality_identity_v08/{name}.mesh"','        scale = 1.0']
        for index,shape_name in enumerate(row['shape_names']):
            gfx+=['        meshsettings = {',f'            name = "{shape_name}"',f'            index = {index}']
            for label,field in (('diffuse','diff'),('normal','n'),('specular','spec')):
                gfx+=[f'            texture_{label} = "{row["textures"][field][0]}"']
            gfx+=['            shader = "PdxMeshShip"','        }']
        gfx+=['    }']
    gfx+=['}']
    (EXPORT/'_reality_identity_v08_meshes.gfx').write_text('\n'.join(gfx)+'\n',encoding='utf-8')


def export_saved_source(blend,removed,images,resumed=False):
    """可从已经保存的作者源继续导出，不重做几何或渲染。"""
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    assert not bpy.data.libraries
    assert len([i for i in bpy.data.images if i.filepath.endswith('.dds') and i.packed_file])==6
    collections={p:bpy.data.collections['arfv08_'+p] for p in shape.PARTS}
    bpy.context.view_layer.update()
    assert shape.shared_signature(collections['baseline_base'])==shape.shared_signature(collections['baseline_active'])
    shared_count=len(shape.shared_signature(collections['baseline_base']))
    mid=collections['flagship_mid']
    assert {o.get('interface_plate_index') for o in mid.objects if 'interface_plate_index' in o}=={1,2,3}
    assert not any(any(label in o.name for label in RETIRED_LABELS) for o in mid.objects)
    collars=sum('炮位锁紧边' in o.name and o.get('surface_role')=='plate' for c in collections.values() for o in c.objects)
    assert collars==6 and len(removed)==9
    pipeline.EXPORT,pipeline.ROOT=EXPORT,ROOT
    records=[]
    for part,c in collections.items():
        c.hide_viewport=c.hide_render=False
        old=read_meshfile(str(BASE/'export'/('arfv07_'+part+'.mesh')))
        old_locs={n.tag:n.attrib for n in old.findall('./locator/*')}
        for obj in c.objects:
            if obj.type=='MESH':
                assert all(0<=v<=1 for l in obj.data.uv_layers.active.data for v in l.uv)
                obj.data.transform(obj.matrix_world)
                obj.matrix_world=Matrix.Identity(4)
                if part.startswith('flagship'):obj.data.transform(Matrix.Rotation(math.pi,4,'Z'))
                obj.data.update()
            elif obj.type=='EMPTY' and part.startswith('flagship'):
                obj.location.x*=-1;obj.location.y*=-1
                obj.rotation_euler=(0,0,math.pi) if obj['pdx_locator_name'].startswith('engine_') else (0,0,0)
        row=pipeline.export_group(c,export_meshfile,read_meshfile)
        pdx=read_meshfile(str(ROOT/row['mesh']))
        locs={n.tag:n.attrib for n in pdx.findall('./locator/*')}
        assert locs.keys()==old_locs.keys()
        for name,data in locs.items():
            assert max(abs(a-b) for a,b in zip(data['p'],old_locs[name]['p']))<1e-5
            assert abs(sum(a*b for a,b in zip(data['q'],old_locs[name]['q'])))>.99999
        materials=pdx.findall('./object/*/mesh/material')
        assert len(materials)==1
        row.update(lod=0,textures=materials[0].attrib,original_locators_preserved=True)
        records.append(row)
        for level,ratio in ((1,.5),(2,.23)):
            lod=common.simplified(c,level,ratio)
            child=pipeline.export_group(lod,export_meshfile,read_meshfile)
            assert child['triangles']<row['triangles'] and child['locators']==row['locators']
            child.update(lod=level,textures=row['textures'],automatic_lod_switching=False)
            records.append(child)
    definitions(records)
    result={'date':'2026-11-03','base_commit':'bc8274a','status':'offline_identity_checks_passed',
        'formal_appearance':'draft_pending_human_review','runtime_installed':False,
        'source_binding':'docs/art/REALITY_ASSET_LORE_STYLE_BINDING.md',
        'source_blend':blend.relative_to(ROOT).as_posix(),'source_reopened':True,'packed_dds':6,
        'private_interface_plates':3,'private_palette_scope':'flagship_mid only',
        'old_central_objects_replaced':removed,'original_locator_transforms_preserved':True,
        'six_weapon_collars_coated_not_removed':collars,'shared_hub_objects_identical':shared_count,
        'material_count_per_mesh':1,'meshes':records,'previews':images,
        'resumed_export_without_rebuilding_or_rendering':resumed,
        'animation':'static resting pose only; no card flipping or moving tracks implemented',
        'automatic_lod_switching':False,'gameplay_changed':False,'game_operated':False,
        'user_live_blender_scene_modified':False,'original_game_reference_images_copied':False}
    (OUT/'identity_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('REALITY_V08_OK local personal interface, public observation hub, six original L slots',flush=True)


def main():
    global PRIVATE_MATERIAL
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdx-addon-root',required=True)
    parser.add_argument('--resume-export',action='store_true',help='修正已保存源的贴图路径并继续导出，跳过建模和渲染')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('只允许独立后台factory-startup，不操作用户场景。')
    sys.path.insert(0,args.pdx_addon_root)
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    if args.resume_export:
        # 仅读取v07对象名确认来源，不运行旧构建。所有保存只针对本轮v08。
        bpy.ops.wm.open_mainfile(filepath=str(BASE/'reality_refinement_v07.blend'))
        removed=[o.name for o in bpy.data.collections['arfv07_flagship_mid'].objects
                 if o.type=='MESH' and any(x in o.name for x in RETIRED_LABELS)]
        assert len(removed)==9
        blend=OUT/'reality_identity_v08.blend'
        bpy.ops.wm.open_mainfile(filepath=str(blend))
        bpy.context.preferences.filepaths.save_version=0
        expected={prefix+'_'+suffix+'.dds' for prefix in ('cc_surface_v05','reality_identity_v08')
                  for suffix in ('diffuse','normal','properties')}
        repaired=[]
        for img in bpy.data.images:
            if img.name in expected:
                assert img.packed_file and (EXPORT/img.name).is_file()
                # 本次受影响的三张图已由只读检查确认，名称仍保存完整文件名。
                img.filepath=str(EXPORT/img.name)
                repaired.append(img.name)
        assert set(repaired)==expected
        images=[(OUT/'previews'/(n+'.png')).relative_to(ROOT).as_posix() for n in
                ('flagship_oblique','flagship_side','baseline_base','baseline_active','flagship_interface','flagship_geometry')]
        assert all((ROOT/p).is_file() for p in images)
        bpy.ops.wm.save_as_mainfile(filepath=str(blend))
        export_saved_source(blend,removed,images,resumed=True)
        return
    assert (OUT/'material_manifest.json').is_file(),'先完成v08材料处理；不要重建v07。'
    for suffix in ('diffuse','normal','properties'):
        name='cc_surface_v05_'+suffix+'.dds'
        shutil.copy2(BASE/'export'/name,EXPORT/name)
    bpy.ops.wm.open_mainfile(filepath=str(BASE/'reality_refinement_v07.blend'))
    bpy.context.preferences.filepaths.save_version=0
    collections={part:bpy.data.collections['arfv07_'+part] for part in shape.PARTS}
    for part,c in collections.items():
        c.name='arfv08_'+part
        c.hide_viewport=c.hide_render=False
    public_material=next(o.data.materials[0] for o in collections['flagship_bow'].objects if o.type=='MESH')
    for img in bpy.data.images:
        if img.filepath.endswith('.dds'):
            # 先解析Blender的//相对路径；Windows Path会把//export/file当作UNC共享根。
            img.filepath=str(EXPORT/Path(bpy.path.abspath(img.filepath)).name)
    common.EXP=EXPORT
    PRIVATE_MATERIAL=common.texture_material('reality_identity_v08')
    PRIVATE_MATERIAL.name='爱缪莎局部接口_公共工程底座_v08'
    surface.shared_specular_proxy(PRIVATE_MATERIAL)
    mid=collections['flagship_mid']
    for obj in mid.objects:
        if obj.type=='MESH':
            obj.data.materials.clear()
            obj.data.materials.append(PRIVATE_MATERIAL)
            for loop in obj.data.uv_layers.active.data:loop.uv.y=.5+.5*loop.uv.y
    # 炮位完整白圈在v07过于抢眼；保留形状与挂点，只改用涂层金属。
    collars=0
    for part,c in collections.items():
        use_material(PRIVATE_MATERIAL if part=='flagship_mid' else public_material)
        for obj in c.objects:
            if obj.type=='MESH' and '炮位锁紧边' in obj.name:
                style(obj,'plate')
                collars+=1
    assert collars==6
    use_material(PRIVATE_MATERIAL)
    removed=personal_interface(mid)
    use_material(public_material)
    common_hub_interfaces(collections['baseline_base'],collections['baseline_active'])
    support_observation_mounts(collections['baseline_base'],collections['baseline_active'])
    hub_observation(collections['baseline_active'])
    bpy.context.view_layer.update()
    assert shape.shared_signature(collections['baseline_base'])==shape.shared_signature(collections['baseline_active'])
    shared_count=len(shape.shared_signature(collections['baseline_base']))
    for part,c in collections.items():
        if part!='flagship_mid':
            assert all(not o.get('surface_role','').startswith('personal_') for o in c.objects)
    scene=bpy.context.scene
    scene.name='现实恒定舰个人接口与公共基线枢纽v08'
    camera=scene.camera
    previews=OUT/'previews'
    previews.mkdir(exist_ok=True)
    images=[]
    for name,parts,target,offset,scale in (
        ('flagship_oblique',shape.PARTS[:3],(0,-.5,0),(34,43,36),53),
        ('flagship_side',shape.PARTS[:3],(0,-.5,0),(48,9,12),49),
        ('baseline_base',('baseline_base',),(0,0,.5),(30,35,30),34),
        ('baseline_active',('baseline_active',),(0,0,.5),(30,35,30),34),
        ('flagship_interface',shape.PARTS[:3],(0,-.5,1.3),(12,16,19),15),
        ('flagship_geometry',shape.PARTS[:3],(0,-.5,0),(34,43,36),53)):
        for part,c in collections.items():c.hide_render=part not in parts
        surface.camera_view(scene,camera,target,offset,scale)
        if name=='flagship_geometry':
            gray=bpy.data.materials.new('仅几何评审_无个人色与发光')
            gray.use_nodes=True
            bsdf=gray.node_tree.nodes.get('Principled BSDF')
            bsdf.inputs['Base Color'].default_value=(.23,.23,.23,1)
            bsdf.inputs['Roughness'].default_value=.7
            scene.view_layers[0].material_override=gray
        scene.render.filepath=str(previews/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        scene.view_layers[0].material_override=None
        images.append((previews/(name+'.png')).relative_to(ROOT).as_posix())
        print('V08_PREVIEW_SAVED '+name,flush=True)
    for part,c in collections.items():c.hide_render=c.hide_viewport=part not in shape.PARTS[:3]
    surface.camera_view(scene,camera,(0,-.5,0),(34,43,36),53)
    bpy.data.orphans_purge(do_recursive=True)
    for img in bpy.data.images:
        if img.filepath.endswith('.dds'):img.pack()
    assert not bpy.data.libraries
    blend=OUT/'reality_identity_v08.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    export_saved_source(blend,removed,images)


if __name__=='__main__':main()
