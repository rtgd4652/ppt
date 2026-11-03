"""独立后台精修私人旗舰与基线枢纽；复用v06接口，不安装到Mod。"""

import argparse
import json
import math
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_central_court_surface_v02 as common
import build_central_court_surface_v03 as refinement
import build_milestone4_surface as pipeline

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'art/models/aemusa_reality_production_v06'
OUT = ROOT / 'art/models/aemusa_reality_refinement_v07'
EXPORT = OUT / 'export'
PARTS = ('flagship_bow', 'flagship_mid', 'flagship_stern', 'baseline_base', 'baseline_active')
MAT = None


def style(obj, role):
    refinement.metric_uv(obj, role, MAT)
    obj['surface_role'] = role
    return obj


def plate(c, label, pos, size, role='plate', rotation=(0, 0, 0)):
    obj = refinement.cut_plate(c, label, pos, size, role)
    obj.rotation_euler = rotation
    return obj


def loft(c, label, stations, role='armor', x=0):
    return common.loft(c, label, stations, role, x)


def box(c, label, pos, size, role='plate', rotation=(0, 0, 0)):
    return common.box(c, label, pos, size, role, rotation)


def beam(c, label, a, b, width=.15, role='silver'):
    return common.beam(c, label, a, b, width, role)


def ring(c, label, pos, outer, inner, depth, role='plate', rotation=(0, 0, 0), segments=12):
    """真实开口的工程护圈，不用不透明圆盘伪装喷口或设备井。"""
    vertices = []
    for z, radius in ((-depth/2, outer), (depth/2, outer), (-depth/2, inner), (depth/2, inner)):
        vertices += [(radius*math.cos(i*math.tau/segments), radius*math.sin(i*math.tau/segments), z)
                     for i in range(segments)]
    faces = []
    for i in range(segments):
        j = (i+1) % segments
        faces += [(i, j, segments+j, segments+i),
                  (2*segments+j, 2*segments+i, 3*segments+i, 3*segments+j),
                  (segments+i, segments+j, 3*segments+j, 3*segments+i),
                  (j, i, 2*segments+i, 2*segments+j)]
    mesh = bpy.data.meshes.new(c.name+'__'+label)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(mesh.name, mesh)
    c.objects.link(obj)
    obj.location, obj.rotation_euler = pos, rotation
    return style(obj, role)


def service(c, x, y, z, width=1.15, length=2.0):
    plate(c, '可拆换热座', (x, y, z), (width+.25, length+.25, .12))
    plate(c, '凹入百叶', (x, y, z+.09), (width, length, .08), 'vent')
    for index in range(5):
        box(c, '独立散热片', (x, y-length*.4+index*length*.2, z+.18),
            (width*.91, .085, .12), 'plate')
    for side in (-1, 1):
        box(c, '检修护轨', (x+side*(width/2+.035), y, z+.15), (.07, length, .14), 'silver')


def sockets(c, old_locators):
    """承载座服从原六个L槽，不增加烘焙炮管或改变实际武器数量。"""
    for name, data in old_locators.items():
        p = data['p']
        # v06已是原生PDX坐标；作者空间反向还原位置。
        pos = (-p[0], -p[2], p[1]) if 'flagship' in c.name else (p[0], p[2], p[1])
        loc = common.locator(c, name, pos)
        if 'gun_' in name:
            x, y, z = pos
            plate(c, '炮位装甲肩', (x, y, z-.32), (2.05, 2.25, .35), 'armor')
            common.cylinder(c, '炮位回转座', (x, y, z-.12), .79, .2, 'plate', vertices=12)
            ring(c, '炮位锁紧边', (x, y, z-.025), .83, .66, .05, 'silver')
        loc['source_interface'] = 'v06_original_unchanged'


