"""独立后台制作中庭级与造境平台完整灰模；原版参照只落本机忽略目录。"""
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
import build_central_court_kit as kit

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art/models/central_court_full_candidates_v01'
EXP=OUT/'export'
LOCAL=ROOT/'art/reference_library/central_court_collision_20261031'
GAME=Path('F:/steam/steamapps/common/Stellaris')
GROUPS={}
MAT=None
REUSE=[]


def group(name):
    c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);GROUPS[name]=c;return c


def box(c,label,pos,size,angle=0):return kit.block(c,MAT,label,pos,size,angle)
def prism(c,label,points,low,high):return kit.prism(c,MAT,label,points,low,high)
def beam(c,label,a,b,width=.22):return kit.beam(c,MAT,label,a,b,width)
def locator(c,name,pos,rot=(0,0,0)):return kit.geometry.locator(c,name,pos,rot)


def component(c,key,pos,scale=1,rot=(0,0,0)):
    matrix=Matrix.Translation(Vector(pos))@Matrix.Rotation(rot[2],4,'Z')@Matrix.Rotation(rot[0],4,'X')@Matrix.Diagonal((scale,scale,scale,1))
    for original in bpy.data.collections[key].objects:
        if original.type!='MESH':continue
        obj=original.copy();obj.data=original.data.copy();obj.name=c.name+'__'+key;c.objects.link(obj)
        obj.data.materials.clear();obj.data.materials.append(MAT)
        obj.matrix_world=matrix@original.matrix_world
    REUSE.append(dict(collection=c.name,part=key,position=list(pos),scale=scale,rotation=list(rot)))


def ship():
    bow,mid,stern=[group('cc_candidate_cruiser_'+s) for s in ('bow','mid','stern')]
    # 成对前伸舰首与中轴炮道：武器方向由完整轮廓承担，不用粒子替代实体。
    for sign in (-1,1):
        points=[(sign*x,y) for x,y in [(1.8,3),(5.8,3),(6.2,10),(3.7,23),(2.2,25),(1.8,13)]]
        if sign<0:points.reverse()
        prism(bow,'前伸装甲体',points,-.8,1.0)
        box(bow,'舰首上装甲',(sign*3.4,10,1.22),(2.0,10,.45))
        beam(bow,'前部测量轨',(sign*2.1,10,1.9),(sign*2.6,21,1.5),.23)
        box(mid,'肩部装甲',(sign*4.3,-2.0,.4),(4.6,12.2,2.0),angle=-sign*.1)
        box(mid,'侧面维护台',(sign*6.9,-1.8,-.1),(1.0,7.5,.45))
        for y in (-3.5,-1,1.5):box(mid,'换热片',(sign*5.0,y,1.63),(2.7,.26,.21))
        component(stern,'cck_03_noncontact',(sign*5.5,-15,0),1.35)
        box(stern,'独立推进舱',(sign*5.5,-21.2,0),(3.5,5.1,2.1))
        for x in (-.8,.8):box(stern,'推进口内衬',(sign*5.5+x,-23.82,0),(.9,.18,1.2))
        beam(stern,'推进前段支撑',(sign*1.8,-10.8,0),(sign*5.5,-10.8,0),.65)
        component(mid,'cck_06_service',(sign*5.2,-3,1.45),1.1)
    prism(mid,'中央承载体',[(-2,-10),(2,-10),(3,2),(2,5),(-2,5),(-3,2)],-1.3,.9)
    component(mid,'cck_01_spine',(0,-3,-.3),1.35)
    box(mid,'舰桥基座',(0,-4.3,1.3),(3.2,3.5,1.3))
    box(mid,'舰桥观察舱',(0,-3.9,2.25),(2.4,2.0,.65))
    component(mid,'cck_05_calibration',(0,1.3,1.25),.7)
    box(stern,'中央艉段',(0,-15.3,-.2),(3.0,11.2,1.65))
    box(stern,'辅助推进口',(0,-21.05,-.2),(1.8,.2,1.0))
    box(bow,'脊炮下承台',(0,8.6,-.25),(2.2,9.0,1.05))
    for x in (-.56,.56):box(bow,'脊炮导轨',(x,17.2,.75),(.32,17.2,.45))
    box(bow,'脊炮口座',(0,24.8,.62),(1.6,.45,.8))
    locator(bow,'xl_gun_01',(0,25.1,.7))
    for i,(x,y) in enumerate(((-4,2.5),(4,2.5),(0,-7.1)),1):
        box(mid,'大型炮位基座',(x,y,1.7),(1.4,1.4,.4));locator(mid,'large_gun_0'+str(i),(x,y,2.0))
    box(stern,'艉部炮位',(0,-12.3,1.0),(1.4,1.4,.4));locator(stern,'large_gun_01',(0,-12.3,1.25))
    locator(stern,'engine_large_01',(-5.5,-24,0),(math.pi,0,0));locator(stern,'engine_large_02',(5.5,-24,0),(math.pi,0,0))
    return [bow,mid,stern]


