"""在独立Blender后台进程生成中央庭六部件灰模、PDX样品与组合评审图。"""
import argparse
import json
import math
from pathlib import Path
import shutil
import struct
import sys

sys.dont_write_bytecode = True
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_milestone4_graybox as geometry
import build_milestone4_surface as pipeline

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'art/models/central_court_kit_v01'
EXPORT = OUTPUT / 'export'
PREVIEWS = OUTPUT / 'previews'
PARTS = [
    ('cck_01_spine', '工程脊梁', 6.4),
    ('cck_02_junction', '四向接口座', 3.2),
    ('cck_03_noncontact', '非接触联接器', 6.4),
    ('cck_04_core_frame', '规则核心框', 6.4),
    ('cck_05_calibration', '观测标定叉', 6.4),
    ('cck_06_service', '检修护板', 3.2),
]


def block(group, mat, label, position, dimensions, angle=0, bevel=True):
    obj = geometry.box(group.name+'__'+label, position, dimensions, group, mat)
    obj.rotation_euler.z = angle
    if bevel and min(dimensions) > .15:
        mod = obj.modifiers.new('工程边倒角', 'BEVEL')
        mod.width = min(.065, min(dimensions)*.15)
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    # 灰模只有平色共享材质，沿用项目逐面投影；正式图集/UV尚未制作。
    pipeline.map_style(obj, 'plate', mat)
    return obj


def prism(group, mat, label, points, low, high):
    obj = geometry.prism(group.name+'__'+label, points, low, high, group, mat)
    pipeline.map_style(obj, 'plate', mat)
    return obj


def beam(group, mat, label, start, end, thickness=.18):
    delta = Vector(end)-Vector(start)
    obj = block(group, mat, label, (Vector(end)+Vector(start))/2,
                (thickness, thickness, delta.length), bevel=False)
    obj.rotation_euler = delta.to_track_quat('Z', 'Y').to_euler()
    return obj


def end_fittings(group, mat, length):
    # 所有直线部件共用2.4宽的接口，刻意保留可见的双锁座和中央通道。
    for sign in (-1, 1):
        for x in (-.94, .94):
            block(group, mat, '接口锁座', (x, sign*(length/2-.16), 0), (.38,.32,.98))