def bow(c):
    loft(c, '有厚度变化的钝楔主壳', [(6,4.4,-.02,1.25), (10.4,4.75,0,1.45),
         (15.3,3.7,-.13,1.18), (20.2,1.7,-.32,.72)])
    loft(c, '下方承力脊', [(6,1.8,-1.1,.42), (14,1.35,-1.25,.4), (19.8,.9,-.95,.25)], 'plate')
    loft(c, '低矮观测背脊', [(6.3,.72,1.26,.22), (12.8,.64,1.5,.22),
         (16.7,.42,1.1,.16)], 'plate')
    for side in (-1, 1):
        # 分块斜肩改变外轮廓，板缝是真实间隙，不把整舰铺成白色长条。
        for y, x, width, length, z in ((7.7,3.48,1.4,2.6,1.3), (10.6,3.56,1.38,2.8,1.48),
                (13.5,3.03,1.25,2.65,1.3), (16.1,2.42,1.12,2.3,1.02), (18.15,1.64,.96,1.45,.73)):
            plate(c, '分段斜肩装甲', (side*x,y,z), (width,length,.25),
                  'plate', (0,side*.16,0))
            plate(c, '短段雾银受力边', (side*(x+width*.42), y, z-.02),
                  (.13,length*.84,.15), 'silver', (0,side*.16,0))
        for y, x in ((7.9,4.22),(11.6,4.3),(15,3.53)):
            plate(c, '侧舷分舱防护', (side*x,y,-.12), (.3,2.65,1.15), 'armor')
            box(c, '侧向维护锁', (side*(x+.17),y,-.02), (.07,.58,.25), 'silver')
        plate(c, '舰首传感面', (side*.8,18.9,.5), (.68,1.25,.1), 'glass')
        box(c, '有限航行灯', (side*1.3,19.63,.48), (.35,.1,.09), 'cyan')
        service(c, side*1.75,7.6,1.34,.7,1.2)


def middle(c):
    loft(c, '中段连续下脊', [(-7,3.9,-.7,.62), (-3.5,4.05,-.62,.66),
         (2.2,4.3,-.62,.66), (6,4.4,-.55,.72)])
    plate(c, '恒定作业井底', (0,-.5,.12), (3.6,5.3,.25), 'vent')
    for side in (-1, 1):
        loft(c, '侧舷承重舱', [(-7,.82,.08,1.05),(-4.4,1.12,.22,1.15),
             (.9,1.0,.22,.9),(4.5,.96,.3,.95),(6,.88,.3,.95)], 'armor',side*3.25)
        for y in (-5.0,-2.0,1.1,4.15):
            plate(c, '侧舷可换护板', (side*4.25,y,.2), (.3,2.55,1.15), 'plate')
            plate(c, '短上肩维护盖', (side*3.5,y,1.27), (1.35,2.5,.18), 'plate')
        # 低位主框和短立柱围住设备，顶部保持开放作业视线。
        beam(c, '恒定井纵向承架', (side*1.85,-3.15,.4),(side*1.85,1.15,.4),.23)
        for y in (-2.6,1.0):
            beam(c, '作业井立架',(side*1.85,y,.4),(side*1.85,y,2.35),.19)
            beam(c, '斜撑受力段',(side*2.65,y,.45),(side*1.85,y,2.35),.16,'plate')
            plate(c, '成对场作用端', (side*1.73,y,1.55), (.15,.6,.9),'plate')
            box(c, '受控状态端面',(side*1.63,y,1.55),(.045,.38,.58),'cyan')
        beam(c, '上方短维护梁',(side*1.85,-2.6,2.35),(side*1.85,1.0,2.35),.14,'plate')
        # 分叉后汇合的设备路径是局部仪器关系，不成为新增主炮。
        beam(c, '分歧仪轨',(0,-2.15,.62),(side*.95,-.7,.62),.105,'silver')
        beam(c, '汇合仪轨',(side*.95,-.7,.62),(0,.65,.62),.105,'silver')
        beam(c, '路径读数',(side*.23,-1.88,.69),(side*.8,-.96,.69),.04,'cyan')
        service(c,side*3.35,-5.2,1.35,.85,1.65)
    # 受约束的小体积仪器，围框与核心留有可见净空。
    core = common.geometry.prism(c.name+'__受控恒定模块',
        [(-.65,-.6),(0,-1.35),(.65,-.6),(.4,.4),(0,.7),(-.4,.4)], .95,1.55,c,MAT)
    style(core,'plate')
    plate(c,'仪器标定面',(0,-.35,1.59),(.48,1.28,.06),'glass')
    box(c,'局部状态读数',(0,-.3,1.64),(.08,.7,.04),'cyan')
    loft(c,'低矮指挥舱',[(-6.7,1.42,1.65,.8),(-5.6,1.58,1.8,.9),
         (-3.15,1.3,1.65,.84),(-2.7,.9,1.38,.55)],'plate')
    for side in (-1,1):
        plate(c,'分段指挥窗',(side*1.36,-4.65,2.18),(.1,1.6,.28),'glass')
        for y in (-5.25,-4.45):
            box(c,'舱侧人居灯',(side*1.47,y,1.69),(.04,.2,.08),'amber')
    plate(c,'舰桥装甲顶',(0,-4.65,2.78),(2.75,2.7,.13),'armor')