def former(active):
    c=group('cc_candidate_worldformer_'+('active' if active else 'base'))
    box(c,'后部工程平台',(0,-8,0),(22,3.0,1.1))
    component(c,'cck_02_junction',(0,-8,.1),1.7)
    component(c,'cck_01_spine',(0,-12.4,0),1.25)
    for sign in (-1,1):
        box(c,'开放支架纵梁',(sign*9,-1,.0),(2.3,15,1.1))
        box(c,'人员施工舱',(sign*6.5,-8,1.1),(3.2,3.0,1.2))
        for y in (-5,0,5):component(c,'cck_06_service',(sign*9,y,.8),.85)
        beam(c,'内侧维护托臂',(sign*8.8,-7,.5),(sign*6.7,-5,.5),.55)
        if active:
            box(c,'作业塔下段',(sign*9,1,2.8),(1.6,2.0,5.0))
            component(c,'cck_03_noncontact',(sign*9,1,6.3),.85,(math.pi/2,0,0))
            box(c,'上部观测架',(sign*9,1,9.5),(2.3,2.5,1.0))
            component(c,'cck_05_calibration',(sign*7.2,1,9.1),.7,(0,0,sign*math.pi/2))
            component(c,'cck_04_core_frame',(sign*6.5,-8,1.9),.65)
        else:
            box(c,'待展开作业端基座',(sign*9,1,1.2),(2.0,2.4,1.2))
    locator(c,'planet_focus',(0,0,5.2));locator(c,'build_point',(0,-12.4,1.3))
    return c


def render_setup():
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.cycles.max_bounces=4
    scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
    scene.render.resolution_x=1440;scene.render.resolution_y=960;scene.view_settings.view_transform='Standard'
    if scene.world is None:scene.world=bpy.data.worlds.new('候选灰模背景')
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.075,.075,.075,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
    for position,energy,size in (((25,-28,48),30000,25),((-28,22,30),20000,24)):
        bpy.ops.object.light_add(type='AREA',location=position);obj=bpy.context.object;obj.data.energy=energy;obj.data.size=size
        obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';scene.camera=camera
    return scene,camera


def frame(scene,camera,path,groups,shown,target,offset,scale):
    for c in groups:c.hide_render=c not in shown
    camera.location=Vector(target)+Vector(offset);camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)