def build_part(index, mat):
    key, label, length = PARTS[index]
    group = bpy.data.collections.new(key)
    bpy.context.scene.collection.children.link(group)
    group['kit_id'] = 'CCK-'+str(index+1).zfill(2)
    group['design_status'] = 'draft_pending_human_review'
    if index == 0:
        prism(group, mat, '承重体', [(-1,-3.2),(1,-3.2),(1.25,-1.9),(1.25,1.9),(1,3.2),(-1,3.2),(-1.25,1.9),(-1.25,-1.9)], -.38,.38)
        for x in (-.85,.85):
            block(group, mat, '可更换上护甲', (x,0,.51), (.6,4.6,.23))
            block(group, mat, '维护边梁', (x*1.6,0,-.05), (.15,4.9,.32))
        for y in (-1.6,-.8,0,.8,1.6):
            block(group, mat, '横向检修肋', (0,y,.44), (.85,.13,.14), bevel=False)
    elif index == 1:
        prism(group, mat, '四向承重座', [(-1.6,-1),(-1,-1.6),(1,-1.6),(1.6,-1),(1.6,1),(1,1.6),(-1,1.6),(-1.6,1)], -.5,.5)
        block(group, mat, '上检修舱', (0,0,.75), (1.25,1.25,.5))
        for side in (-1,1):
            for y in (-.94,.94):
                block(group, mat, '侧接口锁座', (side*1.44,y,0), (.32,.38,.98))
        for x in (-.9,.9):
            block(group, mat, '释放手柄', (x,0,.65), (.13,.8,.17), bevel=False)
    elif index == 2:
        # 两个独立承载半体，中间0.9单位完全留空；禁止用暗杆穿过间隙。
        for sign in (-1,1):
            a,b = sorted((sign*.45,sign*3.2))
            prism(group, mat, '独立承载半体', [(-1.08,a),(1.08,a),(1.08,b),(-1.08,b)], -.34,.34)
            block(group, mat, '成对作用端', (0,sign*.62,.1), (2.38,.34,1.12))
            for x in (-.78,.78):
                block(group, mat, '观测稳定鞋', (x,sign*1.45,.55), (.32,1.12,.34))
                block(group, mat, '检修外缘', (x*1.6,sign*2.1,-.03), (.16,1.75,.24), bevel=False)
    elif index == 3:
        block(group, mat, '独立工程底座', (0,0,-.1), (2.0,6.1,.62))
        for x in (-1.32,1.32):
            for y in (-1.35,1.35):
                block(group, mat, '隔离支柱', (x,y,1.03), (.25,.42,2.0))
                beam(group, mat, '内收定位臂', (x,y,1.92),(x*.55,y*.55,2.25),.2)
        for z,angle in ((1.03,-.32),(1.5,.32),(1.97,-.18)):
            block(group, mat, '受控核心薄层', (0,0,z), (1.18,.92,.17), angle=angle)
        for y in (-2.55,2.55):
            block(group, mat, '安全供能舱', (0,y,.51), (1.5,.65,.58))
    elif index == 4:
        block(group, mat, '仪器承重体', (0,-.6,-.03), (1.8,4.9,.7))
        for x,height in ((-1.05,1.32),(1.05,1.65)):
            block(group, mat, '标定叉臂', (x,.2,height/2), (.36,5.0,height))
            block(group, mat, '收发测量端', (x,2.1,height*.85), (.62,.85,.42))
            for y in (-1.5,-.6,.3):
                block(group, mat, '对向测量片', (x*.76,y,.9), (.32,.16,.62), bevel=False)
        block(group, mat, '人员维护舱', (0,-2.35,.55), (.95,1.1,.45))
    else:
        prism(group, mat, '折边护板', [(-1.15,-1.6),(1.15,-1.6),(1.32,-.7),(1.32,.7),(.9,1.6),(-.9,1.6),(-1.32,.7),(-1.32,-.7)], -.14,.14)
        for x in (-1.0,1.0):
            block(group, mat, '可拆检修梁', (x,0,.27), (.24,2.3,.3))
        for y in (-.9,-.45,0,.45,.9):
            block(group, mat, '换热百叶', (0,y,.23), (1.36,.16,.16), bevel=False)
        block(group, mat, '检修方向凸标', (.55,-1.15,.34), (.3,.32,.23))
    end_fittings(group, mat, length)
    geometry.locator(group,'cc_in',(0,-length/2,0),(0,0,math.pi))
    geometry.locator(group,'cc_out',(0,length/2,0))
    geometry.locator(group,'cc_service',(0,0,1.15))
    if index == 1:
        geometry.locator(group,'cc_left',(-1.6,0,0),(0,0,math.pi/2))
        geometry.locator(group,'cc_right',(1.6,0,0),(0,0,-math.pi/2))
    group.asset_mark()
    group.asset_data.description = label+'；中央庭公共工程灰模候选，非正式外观。'
    return group