def stern(c):
    loft(c,'艉部承力脊',[(-19,1.2,-.35,.65),(-15.6,1.6,-.5,.8),
         (-11.2,3.85,-.45,.85),(-7,3.9,-.4,.9)],'armor')
    plate(c,'中央动力维护盖',(0,-12.4,.64),(1.7,4.8,.23),'plate')
    for side in (-1,1):
        x=side*2.4
        loft(c,'有收口的推进舱',[(-19.38,1.08,-.2,1.03),(-17.8,1.37,-.2,1.28),
             (-14.5,1.48,-.03,1.35),(-11.3,1.25,.06,1.18),(-10.2,.9,0,.96)],'armor',x)
        for y in (-17.3,-14.65,-12.0):
            plate(c,'推进舱分段脊盖',(x,y,1.27),(1.8,2.3,.19),'plate')
            plate(c,'推进护甲侧叶',(x+side*1.2,y,.1),(.28,2.35,1.45),'plate')
        service(c,x,-14.75,1.43,1.12,2.65)
        service(c,x,-11.5,1.4,1.12,1.65)
        beam(c,'艉侧导热承梁',(side*3.7,-18.1,.7),(side*4.7,-11.4,.7),.22,'plate')
        for index in range(6):
            y=-17.2+index*.85
            x1=side*(3.8+(y+17.2)*.14)
            plate(c,'外露换热叶',(x1,y,.4),(.73,.43,.1),'vent',(0,side*.35,0))
            beam(c,'换热叶根',(side*3.4,y,.45),(x1,y,.4),.08,'silver')
        ring(c,'推进口装甲护圈',(x,-19.36,-.2),1.1,.75,.35,'plate',(math.pi/2,0,0))
        ring(c,'喷口薄金属唇',(x,-19.58,-.2),.94,.76,.08,'silver',(math.pi/2,0,0))
        common.cylinder(c,'喷口凹入工作面',(x,-19.43,-.2),.73,.04,'cyan',
                        (math.pi/2,0,0),vertices=12)
        box(c,'艉侧小型维护灯',(x+side*1.35,-15.9,.2),(.05,.28,.1),'amber')
    loft(c,'艉炮台承座',[(-10.1,1.08,.9,.35),(-8.8,1.28,1.15,.45),
         (-7.1,1.1,.94,.38)],'plate')


def turn_objects(c, before, angle):
    bpy.context.view_layer.update()
    rotation=Matrix.Rotation(angle,4,'Z')
    for obj in set(c.objects)-before:
        obj.matrix_world=rotation @ obj.matrix_world