def native_references(import_meshfile):
    # 独立factory进程内只作本地灰模参照；不保存Blend或复制原版网格到可提交目录。
    LOCAL.mkdir(parents=True,exist_ok=True)
    specs=[('mammalian_battleship',[f'gfx/models/ships/mammalian_01/mammalian_01_battleship_{x}.mesh' for x in ['frame','bow_XL1','mid_L3','stern_L1']]),
           ('science_nexus',[f'gfx/models/ships/megastructures/think_tank/thinktank_part{i}.mesh' for i in (1,2,3)])]
    outputs=[]
    for label,files in specs:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        for relative in files:
            path=GAME/relative;assert path.is_file(),path
            import_meshfile(str(path),imp_mesh=True,imp_skel=True,imp_locs=False,join_materials=True)
        meshes=[];excluded=0
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH':continue
            if any(m and (m.name.lower().startswith('collision') or m.get('shader')=='Collision') for m in obj.data.materials):
                obj.hide_render=True;excluded+=1
            else:meshes.append(obj)
        assert meshes
        mat=kit.flat_material('仅用于本地原版轮廓对照',(.42,.42,.42))
        for obj in meshes:obj.data.materials.clear();obj.data.materials.append(mat)
        bpy.context.view_layer.update()
        points=[obj.matrix_world@Vector(p) for obj in meshes for p in obj.bound_box]
        low=Vector(tuple(min(p[i] for p in points) for i in range(3)));high=Vector(tuple(max(p[i] for p in points) for i in range(3)))
        center=(low+high)/2;scale=max(high-low)*1.5
        scene,camera=render_setup();camera.location=center+Vector((scale*.5,-scale*.7,scale*.7));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
        image=LOCAL/(label+'.png');scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
        outputs.append(dict(label=label,source_meshes=files,image=image.relative_to(ROOT).as_posix(),collision_meshes_excluded=excluded,scope='灰材质静态网格及静止姿态；无原版纹理/粒子/动画/最终曝光',native_geometry_committed=False))
    (LOCAL/'reference_manifest.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def candidates(export_meshfile,read_meshfile):
    global MAT
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    OUT.mkdir(parents=True,exist_ok=True);EXP.mkdir(parents=True,exist_ok=True);(OUT/'previews').mkdir(exist_ok=True)
    for name in ('gray_plate.dds','gray_normal.dds','gray_spec.dds'):shutil.copy2(ROOT/'art/models/central_court_kit_v01/export'/name,EXP/name)
    with bpy.data.libraries.load(str(ROOT/'art/models/central_court_kit_v01/central_court_kit_v01.blend'),link=False) as (source,dest):
        dest.collections=[x for x in source.collections if x.startswith('cck_')]
    assert len([c for c in bpy.data.collections if c.name.startswith('cck_')])==6
    kit.geometry.EXPORT=EXP;kit.pipeline.EXPORT=EXP
    MAT=kit.geometry.material('完整候选导出灰材质','gray_plate.dds',(.5,.5,.5))
    sections=ship();base=former(False);active=former(True);groups=sections+[base,active]
    records=[kit.pipeline.export_group(c,export_meshfile,read_meshfile) for c in groups]
    assert all(r['material_count']==1 for r in records)
    gfx=['# 完整灰模候选的注册样品，尚未安装。','objectTypes = {']
    for r in records:
        gfx += ['    pdxmesh = {',f'        name = "{r["part"]}_mesh"',f'        file = "gfx/models/central_court_full_candidates_v01/{r["part"]}.mesh"','        scale = 1.0']
        for shape in r['shape_names']:
            gfx += ['        meshsettings = {',f'            name = "{shape}"','            index = 0','            texture_diffuse = "gray_plate.dds"',
                    '            texture_normal = "gray_normal.dds"','            texture_specular = "gray_spec.dds"','            shader = "PdxMeshShip"','        }']
        gfx.append('    }')
    gfx.append('}');(EXP/'_central_court_candidates.gfx').write_text('\n'.join(gfx)+'\n',encoding='utf-8')
    preview=kit.flat_material('候选统一灰',(.42,.42,.42));original={}
    for c in groups:
        obj=next(o for o in c.objects if o.type=='MESH');original[obj.name]=list(obj.data.materials);obj.data.materials.clear();obj.data.materials.append(preview)
    planet_group=group('仅预览天体参照_不导出')
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=5.7,location=(0,0,5.2));planet=bpy.context.object
    for old in list(planet.users_collection):old.objects.unlink(planet)
    planet_group.objects.link(planet);planet.data.materials.append(kit.flat_material('天体参照灰',(.2,.2,.2)))
    for poly in planet.data.polygons:poly.use_smooth=True
    scene,camera=render_setup()
    frames=[]
    for stem,shown,target,offset,scale in [
        ('cruiser_three_quarter',sections,(0,0,0),(40,-60,54),63),
        ('cruiser_top',sections,(0,0,0),(0,0,80),82),
        ('worldformer_foundation',[base,planet_group],(0,-1,3),(34,-42,34),43),
        ('worldformer_operational',[active,planet_group],(0,-1,3),(34,-42,34),43)]:
        path=OUT/'previews'/(stem+'.png');frame(scene,camera,path,groups+[planet_group],shown,target,offset,scale);frames.append(path.relative_to(ROOT).as_posix())
    for c in groups:
        obj=next(o for o in c.objects if o.type=='MESH');obj.data.materials.clear()
        for mat in original[obj.name]:obj.data.materials.append(mat)
    for c in groups:c.hide_render=c not in sections;c.hide_viewport=c not in sections
    planet_group.hide_render=True;planet_group.hide_viewport=True
    camera.location=(40,-60,54);camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=63
    for c in list(bpy.data.collections):
        if c.name.startswith('cck_'):bpy.data.collections.remove(c)
    for mat in list(bpy.data.materials):
        if mat.library is not None:bpy.data.materials.remove(mat)
    bpy.data.orphans_purge(do_recursive=True)
    # append后的来源Library可保留弱引用。先证明交付图完全本地化，再移除来源元数据。
    for c in groups:
        assert c.library is None
        for obj in c.objects:
            assert obj.library is None and (obj.data is None or obj.data.library is None)
            if obj.type=='MESH':assert all(mat.library is None for mat in obj.data.materials)
    for lib in list(bpy.data.libraries):
        assert Path(bpy.path.abspath(lib.filepath)).resolve()==(ROOT/'art/models/central_court_kit_v01/central_court_kit_v01.blend').resolve(),lib.filepath
        bpy.data.libraries.remove(lib)
    assert len(bpy.data.libraries)==0,[(lib.filepath,lib.users) for lib in bpy.data.libraries]
    assert all(not im.filepath.lower().startswith(str(GAME).lower()) for im in bpy.data.images)
    for image in bpy.data.images:
        if image.filepath.lower().endswith('.dds'):image.pack()
    blend=OUT/'central_court_full_candidates_v01.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    manifest=dict(date='2026-10-31',status='draft_pending_human_review',runtime_installed=False,blender=bpy.app.version_string,
        targets=['AP-ST-11 中庭级战略舰/传承舰首','AP-ST-10 F08传承造境平台两阶段'],meshes=records,kit_reuse=REUSE,
        source_blend=blend.relative_to(ROOT).as_posix(),previews=frames,ship_sections_common_origin=True,
        planet_reference='仅预览比例参照，不导出；实际天体大小/轨道偏移需游戏匹配',
        unchanged=['ship_size/武器槽/数值','F08造境脚本/资格/费用','角色/个人旗舰/结局'],formal_assets_approved=False,
        native_geometry_in_source=False,engine_scale_locators_effects='not_run',game_operated=False)
    (OUT/'candidate_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    bpy.ops.wm.open_mainfile(filepath=str(blend));assert len(bpy.data.libraries)==0
    for record in records:
        c=bpy.data.collections[record['part']];objects=[o for o in c.objects if o.type=='MESH']
        assert len(objects)==1 and len(objects[0].data.polygons)==record['triangles']
        assert sorted(o['pdx_locator_name'] for o in c.objects if o.type=='EMPTY')==record['locators']
    (OUT/'saved_blend_check.json').write_text(json.dumps(dict(status='pass',meshes=5,source_reopened=True,external_blend_libraries=0,game_test=False),indent=2)+'\n',encoding='utf-8')
    print('FULL_CANDIDATES_OK 5 PDX meshes, 4 previews, saved file reopened.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pdx-addon-root',type=Path,required=True);p.add_argument('--mode',choices=['references','candidates','both'],default='both')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if not bpy.app.background or bpy.data.filepath:raise RuntimeError('只允许独立后台factory-startup，禁止用户交互场景。')
    sys.path.insert(0,str(args.pdx_addon_root))
    from io_pdx_mesh.pdx_blender.blender_import_export import import_meshfile,export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    if args.mode in ('references','both'):native_references(import_meshfile)
    if args.mode in ('candidates','both'):candidates(export_meshfile,read_meshfile)


if __name__=='__main__':main()