def flat_material(name, color, emission=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes=True
    node=mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Roughness'].default_value=.72
    if emission:
        emitter=mat.node_tree.nodes.new('ShaderNodeEmission')
        emitter.inputs['Color'].default_value=(*color,1)
        emitter.inputs['Strength'].default_value=1
        mat.node_tree.links.new(emitter.outputs[0],mat.node_tree.nodes['Material Output'].inputs['Surface'])
    return mat


def verify_saved():
    # 在另一个隔离进程重新打开磁盘文件，检查真实保存结果；不再次渲染或改写源文件。
    blend=OUTPUT/'central_court_kit_v01.blend'
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    manifest=json.loads((OUTPUT/'kit_manifest.json').read_text(encoding='utf-8'))
    assert len(bpy.data.libraries)==0
    for record in manifest['parts']:
        group=bpy.data.collections[record['part']]
        meshes=[o for o in group.objects if o.type=='MESH']
        assert len(meshes)==1 and len(meshes[0].data.polygons)==record['triangles']
        assert all(math.isfinite(v) for vertex in meshes[0].data.vertices for v in vertex.co)
        assert group.asset_data is not None
        assert sorted(o['pdx_locator_name'] for o in group.objects if o.type=='EMPTY')==record['locators']
    gallery=bpy.data.scenes['中央庭_灰模评审']
    instances=sum(o.instance_type=='COLLECTION' for o in gallery.objects)
    assert instances==16
    packed=[im for im in bpy.data.images if im.filepath.lower().endswith('.dds') and im.packed_file is not None]
    assert len(packed)==3
    custom_fonts=[font for font in bpy.data.fonts if font.filepath.lower().endswith(('.ttf','.ttc'))]
    assert all(getattr(font,'packed_file',None) is None for font in custom_fonts)
    for relative in manifest['previews']:
        with (ROOT/relative).open('rb') as f:header=f.read(24)
        assert header[:8]==b'\x89PNG\r\n\x1a\n'
        assert struct.unpack('>II',header[16:24]) in [(1600,1100),(1280,900)]
    result=dict(status='pass',source_reopened=True,parts=6,collection_instances=instances,
                packed_project_dds=len(packed),font_bytes_embedded=False,external_blend_libraries=0,
                checks='saved mesh counts, finite vertices, asset marks, locator names, previews; no engine validation')
    (OUTPUT/'saved_blend_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('CCK_REOPEN_OK '+json.dumps(result,ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdx-addon-root',required=True,type=Path)
    parser.add_argument('--font',type=Path,default=Path('C:/Windows/Fonts/msyh.ttc'))
    parser.add_argument('--verify-saved',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('仅允许在独立后台、未载入现有文件的factory-startup场景中构建。')
    if args.verify_saved:
        verify_saved()
        return
    bpy.context.preferences.filepaths.save_version=0
    sys.path.insert(0,str(args.pdx_addon_root.resolve()))
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    EXPORT.mkdir(parents=True,exist_ok=True);PREVIEWS.mkdir(parents=True,exist_ok=True)
    # 只复用项目自产的平色导出贴图，不复制原版几何或外部模型。
    for name in ('gray_plate.dds','gray_normal.dds','gray_spec.dds'):
        shutil.copy2(ROOT/'art/models/milestone4_graybox/export'/name,EXPORT/name)
    geometry.EXPORT=EXPORT;pipeline.EXPORT=EXPORT
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    library=bpy.context.scene;library.name='中央庭_原点部件库'
    mat=geometry.material('中央庭Kit导出灰材质','gray_plate.dds',(.5,.5,.5))
    groups=[build_part(i,mat) for i in range(6)]
    ports={g.name:{o['pdx_locator_name']:dict(position=list(o.location),angle=o.rotation_euler.z)
                  for o in g.objects if o.type=='EMPTY'} for g in groups}
    records=[pipeline.export_group(g,export_meshfile,read_meshfile) for g in groups]
    for record in records: assert record['triangles']<=1800,record
    # 只交付样品注册文本；运行目录/最终尺度需在外观确定后独立接入。
    gfx=['# 中央庭部件库灰模样品注册；尚未复制到mod运行目录。','objectTypes = {']
    for record in records:
        key=record['part'];gfx += ['    pdxmesh = {',f'        name = "{key}_mesh"',
            f'        file = "gfx/models/central_court_kit_v01/{key}.mesh"','        scale = 1.0']
        for i,shape in enumerate(record['shape_names']):
            gfx += ['        meshsettings = {',f'            name = "{shape}"',f'            index = {i}',
                '            texture_diffuse = "gray_plate.dds"','            texture_normal = "gray_normal.dds"',
                '            texture_specular = "gray_spec.dds"','            shader = "PdxMeshShip"','        }']
        gfx.append('    }')
    gfx.append('}');(EXPORT/'_central_court_kit_meshes.gfx').write_text('\n'.join(gfx)+'\n',encoding='utf-8')
    noncontact=next(o for o in groups[2].objects if o.type=='MESH')
    assert all(abs(v.co.y)>=.449 for v in noncontact.data.vertices)
    assert all(noncontact.data.vertices[e.vertices[0]].co.y*noncontact.data.vertices[e.vertices[1]].co.y>=0 for e in noncontact.data.edges)

    scene=bpy.data.scenes.new('中央庭_灰模评审')
    bpy.context.window.scene=scene
    scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
    scene.cycles.max_bounces=4
    scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.world=bpy.data.worlds.new('评审中性背景');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.07,.07,.07,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
    scene.view_settings.view_transform='Standard'
    gray=flat_material('评审中性灰',(.48,.48,.48))
    black=flat_material('剪影黑',(0,0,0),True);white=flat_material('剪影白',(1,1,1),True)
    floor_mat=flat_material('展示底色',(.09,.09,.09))
    text_mat=flat_material('评审文字',(.88,.88,.88),True)
    mesh_objects=[next(o for o in g.objects if o.type=='MESH') for g in groups]
    for obj in mesh_objects:obj.data.materials.clear();obj.data.materials.append(gray)
    font=bpy.data.fonts.load(str(args.font)) if args.font.exists() else None
    views={name:bpy.data.collections.new(name) for name in ('部件一览','线性组合','侧站组合')}
    for group in views.values():scene.collection.children.link(group)
    def instance(key,position,angle,view,name=None):
        obj=bpy.data.objects.new(name or key,None);obj.instance_type='COLLECTION';obj.instance_collection=bpy.data.collections[key]
        obj.location=position;obj.rotation_euler.z=angle;view.objects.link(obj)
        return obj
    def text(label,position,size,view):
        curve=bpy.data.curves.new('评审标注','FONT');curve.body=label;curve.size=size;curve.align_x='CENTER';curve.space_line=1.15
        if font:curve.font=font
        obj=bpy.data.objects.new('标注_'+label,curve);view.objects.link(obj);obj.location=position;curve.materials.append(text_mat)
        obj['label_base_position']=list(position)
        return obj
    for i,(key,label,length) in enumerate(PARTS):
        x=(i%3-1)*11;y=(.5-i//3)*12
        instance(key,(x,y,0),0,views['部件一览'])
        text('CCK-'+str(i+1).zfill(2)+' '+label,(x,y-4.6,.1),.58,views['部件一览'])
    links=[]
    def attach(source,port,key,view):
        bpy.context.view_layer.update()
        source_port=ports[source.instance_collection.name][port]
        angle=source.rotation_euler.z+source_port['angle']
        target=source.matrix_world@Vector(source_port['position'])
        pos=target-Matrix.Rotation(angle,4,'Z')@Vector(ports[key]['cc_in']['position'])
        obj=instance(key,pos,angle,view)
        bpy.context.view_layer.update()
        actual=obj.matrix_world@Vector(ports[key]['cc_in']['position'])
        distance=(actual-target).length;assert distance<1e-5
        a=Matrix.Rotation(angle,3,'Z')@Vector((0,1,0))
        b=Matrix.Rotation(angle+ports[key]['cc_in']['angle'],3,'Z')@Vector((0,1,0))
        normal_dot=a.dot(b);assert normal_dot<-.99999
        links.append(dict(parent=source.name,port=port,child=obj.name,distance=distance,normal_dot=normal_dot))
        return obj
    first=instance(PARTS[0][0],(0,0,0),0,views['线性组合'],'组合_工程脊梁')
    current=first
    for i in (2,3,4):current=attach(current,'cc_out',PARTS[i][0],views['线性组合'])
    text('线性作业链 · 同一组接口连接承载、联接、核心与测量',(0,-5.3,0),.55,views['线性组合'])
    junction=instance(PARTS[1][0],(0,0,0),0,views['侧站组合'],'组合_四向接口座')
    for port,i in (('cc_in',2),('cc_out',3),('cc_left',0),('cc_right',4)):
        attach(junction,port,PARTS[i][0],views['侧站组合'])
    # 检修护板作为独立服务组件落在右侧支架上，未计作主承载接口连接。
    instance(PARTS[5][0],(-5.1,0,1.05),math.pi/2,views['侧站组合'],'组合_检修护板')
    text('侧站组合 · 同一部件库的第二种用途',(0,-9.3,0),.6,views['侧站组合'])
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-1.6));floor=bpy.context.object;floor.name='仅展示地面';floor.data.materials.append(floor_mat)
    for position,energy,size in (((20,-20,30),18000,18),((-18,12,22),14000,16)):
        bpy.ops.object.light_add(type='AREA',location=position);light=bpy.context.object
        light.data.energy=energy;light.data.shape='DISK';light.data.size=size
        light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(25,-34,40));camera=bpy.context.object;camera.data.type='ORTHO';scene.camera=camera
    images=[]
    def render(view,stem,target,scale,camera_offset,resolution=(1600,1100),silhouette=False):
        for name,group in views.items():group.hide_render=(name!=view);group.hide_viewport=False
        camera.location=Vector(target)+Vector(camera_offset)
        camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
        for group in views.values():
            for obj in group.objects:
                if obj.type=='FONT':
                    obj.rotation_euler=camera.rotation_euler
                    # 一览标签在画面内下移，避开长部件的前端剪影，保持中文名称完整。
                    down=Vector((0,-.65,0)) if group.name=='部件一览' else Vector((0,0,0))
                    obj.location=Vector(obj['label_base_position'])+camera.rotation_euler.to_matrix()@down
        for obj in mesh_objects:obj.data.materials[0]=black if silhouette else gray
        floor.data.materials[0]=white if silhouette else floor_mat
        text_mat.node_tree.nodes['Emission'].inputs['Color'].default_value=((0,0,0,1) if silhouette else (.88,.88,.88,1))
        scene.render.resolution_x,scene.render.resolution_y=resolution
        path=PREVIEWS/(stem+'.png');scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True);images.append(path.relative_to(ROOT).as_posix())
    render('部件一览','kit_gray',(0,0,.6),39,(22,-33,43))
    render('部件一览','kit_silhouette',(0,0,.6),39,(22,-33,43),silhouette=True)
    render('线性组合','assembly_linear',(0,9,0),32,(24,-36,32),(1280,900))
    render('侧站组合','assembly_station',(0,0,0),29,(22,-31,34),(1280,900))
    # 保存时恢复导出材质；预览统一灰材质只用于判断结构和负形。
    for obj in mesh_objects:obj.data.materials[0]=mat
    for name,group in views.items():group.hide_viewport=(name!='部件一览');group.hide_render=(name!='部件一览')
    camera.location=(22,-33,43);camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=39
    for obj in views['部件一览'].objects:
        if obj.type=='FONT':
            obj.rotation_euler=camera.rotation_euler
            obj.location=Vector(obj['label_base_position'])+camera.rotation_euler.to_matrix()@Vector((0,-.65,0))
    for image in bpy.data.images:
        if image.filepath and image.filepath.lower().endswith('.dds'):image.pack()
    # factory-startup的笔刷默认材质不属于Kit，去掉其无关外部库依赖。
    for item in list(bpy.data.materials):
        if item.library is not None:
            assert all(item not in list(obj.data.materials) for obj in mesh_objects)
            bpy.data.materials.remove(item)
    bpy.data.orphans_purge(do_recursive=True)
    assert len(bpy.data.libraries)==0,'灰模源文件不应依赖外部blend库。'
    blend=OUTPUT/'central_court_kit_v01.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    manifest=dict(date='2026-10-31',status='draft_pending_human_review',runtime_installed=False,blender=bpy.app.version_string,
        new_geometry=True,legacy_geometry_used=False,individual_artifacts_replicated=False,
        coordinate='+Y forward, +Z up; construction units, not final game scale',common_port_width=2.4,
        parts=[dict(record,kit_id='CCK-'+str(i+1).zfill(2),label=PARTS[i][1],ports=ports[PARTS[i][0]]) for i,record in enumerate(records)],
        assembly_connections=links,noncontact_internal_gap=.9,noncontact_gap_geometry_checked=True,
        export_chain='project existing export_group + installed io_pdx_mesh; names/textures read back',
        game_scale_and_render='not_run',formal_assets_approved=False,vanilla_visual_collision='pending_visual_comparison',
        source_blend=blend.relative_to(ROOT).as_posix(),previews=images,font_path=str(args.font),font_packed=False,
        external_blend_libraries=0,gfx_sample='art/models/central_court_kit_v01/export/_central_court_kit_meshes.gfx',
        preview_material='uniform neutral gray / black silhouette; source retains export material',
        source_textures='project milestone4_graybox generated gray placeholders; no vanilla meshes copied')
    (OUTPUT/'kit_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('CCK_BUILD_OK '+str(len(records))+' parts; '+str(len(links))+' Blender snap connections; '+str(len(images))+' previews')
    verify_saved()


if __name__=='__main__':main()