def hub_base(c):
    # 中央开口井与外围承框，四个臂的空间原点与已存接口保持一致。
    ring(c,'中央承载八角座',(0,0,-.18),4,2.35,.88,'armor',segments=8)
    ring(c,'中央维护边',(0,0,.37),3.82,2.45,.16,'plate',segments=8)
    common.cylinder(c,'设备井下底',(0,0,-.65),2.6,.18,'vent',vertices=8)
    ring(c,'下方屏蔽壳',(0,0,-1),2.65,2.14,.6,'plate',segments=8)
    for arm in range(4):
        before=set(c.objects)
        plate(c,'支臂根部过渡座',(0,3.35,-.03),(2.7,2.25,.62),'plate')
        plate(c,'设备段底座',(0,10,.12),(3.7,4.0,.66),'armor')
        plate(c,'设备段维护甲板',(0,10,.53),(3.45,3.8,.16),'plate')
        plate(c,'设备安装井',(0,10,.64),(2.7,2.75,.06),'vent')
        # 上下弦杆与斜腹杆形成真正的桁架，侧面不再是一块白色长方体。
        for side in (-1,1):
            for z in (-.43,.53):
                beam(c,'运输臂弦杆',(side*.78,3.6,z),(side*.78,8.7,z),.18,'plate')
            for index in range(4):
                y=3.8+index*1.18
                beam(c,'运输臂斜腹杆',(side*.78,y,-.43),(side*.78,y+1.12,.53),.105,'silver')
            for y in (8.6,11.4):
                beam(c,'模块可复用立柱',(side*1.48,y,.6),(side*1.48,y,2.48),.18,'plate')
                beam(c,'模块纵向维护架',(side*1.48,8.6,2.48),(side*1.48,11.4,2.48),.12,'silver') if y==8.6 else None
                box(c,'装配机械锁',(side*1.48,y,.77),(.35,.42,.25),'silver')
            beam(c,'中央井受力柱',(side*1.75,1.7,.3),(side*1.75,1.7,2.5),.22,'plate')
            beam(c,'中央井侧向撑',(side*2.8,2,.4),(side*1.75,1.7,2.45),.17,'silver')
            box(c,'设备端维护灯',(side*1.65,11.55,.68),(.15,.15,.06),'amber')
        for index in range(3):
            plate(c,'分段维护通道',(0,4.65+index*1.27,.52),(1.08,1.15,.12),'plate')
        plate(c,'吊装空口锁边',(0,10,2.43),(2.72,.22,.15),'silver')
        service(c,0,11.55,.66,1.5,.5)
        turn_objects(c,before,arm*math.pi/2)
    for obj in c.objects:
        if obj.type=='MESH':obj['shared_base_key']=obj.name.split('__',1)[-1]


def hub_active(c):
    common.cylinder(c,'中枢屏蔽资料舱',(0,0,1.28),2.48,1.9,'armor',vertices=8)
    common.cylinder(c,'中枢低矮封装顶',(0,0,2.34),2.32,.23,'plate',vertices=8)
    plate(c,'中枢检修顶盖',(0,0,2.5),(2.9,2.9,.14),'armor')
    plate(c,'中央解译读数面',(0,0,2.61),(1.5,1.5,.08),'glass')
    for arm in range(4):
        before=set(c.objects)
        # 运行设备加装于同一基础，而不是另造一个位置不同的空间站。
        loft(c,'封装分析舱',[(8.55,1.24,1.46,.72),(9.1,1.39,1.6,.87),
             (10.9,1.39,1.6,.87),(11.45,1.24,1.46,.72)],'armor')
        for index in range(3):
            plate(c,'可拆分析舱顶',(0,9.02+index*.94,2.52),(2.38,.82,.14),'plate')
        for side in (-1,1):
            for y in (9.1,10.75):
                plate(c,'分析舱侧面护板',(side*1.36,y,1.52),(.16,1.23,1.1),'plate')
                box(c,'屏蔽封装短锁边',(side*1.48,y,1.72),(.07,.6,.12),'silver')
            box(c,'有效运行状态线',(side*1.46,10.0,1.05),(.04,1.32,.07),'cyan')
            plate(c,'中枢四向防护面',(side*.92,2.23,1.34),(1.3,.2,1.5),'plate')
        box(c,'中央基线状态面',(0,2.47,1.58),(.72,.05,.09),'cyan')
        plate(c,'数据臂接口封装',(0,3.25,.79),(1.25,1.4,.32),'armor')
        turn_objects(c,before,arm*math.pi/2)


