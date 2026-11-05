"""独立后台制作终局旗舰结构灰模；不读旧船壳、不改用户场景或运行资源。"""

import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/models/aemusa_endgame_blockout_v01'
PREVIEW = OUT / 'previews'
BLEND = OUT / 'endgame_blockout_v01.blend'


def material(name, color, emission=0.0):
    """只做结构辨识用色，不宣称正式七都材质已经完成。"""
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = .64
    bsdf.inputs['Metallic'].default_value = .08
    bsdf.inputs['Emission Color'].default_value = (*color, 1)
    bsdf.inputs['Emission Strength'].default_value = emission
    return mat


def link_mesh(name, verts, faces, collection, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def loft(name, stations, collection, mat, subdivisions=1, end_curves=None):
    """按同一纵向坐标生成有厚度的截面，不用平面贴片冒充舰壳。"""
    section = [(1, 0), (.68, .66), (0, 1), (-.68, .66),
               (-1, 0), (-.68, -.66), (0, -1), (.68, -.66)]
    end_curves = end_curves or {}
    verts = [(cx + x * width, y + end_curves.get(i, 0) * abs(x)**2, cz + z * height)
             for i,(y, cx, cz, width, height) in enumerate(stations) for x, z in section]
    faces = []
    for i in range(len(stations) - 1):
        for j in range(8):
            faces.append((8*i+j, 8*i+(j+1)%8, 8*(i+1)+(j+1)%8, 8*(i+1)+j))
    faces += [tuple(reversed(range(8))), tuple(range(len(verts)-8, len(verts)))]
    obj = link_mesh(name, verts, faces, collection, mat)
    if subdivisions:
        mod = obj.modifiers.new('结构曲面细分', 'SUBSURF')
        mod.levels = subdivisions
        mod.render_levels = subdivisions
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def tube(name, points, radius, collection, mat):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new('POLY')
    spline.points.add(len(points)-1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    curve.materials.append(mat)
    return obj


def star_material():
    """三维程序化占位星空；用于观察核心，不是最终游戏着色器。"""
    mat = bpy.data.materials.new('中央星空_程序化占位')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    links = mat.node_tree.links
    out = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value = .8
    links.new(emission.outputs[0], out.inputs['Surface'])
    tex = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 5.5
    noise.inputs['Detail'].default_value = 3
    links.new(tex.outputs['Generated'], noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .25
    ramp.color_ramp.elements[0].color = (.002, .004, .014, 1)
    ramp.color_ramp.elements[1].position = .77
    ramp.color_ramp.elements[1].color = (.065, .036, .14, 1)
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    stars = nodes.new('ShaderNodeTexVoronoi')
    stars.inputs['Scale'].default_value = 65
    links.new(tex.outputs['Generated'], stars.inputs['Vector'])
    threshold = nodes.new('ShaderNodeMath')
    threshold.operation = 'LESS_THAN'
    threshold.inputs[1].default_value = .058
    links.new(stars.outputs['Distance'], threshold.inputs[0])
    mix = nodes.new('ShaderNodeMixRGB')
    links.new(threshold.outputs[0], mix.inputs[0])
    links.new(ramp.outputs['Color'], mix.inputs[1])
    mix.inputs[2].default_value = (.75, .82, 1.0, 1)
    links.new(mix.outputs[0], emission.inputs['Color'])
    return mat


def star_volume(collection, mat):
    # 星空沿舰体断面成为空间带，不做独立球体；纯几何视图不显示此效果体。
    rows=[(2,0,0,8.2,3.5),(-1,0,0,8.6,3.65),(-5.4,0,0,8.8,3.7),
          (-9.6,0,0,8.6,3.65),(-12.6,0,0,8.2,3.5)]
    obj = loft('星空缺口_空间带占位',rows,collection,mat,0,{0:2.0,4:-2.0})
    obj['role'] = 'visual_placeholder_not_hull_or_collision'
    return obj


def camera(scene, name, position, target, width, height, resolution):
    data = bpy.data.cameras.new(name)
    data.type = 'ORTHO'
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    data.ortho_scale = 1
    frame = data.view_frame(scene=scene)
    span_x = max(v.x for v in frame)-min(v.x for v in frame)
    span_y = max(v.y for v in frame)-min(v.y for v in frame)
    data.ortho_scale = max(width/span_x, height/span_y)
    scene.camera = obj
    return obj


def configure_scene(scene):
    # 由本机实际接受的引擎枚举决定，不依赖旧 Blender 版本名称。
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 20
        scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new(scene.name+'_背景')
    scene.world.use_nodes = True
    bg = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (.20, .24, .32, 1)
    bg.inputs['Strength'].default_value = .75
    try:
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.look = 'Medium High Contrast'
    except TypeError:
        pass
    scene.view_settings.exposure = 0
    scene.render.image_settings.color_mode = 'RGBA'


def area(scene, name, pos, energy, size, target=(0, 0, 0)):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size = energy, 'DISK', size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()
    return obj


def world_bvh(objects):
    deps = bpy.context.evaluated_depsgraph_get()
    verts, faces = [], []
    for obj in objects:
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        base = len(verts)
        verts += [obj.matrix_world @ v.co for v in mesh.vertices]
        faces += [tuple(base+i for i in t.vertices) for t in mesh.loop_triangles]
        evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(verts, faces, all_triangles=True)


def build():
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('构建仅允许在独立 --background --factory-startup 进程中执行。')
    OUT.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # 清掉factory-startup中未使用的默认材质，避免无关笔刷库写入作者源。
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    main = bpy.context.scene
    main.name = '终局旗舰_结构样稿'
    configure_scene(main)
    hull = bpy.data.collections.new('实体舰体')
    fx = bpy.data.collections.new('中央星空_视觉占位')
    sockets = bpy.data.collections.new('十六T定位器')
    for c in (hull, fx, sockets):
        main.collection.children.link(c)
    navy = material('靛蓝主体_占位', (.035, .055, .115))
    silver = material('雾银外壳_占位', (.32, .40, .53))
    gold = material('主轴暖金_占位', (.65, .46, .19), .35)
    dark = material('发射口深色_占位', (.008, .014, .027))
    cyan = material('推进指示_占位', (.08, .38, .50), 1.0)

    physical = []
    fore = [(50,0,0,.08,.06),(44,0,0,2.2,.7),(33,0,0,5.8,1.9),
            (21,0,0,8.6,3.1),(9,0,0,9.3,3.5),(2,0,0,8.2,3.5)]
    aft = [(-12.6,0,0,8.2,3.5),(-19,0,0,8.8,3.6),(-30,0,0,7.6,3.0),
           (-41,0,0,5.3,2.3),(-45,0,0,4.6,1.9)]
    physical += [loft('主舰体_前', fore, hull, navy, 1,{5:2.0}),
                 loft('主舰体_后', aft, hull, navy, 1,{0:-2.0})]
    for bank, sx, sz in [('A',-1,1),('B',1,1),('C',-1,-1),('D',1,-1)]:
        # 同一主坐标系：+Y舰首、+Z上方；四组浮置外壳均保留实体厚度。
        front = [(46,3.4,2.6,.08,.06),(36,6.4,4.0,1.9,.6),
                 (24,9.2,4.8,3.0,1.05),(12,10.3,5.2,3.8,1.25),
                 (4,10.1,4.9,3.4,1.0),(0,9.0,4.4,.08,.05)]
        rear = [(-11.5,9.0,4.3,.08,.05),(-20,10.8,4.8,3.3,1.05),
                (-30,10.0,4.3,3.0,1.0),(-42,7.0,3.0,2.0,.7),
                (-47,4.0,2.5,.08,.05)]
        for label, rows in [('前',front),('后',rear)]:
            transformed = [(y,sx*x,sz*z,w,h) for y,x,z,w,h in rows]
            physical.append(loft(f'悬隔外壳_{bank}_{label}', transformed, hull, silver, 2))
    star_volume(fx, star_material())
    # 主轴穿过空间缺口只是视觉占位，绝不承担机械承梁。
    tube('主轴细金线',[(0,49,.15),(0,33,1.95),(0,9,3.6),(0,2,3.72),
                       (0,-12.6,3.72),(0,-30,3.1),(0,-44,2.15)],.035,fx,gold)
    for y in (2,-12.6):
        bend=2 if y>0 else -2
        points=[(8.2*math.cos(t),y+bend*abs(math.cos(t))**2,3.5*math.sin(t))
                for t in [math.pi/12+i*5*math.pi/6/48 for i in range(49)]]
        tube('星空边界细线_'+str(y),points,.045,fx,gold)
    # 本地程序化旋臂只帮助理解星空的纵深，不是复制原作或正式游戏特效。
    galaxy=material('星空旋臂_占位',(.20,.16,.40),1.1)
    for phase in (0,math.pi):
        points=[]
        for i in range(85):
            t=i/84;r=.08+2.2*t;angle=phase+5.6*t
            points.append((1.5+r*math.cos(angle),-5.2+.7*r*math.sin(angle),3.65))
        tube('星空旋臂_'+str(phase),points,.035,fx,galaxy)
    for x in (-1.65,0,1.65):
        loft('推进指示_'+str(x),[(-45.1,x,0,.42,.45),(-45.4,x,0,.40,.42)],fx,cyan,0)

    # 仅检测模型静态实体对前向直线的遮挡；不冒称引擎瞄准或发射已经通过。
    bpy.context.view_layer.update()
    bvh = world_bvh(physical)
    records = []
    for bank, sx, sz in [('A',-1,1),('B',1,1),('C',-1,-1),('D',1,-1)]:
        for index, (y,x,z) in enumerate([(29,9.2,4.8),(20,12.0,5.5),(10,14.0,5.7),(-22,14.2,5.0)]):
            position = Vector((sx*x,y,sz*z))
            adjustment = 0
            while bvh.ray_cast(position+Vector((0,.15,0)),Vector((0,1,0)),120)[0] is not None:
                adjustment += .2
                position.x += sx*.2
                if adjustment > 6:
                    raise RuntimeError('发射方向仍受实体遮挡：'+bank+str(index))
            number = len(records)+1
            name = f't_gun_{number:02d}'
            obj = bpy.data.objects.new(name,None)
            sockets.objects.link(obj)
            obj.location = position
            obj.empty_display_type = 'ARROWS'
            obj.empty_display_size = .8
            obj['slot_size_intent'] = 'titanic'
            obj['forward_axis'] = '+Y'
            obj['bank'] = bank
            # 小型浮置发射接口只是形体占位，没有安装或复用原版炮塔。
            x0,y0,z0 = position
            physical.append(loft('发射接口_'+name,[(y0-.7,x0,z0,.62,.23),
                (y0-.1,x0,z0,.52,.19),(y0,x0,z0,.48,.16)],hull,dark,0))
            tube('接口指示_'+name,[(x0-.34,y0+.015,z0),(x0+.34,y0+.015,z0)],.025,fx,gold)
            records.append({'id':name,'bank':bank,'position':list(position),'rotation_radians':[0,0,0],
                            'forward_axis':[0,1,0],'outboard_adjustment':round(adjustment,2)})
    # 对包括发射接口在内的完整实体进行最终前向检查。
    bpy.context.view_layer.update()
    bvh = world_bvh(physical)
    for r in records:
        assert bvh.ray_cast(Vector(r['position'])+Vector((0,.15,0)),Vector((0,1,0)),120)[0] is None,r['id']

    area(main,'主光',(-35,30,65),28000,55)
    area(main,'轮廓光',(35,-40,25),18000,45)
    cam = camera(main,'概念角度',(-95,108,68),(0,0,0),112,78,(1400,980))
    master = bpy.data.collections.new('旗舰完整实例')
    # 新集合仅引用本次三个集合，用于同一网格的正交展示。
    for c in (hull,fx,sockets):
        master.children.link(c)
    sheet = bpy.data.scenes.new('同尺度正交三视')
    configure_scene(sheet)
    grey = bpy.data.scenes.new('纯几何正交三视')
    configure_scene(grey)
    top = Matrix.Rotation(math.pi/2,4,'Z')
    side = Matrix(((0,-1,0,0),(0,0,1,0),(-1,0,0,0),(0,0,0,1)))
    front = Matrix(((-1,0,0,0),(0,0,1,0),(0,1,0,0),(0,0,0,1)))
    for scene in (sheet,grey):
        for label, matrix, pos in [('TOP',top,(-24,25,0)),('SIDE',side,(-24,-12,0)),('FRONT',front,(53,8,0))]:
            obj = bpy.data.objects.new(label+'_同源实例',None)
            scene.collection.objects.link(obj)
            obj.instance_type='COLLECTION'
            obj.instance_collection=master if scene==sheet else hull
            obj.matrix_world=Matrix.Translation(Vector(pos)) @ matrix
        textmat=material(scene.name+'_标注',(.78,.84,.94),1.0)
        fontpath=Path('C:/Windows/Fonts/msyh.ttc')
        font=bpy.data.fonts.load(str(fontpath)) if fontpath.is_file() else None
        for label,loc,size in [('俯视图',(-69,43,8),2.0),('侧视图',(-69,0,8),2.0),('正视图',(42,23,8),2.0),
                              ('舰首 ←       → 舰尾',(-69,-25,8),1.3),
                              ('同一三维源 · 同一显示比例',(-69,-32,8),1.4),
                              ('结构样稿，星空为占位效果；不是最终外观',(-69,-36,8),1.1)]:
            curve=bpy.data.curves.new(label,'FONT');curve.body=label;curve.size=size
            if font:curve.font=font
            obj=bpy.data.objects.new(label,curve);scene.collection.objects.link(obj);obj.location=loc
            curve.materials.append(textmat)
        area(scene,'三视主光',(-35,25,100),45000,100)
        area(scene,'三视补光',(65,-20,60),24000,80)
        camera(scene,scene.name+'_相机',(0,4,180),(0,4,0),160,88,(1920,1056))
        if scene==grey:
            scene.render.engine='BLENDER_WORKBENCH'
            scene.display.shading.color_type='SINGLE'
            scene.display.shading.single_color=(.64,.66,.70)
            scene.display.shading.light='STUDIO'
            scene.display.shading.show_cavity=True
            scene.display.shading.show_shadows=True
            scene.display.shading.background_type='WORLD'
            scene.world.color=(.035,.045,.065)
        # 标注转为轮廓网格，使作者源可独立打开，不打包整套系统字体。
        bpy.context.window.scene=scene
        bpy.context.view_layer.update()
        deps=bpy.context.evaluated_depsgraph_get()
        for obj in list(scene.objects):
            if obj.type=='FONT':
                mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(deps))
                replacement=bpy.data.objects.new(obj.name+'_轮廓',mesh)
                replacement.matrix_world=obj.matrix_world.copy()
                scene.collection.objects.link(replacement)
                bpy.data.objects.remove(obj,do_unlink=True)
    bpy.context.window.scene=main
    main.camera=cam
    # 只清理由本独立factory-startup进程生成的无使用者数据。
    if hasattr(bpy.data,'orphans_purge'):
        bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    # 在保存后读回本文件验证，不对游戏资源作导出或安装。
    manifest={'status':'structural_blockout_pending_visual_review','coordinates':'+Y bow, +Z up; author units, not metres',
              'source_reference':'art/concepts/aemusa_flagship_redesign_20261105/endgame_transcendent_v01.png',
              'blend':BLEND.relative_to(ROOT).as_posix(),'locators':records,
              'slot_count':len(records),'banks':{b:sum(r['bank']==b for r in records) for b in 'ABCD'},
              'forward_static_ray_clearance':'16 of 16 against blockout solid meshes; not engine weapon validation',
              'starfield':'procedural Blender visual placeholder, not a game-ready shader or approved new lore',
              'runtime_16T_implemented':False,'game_operated':False,'user_live_scene_modified':False,
              'automatic_lod':False,'appearance_approved':False}
    (OUT/'blockout_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('BLOCKOUT_SAVED '+str(BLEND),flush=True)


def verify():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    main=bpy.data.scenes['终局旗舰_结构样稿']
    bpy.context.window.scene=main
    locators=[o for o in main.objects if o.type=='EMPTY' and o.get('slot_size_intent')=='titanic']
    assert len(locators)==16 and len({o.name for o in locators})==16
    dims=[]
    for c in ['实体舰体']:
        for obj in bpy.data.collections[c].objects:
            if obj.type=='MESH':dims.extend(obj.matrix_world @ Vector(v) for v in obj.bound_box)
    bounds=[[min(p[i] for p in dims),max(p[i] for p in dims)] for i in range(3)]
    deps=bpy.context.evaluated_depsgraph_get();triangles=0
    for obj in bpy.data.collections['实体舰体'].objects:
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
        triangles+=len(mesh.loop_triangles);evaluated.to_mesh_clear()
    result={'source_reopened':True,'unique_T_locators':len(locators),'evaluated_hull_triangles':triangles,
            'bounds_xyz':bounds,'dimensions_xyz':[b[1]-b[0] for b in bounds],
            'orthographic_views':'collection instances of identical geometry, unit transforms, shared sheet camera',
            'runtime_validation':False,'appearance_approved':False}
    scales=[]
    for scene_name in ('同尺度正交三视','纯几何正交三视'):
        scene=bpy.data.scenes[scene_name]
        assert scene.camera.data.type=='ORTHO'
        instances=[o for o in scene.objects if o.instance_type=='COLLECTION']
        assert len(instances)==3
        for obj in instances:
            scale=list(obj.matrix_world.to_scale())
            assert all(abs(v-1)<1e-5 for v in scale)
            assert abs(obj.matrix_world.to_3x3().determinant()-1)<1e-5
            scales.append({'scene':scene_name,'instance':obj.name,'scale':scale})
    result['orthographic_instance_scales']=scales
    result['external_libraries']=[lib.filepath for lib in bpy.data.libraries]
    result['unpacked_external_fonts']=[f.filepath for f in bpy.data.fonts if f.filepath and not f.packed_file and f.filepath!='<builtin>']
    assert not result['external_libraries'],result['external_libraries']
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('BLOCKOUT_VERIFY '+json.dumps(result,ensure_ascii=False),flush=True)


def render(names):
    mapping={'oblique':'终局旗舰_结构样稿','three_view':'同尺度正交三视','geometry':'纯几何正交三视'}
    for name in names:
        scene=bpy.data.scenes[mapping[name]]
        bpy.context.window.scene=scene
        scene.render.filepath=str(PREVIEW/(name+'.png'))
        bpy.ops.render.render(write_still=True,scene=scene.name)
        print('RENDERED '+name,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['build','resume'],default='build')
    parser.add_argument('--views',nargs='*',default=['oblique','three_view','geometry'])
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if args.mode=='build':build()
    verify()
    render(args.views)


if __name__=='__main__':main()