def shared_signature(c):
    result={}
    for obj in c.objects:
        if obj.type=='MESH' and 'shared_base_key' in obj:
            result[obj['shared_base_key']]={
                'transform':[float(v) for row in obj.matrix_world for v in row],
                'vertices':[tuple(v.co) for v in obj.data.vertices],
                'faces':[tuple(p.vertices) for p in obj.data.polygons],
                'uv':[tuple(loop.uv) for loop in obj.data.uv_layers.active.data]}
    return result


def export_definitions(records):
    # 复用经过检查的实体结构，仅替换本候选名字与目录，不修改旧样品。
    from build_reality_production_v06 import definitions as old_definitions
    import build_reality_production_v06 as previous
    previous.EXPORT=EXPORT
    old_definitions(records)
    for suffix in ('meshes.gfx','entities.asset'):
        old=EXPORT/('_reality_production_v06_'+suffix)
        text=old.read_text(encoding='utf-8').replace('v06','v07').replace('production','refinement')
        target=EXPORT/('_reality_refinement_v07_'+suffix)
        target.write_text(text,encoding='utf-8')
        old.unlink()  # 仅本轮新目录内的临时定义，既有v06文件完全不改。


def main():
    global MAT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdx-addon-root',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('仅允许独立background factory-startup，不能修改用户交互场景。')
    sys.path.insert(0,args.pdx_addon_root)
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    EXPORT.mkdir(parents=True,exist_ok=True)
    for suffix in ('diffuse','normal','properties'):
        name='cc_surface_v05_'+suffix+'.dds'
        shutil.copy2(BASE/'export'/name,EXPORT/name)
    common.EXP=EXPORT
    MAT=common.texture_material('cc_surface_v05')
    MAT.name='现实恒定舰与枢纽_共享工程材质v07'
    refinement.shared_specular_proxy(MAT)
    common.MAT=MAT
    common.style=style
    collections={part:common.group('arfv07_'+part) for part in PARTS}
    bow(collections['flagship_bow'])
    middle(collections['flagship_mid'])
    stern(collections['flagship_stern'])
    hub_base(collections['baseline_base'])
    active=collections['baseline_active']
    for original in collections['baseline_base'].objects:
        obj=original.copy()
        obj.data=original.data.copy()
        active.objects.link(obj)
    hub_active(active)
    reference={}
    for part,c in collections.items():
        old=read_meshfile(str(BASE/'export'/('arfv06_'+part+'.mesh')))
        reference[part]={node.tag:node.attrib for node in old.findall('./locator/*')}
        sockets(c,reference[part])
    bpy.context.view_layer.update()
    assert shared_signature(collections['baseline_base'])==shared_signature(active)
    shared_count=len(shared_signature(active))
    print('V07_GEOMETRY_READY shared_base_objects='+str(shared_count),flush=True)
    # 源文件保持作者坐标。相机/灯光置于根，不随区段隐藏或进入简化网格。
    scene,camera=common.render_setup()
    for obj in list(scene.objects):
        if obj.type in ('CAMERA','LIGHT'):
            if obj.name not in scene.collection.objects:scene.collection.objects.link(obj)
            for group in list(obj.users_collection):
                if group!=scene.collection:group.objects.unlink(obj)
    scene.name='现实恒定旗舰与基线枢纽精修v07'
    previews=OUT/'previews'
    previews.mkdir(exist_ok=True)
    images=[]
    for name,parts,target,offset,scale in (
        ('flagship_oblique',PARTS[:3],(0,-.5,0),(34,43,36),53),
        ('flagship_side',PARTS[:3],(0,-.5,0),(48,9,12),49),
        ('baseline_base',('baseline_base',),(0,0,.5),(30,35,30),34),
        ('baseline_active',('baseline_active',),(0,0,.5),(30,35,30),34),
        ('flagship_device',PARTS[:3],(0,-.5,1.3),(12,16,19),15)):
        for part,c in collections.items():c.hide_render=part not in parts
        refinement.camera_view(scene,camera,target,offset,scale)
        scene.render.filepath=str(previews/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        images.append((previews/(name+'.png')).relative_to(ROOT).as_posix())
        print('V07_PREVIEW_SAVED '+name,flush=True)
    for part,c in collections.items():c.hide_render=c.hide_viewport=part not in PARTS[:3]
    refinement.camera_view(scene,camera,(0,-.5,0),(34,43,36),53)
    bpy.data.orphans_purge(do_recursive=True)
    assert not bpy.data.libraries
    for img in bpy.data.images:
        if img.filepath.lower().endswith('.dds'):img.pack()
    blend=OUT/'reality_refinement_v07.blend'
    names={p:c.name for p,c in collections.items()}
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    assert not bpy.data.libraries
    assert len([i for i in bpy.data.images if i.filepath.endswith('.dds') and i.packed_file])==3
    collections={p:bpy.data.collections[n] for p,n in names.items()}
    bpy.context.view_layer.update()
    assert shared_signature(collections['baseline_base'])==shared_signature(collections['baseline_active'])
    pipeline.EXPORT,pipeline.ROOT=EXPORT,ROOT
    records=[]
    for part,c in collections.items():
        c.hide_viewport=c.hide_render=False
        for obj in c.objects:
            if obj.type=='MESH':
                assert all(math.isfinite(v) and 0<=v<=1 for loop in obj.data.uv_layers.active.data for v in loop.uv)
                # 先烘焙局部变换，再旋转导出内存副本，源文件不改。
                obj.data.transform(obj.matrix_world)
                obj.matrix_world=Matrix.Identity(4)
                if part.startswith('flagship'):obj.data.transform(Matrix.Rotation(math.pi,4,'Z'))
                obj.data.update()
            elif obj.type=='EMPTY' and part.startswith('flagship'):
                obj.location.x*=-1
                obj.location.y*=-1
                obj.rotation_euler=(0,0,math.pi) if obj['pdx_locator_name'].startswith('engine_') else (0,0,0)
        record=pipeline.export_group(c,export_meshfile,read_meshfile)
        pdx=read_meshfile(str(ROOT/record['mesh']))
        locators={node.tag:node.attrib for node in pdx.findall('./locator/*')}
        assert locators.keys()==reference[part].keys()
        for name,data in locators.items():
            assert max(abs(a-b) for a,b in zip(data['p'],reference[part][name]['p']))<1e-5
            assert abs(sum(a*b for a,b in zip(data['q'],reference[part][name]['q'])))>.99999
        assert record['material_count']==1
        record.update(lod=0,original_locator_transforms_preserved=True)
        records.append(record)
        for level,ratio in ((1,.5),(2,.23)):
            lod=common.simplified(c,level,ratio)
            row=pipeline.export_group(lod,export_meshfile,read_meshfile)
            assert row['triangles']<record['triangles'] and row['locators']==record['locators']
            row.update(lod=level,source_part=record['part'],automatic_lod_switching=False)
            records.append(row)
    export_definitions(records)
    manifest={'date':'2026-11-03','base_commit':'1853b00',
        'status':'offline_refinement_checks_passed','formal_appearance':'draft_pending_human_review',
        'runtime_installed':False,'mod_files_changed':False,'game_operated':False,
        'user_live_blender_scene_modified':False,'source_reopened':True,'packed_dds':3,
        'source_blend':blend.relative_to(ROOT).as_posix(),
        'authoring_axes':'+Y forward / +Z up','export_axes':'native PDX -Z forward',
        'geometry_changed':True,'six_L_slots_preserved':True,'all_original_locator_transforms_preserved':True,
        'hub_shared_foundation_objects':shared_count,'hub_foundation_geometry_uv_transforms_identical':True,
        'material':'v05 shared DDS copied unchanged, no new emission or palette',
        'previews':images,'comparison':'same light/camera settings as v06 for first four views',
        'meshes':records,'automatic_lod_switching':False,
        'runtime_scale_particles_and_gameplay':'not retested; candidate not installed',
        'next_step':'review candidate silhouette and refine if needed, then one merged asset integration'}
    (OUT/'refinement_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('REALITY_V07_OK five refined parts, original locators preserved, shared hub foundation identical',flush=True)


if __name__=='__main__':main()
