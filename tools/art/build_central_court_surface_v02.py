"""独立后台制作中央庭7个区段/阶段、共享UV材质和独立远景替代网格。"""

import argparse
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_milestone4_graybox as geometry
import build_milestone4_surface as pipeline

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/models/central_court_surface_candidates_v02'
EXP = OUT / 'export'
GROUPS = []
MAT = None
PARTS = {
    'ccv02_bow_standard': 'ARTIFACT_STRATEGIC_BOW',
    'ccv02_bow_spinal': 'ARTIFACT_POSTCRISIS_SPINAL_BOW',
    'ccv02_mid_artillery': 'ARTIFACT_STRATEGIC_MID_ARTILLERY',
    'ccv02_mid_carrier': 'ARTIFACT_STRATEGIC_MID_CARRIER',
    'ccv02_stern': 'ARTIFACT_STRATEGIC_STERN',
    'ccv02_worldformer_base': 'artifact_postcrisis_world_former_0',
    'ccv02_worldformer_active': 'artifact_postcrisis_world_former_1',
}


def group(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    collection['status'] = 'draft_pending_human_review'
    GROUPS.append(collection)
    return collection


def style(obj, role):
    pipeline.map_style(obj, role, MAT)
    obj['surface_role'] = role
    return obj


def box(c, label, position, dimensions, role='armor', rotation=(0, 0, 0), bevel=True):
    obj = geometry.box(c.name + '__' + label, position, dimensions, c, MAT)
    obj.rotation_euler = rotation
    if bevel and min(dimensions) > .12:
        modifier = obj.modifiers.new('工程护角', 'BEVEL')
        modifier.width = min(.09, min(dimensions) * .16)
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return style(obj, role)


def loft(c, label, stations, role='armor', center_x=0):
    """沿舰首轴布置有切角的截面，避免用等厚长方体代替主舰体。"""
    vertices = []
    for y, width, z, height in stations:
        profile = [(-.72, -1), (.72, -1), (1, -.55), (1, .55),
                   (.72, 1), (-.72, 1), (-1, .55), (-1, -.55)]
        vertices.extend((center_x + u * width, y, z + v * height) for u, v in profile)
    faces = [tuple(reversed(range(8)))]
    for row in range(len(stations) - 1):
        for k in range(8):
            faces.append((row * 8 + k, row * 8 + (k + 1) % 8,
                          (row + 1) * 8 + (k + 1) % 8, (row + 1) * 8 + k))
    faces.append(tuple((len(stations) - 1) * 8 + k for k in range(8)))
    mesh = bpy.data.meshes.new(c.name + '__' + label)
    # XZ截面沿+Y挤出，环绕方向与常见XY平面挤出相反，统一翻转为外法线。
    mesh.from_pydata(vertices, [], [tuple(reversed(face)) for face in faces])
    mesh.update()
    obj = bpy.data.objects.new(mesh.name, mesh)
    c.objects.link(obj)
    return style(obj, role)


def cylinder(c, label, position, radius, depth, role='silver', rotation=(0, 0, 0), vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=position, rotation=rotation)
    obj = bpy.context.object
    obj.name = c.name + '__' + label
    geometry.add_to_group(obj, c)
    return style(obj, role)


def beam(c, label, start, end, width=.18, role='silver'):
    delta = Vector(end) - Vector(start)
    return box(c, label, (Vector(start) + Vector(end)) / 2, (width, width, delta.length),
               role, delta.to_track_quat('Z', 'Y').to_euler(), bevel=False)


def locator(c, name, position, rotation=(0, 0, 0)):
    return geometry.locator(c, name, position, rotation)


def hardpoint(c, name, x, y, z, size=1.1):
    # 只烘焙炮位承载座，炮塔仍由区段的原生组件挂接，不重复烘焙炮管。
    cylinder(c, '炮位承载座', (x, y, z - .13), size, .26, 'plate')
    cylinder(c, '炮位锁圈', (x, y, z), size * .77, .12, 'silver')
    locator(c, name, (x, y, z + .13))


def service_bank(c, x, y, z, length=3, width=1):
    box(c, '检修底座', (x, y, z), (width + .25, length + .25, .17), 'plate')
    box(c, '换热百叶', (x, y, z + .13), (width, length, .14), 'vent', bevel=False)
    for offset in (-.44, .44):
        box(c, '百叶侧护边', (x + offset * width, y, z + .22), (.07, length, .13), 'silver', bevel=False)


def coupler(c, x, y, z, side):
    # 两个作用面朝向空隙，成对锁座保留维护关系；没有暗杆穿过净空。
    for dx in (0, side * .85):
        box(c, '非接触接口框', (x + dx, y, z), (.24, 2.3, 1.2), 'silver')
        box(c, '接口作用端', (x + dx + side * .13, y, z), (.07, 1.6, .72), 'cyan', bevel=False)


def bow(spinal):
    c = group('ccv02_bow_spinal' if spinal else 'ccv02_bow_standard')
    for side in (-1, 1):
        x = side * 4.5
        loft(c, '切角前伸舰体', [(6, 2.45, -.1, 1.1), (10, 2.9, 0, 1.2),
             (19, 2.15, .05, 1.0), (27, 1.2, -.15, .65), (29, .8, -.23, .42)], center_x=x)
        for y, width, length in ((9.4, 4.6, 4.3), (14.5, 4.0, 4.5), (20, 3.0, 4.5), (25, 1.8, 3.1)):
            box(c, '分层舰首装甲', (x, y, 1.14 - (y - 9) * .027), (width, length, .26), 'plate')
        box(c, '前缘切面', (x, 27.5, -.18), (1.48, 1.5, .22), 'silver')
        beam(c, '前轴观测轨', (side * 2.25, 8, 1.2), (side * 3.7, 25.6, .74), .13)
        service_bank(c, x + side * 1.45, 10.5, .95, 2.6, .55)
        for y in (10, 17, 23):
            box(c, '航行识别端', (x + side * (2.55 if y < 16 else 1.6), y, .25), (.12, .6, .17), 'cyan', bevel=False)
    loft(c, '舰首接续骨架', [(5.8, 2, -.25, .75), (9.5, 1.7, -.25, .7), (12.5, 1.2, -.25, .5)], 'silver')
    if spinal:
        # 传承脊炮为固定式不可见武器模板；导轨/汇流结构可作为舰体本体制作。
        for x in (-.74, .74):
            box(c, '脊炮外轨', (x, 18.4, -.08), (.28, 20.0, .42), 'silver')
            for y in (11, 14, 17, 20, 23, 26):
                box(c, '汇流节点', (x, y, .16), (.38, .36, .2), 'plate')
                box(c, '汇流工作端', (x * .73, y, .12), (.08, .24, .16), 'cyan', bevel=False)
        box(c, '炮膛下脊', (0, 17.5, -.72), (1.25, 19, .34), 'vent')
        locator(c, 'xl_gun_01', (0, 28.5, -.08))
    else:
        for side, name in ((-1, 'large_gun_01'), (1, 'large_gun_02')):
            hardpoint(c, name, side * 4.5, 15, 1.45)
    return c


def middle(carrier):
    c = group('ccv02_mid_carrier' if carrier else 'ccv02_mid_artillery')
    loft(c, '中央工程脊梁', [(-10, 2.2, -.3, 1.1), (-6, 2.6, -.15, 1.3), (4, 2.4, -.1, 1.25), (6, 2, -.2, 1.05)])
    for side in (-1, 1):
        x = side * 5.1
        loft(c, '肩部承载体', [(-10, 1.9, -.25, .8), (-7.5, 2.7, 0, 1.05),
             (2.8, 2.9, .1, 1.2), (6, 2.35, -.1, 1.05)], 'armor', x)
        for y in (-7, -3.2, 1.1, 4.3):
            box(c, '肩甲分区', (x, y, 1.35), (4.5, 2.8, .28), 'plate')
        beam(c, '外侧维护脊', (side * 7.5, -8, .5), (side * 7.5, 4.5, .5), .19)
        service_bank(c, side * 3.1, -4.0, 1.45, 4.2, .78)
        box(c, '维护通道', (side * 7.25, -4.5, .12), (.18, 3.6, .24), 'amber', bevel=False)
        if carrier:
            # 机库外口保留真实开口层次；黑色背墙与顶/底唇分别建模，不用发光贴图画洞。
            box(c, '机库内部', (side * 7.7, -.8, .15), (.34, 6.0, 1.6), 'vent', bevel=False)
            for z in (-.75, 1.1):
                box(c, '机库上下唇', (side * 8.45, -.8, z), (1.7, 6.4, .24), 'silver')
            for y in (-4.1, 2.5):
                box(c, '机库侧框', (side * 8.45, y, .18), (1.65, .28, 1.8), 'plate')
            box(c, '机库引导灯', (side * 8.9, -.8, -.61), (.13, 5.0, .12), 'cyan', bevel=False)
            locator(c, 'strike_craft_locator_' + ('01' if side < 0 else '02'),
                    (side * 9.2, -.8, .15), (0, 0, side * math.pi / 2))
        else:
            hardpoint(c, 'large_gun_' + ('01' if side < 0 else '02'), x, .8, 1.65)
    # 人类舰桥、观测和维修空间仍可辨，不以神器核心代替全舰结构。
    loft(c, '舰桥下层', [(-7.2, 1.65, 1.5, .55), (-5.8, 1.85, 1.65, .7), (-1.6, 1.2, 1.7, .58)], 'plate')
    box(c, '舰桥控制层', (0, -4.7, 2.6), (2.5, 3.8, .64), 'warm')
    box(c, '舰桥玻璃带', (0, -2.77, 2.62), (2.25, .1, .28), 'glass', bevel=False)
    box(c, '中央庭识别护板', (0, -4.8, 3.02), (1.8, 2.3, .13), 'silver')
    for x in (-.6, .6):
        beam(c, '标定天线', (x, -5.5, 3.05), (x, -5.5, 4.25), .09)
        box(c, '天线工作端', (x, -5.5, 4.28), (.45, .22, .12), 'silver')
    if carrier:
        for i, (x, y) in enumerate(((-4.8, 4.8), (4.8, 4.8), (-6.3, -7.5), (6.3, -7.5)), 1):
            hardpoint(c, 'small_gun_0' + str(i), x, y, 1.7, .55)
    else:
        hardpoint(c, 'large_gun_03', 0, 3.7, 1.7)
    return c


def stern():
    c = group('ccv02_stern')
    loft(c, '后部整备脊梁', [(-29, 1.65, -.2, .65), (-24, 2.0, -.1, .9),
         (-16, 3.0, -.1, 1.25), (-10, 2.2, -.3, 1.1)])
    for y in (-13.5, -18, -23.5):
        box(c, '后段分层护板', (0, y, 1.0), (3.3, 3.4, .25), 'plate')
        service_bank(c, 0, y, 1.17, 2.5, 1.2)
    hardpoint(c, 'large_gun_01', 0, -12.4, 1.6)
    for side in (-1, 1):
        x = side * 6.3
        loft(c, '独立推进舱', [(-31, 1.65, -.2, .9), (-28.5, 2.0, -.15, 1.15),
             (-19, 1.9, -.05, 1.1), (-16, 1.35, -.05, .8)], 'armor', x)
        for y in (-20, -24.5, -28.2):
            box(c, '推进舱上护板', (x, y, 1.15), (2.7, 3.2, .24), 'plate')
            service_bank(c, x, y, 1.33, 2.5, .8)
        coupler(c, side * 3.6, -20, 0, side)
        box(c, '喷口内腔', (x, -31.03, -.2), (2.8, .18, 1.6), 'vent', bevel=False)
        box(c, '喷口工作端', (x, -31.14, -.2), (2.15, .08, 1.04), 'cyan', bevel=False)
        for dx in (-1.4, 1.4):
            box(c, '喷口纵护边', (x + dx, -31.16, -.2), (.2, .35, 1.8), 'silver')
        for z in (-1.08, .68):
            box(c, '喷口横护边', (x, -31.16, z), (2.8, .35, .18), 'silver')
        locator(c, 'engine_large_' + ('01' if side < 0 else '02'), (x, -31.3, -.2), (math.pi / 2, 0, 0))
    return c


def platform(active):
    c = group('ccv02_worldformer_active' if active else 'ccv02_worldformer_base')
    box(c, '主承载横桥', (0, -10.5, .2), (32, 4.2, 2.3), 'armor')
    box(c, '上方服务甲板', (0, -10.5, 1.5), (30, 3.7, .35), 'plate')
    for x in range(-14, 15, 2):
        box(c, '模块化装配接口', (x, -12.65, .2), (.9, .3, 1.7), 'silver')
        box(c, '维护走道灯', (x, -12.84, .5), (.45, .08, .18), 'amber', bevel=False)
    loft(c, '后部控制与物料枢纽', [(-19, 3.5, .6, .9), (-17, 5, .7, 1.1), (-9, 4.2, .8, 1.2), (-7, 2.7, .4, .8)], 'armor')
    for x in (-3.0, 0, 3.0):
        box(c, '控制枢纽分层甲板', (x, -14, 2.12), (2.6, 6.5, .28), 'plate')
        service_bank(c, x, -14, 2.33, 3.8, .8)
    box(c, '工程控制楼', (0, -17, 2.8), (3.6, 2.1, 1.2), 'warm')
    box(c, '控制楼观测窗', (0, -15.91, 2.9), (3.0, .08, .35), 'glass', bevel=False)
    for side in (-1, 1):
        x = side * 13
        loft(c, '侧向作业台', [(-13, 2.4, .4, 1.1), (-7, 2.5, .5, 1.1), (1, 2.0, .5, 1.0), (3, 1.5, .4, .7)], 'armor', x)
        for y in (-8, -4, 0):
            box(c, '作业台可替换护板', (x, y, 1.72), (3.6, 3.2, .22), 'plate')
        box(c, '物料接口外罩', (side * 9.2, -12.2, 1.9), (2.7, 3.4, 1.0), 'silver')
        box(c, '物料接口内腔', (side * 9.2, -13.95, 1.9), (2.1, .15, .6), 'vent', bevel=False)
        for y in (-11, -6):
            # 散热板是独立可见结构；本版静态，不声称已接入展开动画。
            box(c, '下挂散热面', (side * 11.5, y, -2.6), (5.5, 3.8, .14), 'vent', (.4 * side, 0, 0), bevel=False)
            beam(c, '散热板维护撑', (side * 11.5, y, -.8), (side * 11.5, y, -2.7), .22)
        if active:
            # 收窄设备芯，显露角柱/斜撑与检修净空，避免把工作立架做成实心高楼。
            box(c, '立架设备芯', (x, -.8, 5.1), (1.6, 1.9, 6.6), 'armor')
            for dx in (-1.25, 1.25):
                for dy in (-1.48, 1.48):
                    box(c, '立架角柱', (x + dx, -.8 + dy, 5.1), (.26, .26, 6.8), 'silver')
            for z in (2.0, 4.1, 6.2, 8.2):
                box(c, '立架横向承载环', (x, -.8, z), (2.8, 3.2, .18), 'plate')
            for z in (2.0, 4.1, 6.2):
                beam(c, '外露斜撑', (x - 1.25, -2.28, z), (x + 1.25, -2.28, z + 2.0), .16)
            box(c, '立架承力背脊', (x + side * 1.4, -.8, 5), (.5, 3.6, 7.0), 'silver')
            for z in (2.6, 4.1, 5.6, 7.1):
                box(c, '作业立架检修盖', (x, -2.5, z), (2.1, .28, .8), 'armor')
            # 上下独立半体留下0.8净空，只有成对作用端与测量架跨越视线。
            box(c, '立架下作用端', (x, -.8, 8.5), (3.3, 3.5, .25), 'silver')
            box(c, '下作用面', (x, -.8, 8.68), (2.6, 2.6, .09), 'cyan', bevel=False)
            box(c, '上作业台独立半体', (x, -.8, 10.35), (3.0, 3.2, 1.5), 'plate')
            box(c, '上作用面', (x, -.8, 9.54), (2.6, 2.6, .09), 'cyan', bevel=False)
            box(c, '行星作业横梁', (side * 9.8, -.8, 11.1), (8.0, 3.0, 2.1), 'armor')
            for dx in (7.2, 9.6, 12):
                box(c, '横梁上护板', (side * dx, -.8, 12.32), (2.0, 2.7, .2), 'plate')
                service_bank(c, side * dx, -.8, 12.47, 1.8, .75)
            cylinder(c, '行星作业聚焦口', (side * 5.65, -.8, 11.1), 1.15, .3, 'silver', (0, math.pi / 2, 0), 16)
            cylinder(c, '聚焦口工作端', (side * 5.45, -.8, 11.1), .8, .12, 'cyan', (0, math.pi / 2, 0), 16)
            beam(c, '独立标定杆', (side * 15.4, -2.0, 1.9), (side * 15.4, -2.0, 8), .22)
            box(c, '标定端', (side * 15.4, -2.0, 8.1), (.75, 1.3, .3), 'silver')
        else:
            box(c, '待展开立架基座', (x, -.8, 2.45), (3.4, 3.6, 1.2), 'silver')
            box(c, '封存接口', (x, -.8, 3.1), (2.5, 2.6, .2), 'vent', bevel=False)
    locator(c, 'build_point', (0, -18.5, 2.0))
    locator(c, 'planet_focus', (0, 8.5, 9.0))
    return c


def texture_material(texture_prefix='cc_surface_v02'):
    mat = bpy.data.materials.new('中央庭共享图集v02')
    mat['shader'] = 'PdxMeshShip'
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    tex = {}
    for suffix in ('diffuse', 'properties', 'normal'):
        node = nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(EXP / (texture_prefix + '_' + suffix + '.dds')), check_existing=True)
        if suffix != 'diffuse':
            node.image.colorspace_settings.name = 'Non-Color'
        tex[suffix] = node
    links.new(tex['diffuse'].outputs['Color'], bsdf.inputs['Base Color'])
    prop = nodes.new('ShaderNodeSeparateColor')
    links.new(tex['properties'].outputs['Color'], prop.inputs['Color'])
    links.new(prop.outputs['Blue'], bsdf.inputs['Metallic'])
    inverse = nodes.new('ShaderNodeMath')
    inverse.operation = 'SUBTRACT'
    inverse.inputs[0].default_value = 1
    links.new(tex['properties'].outputs['Alpha'], inverse.inputs[1])
    links.new(inverse.outputs[0], bsdf.inputs['Roughness'])
    normal = nodes.new('ShaderNodeSeparateColor')
    links.new(tex['normal'].outputs['Color'], normal.inputs['Color'])
    combine = nodes.new('ShaderNodeCombineColor')
    combine.inputs['Blue'].default_value = 1
    links.new(normal.outputs['Green'], combine.inputs['Red'])
    flip = nodes.new('ShaderNodeMath')
    flip.operation = 'SUBTRACT'
    flip.inputs[0].default_value = 1
    links.new(tex['normal'].outputs['Alpha'], flip.inputs[1])
    links.new(flip.outputs[0], combine.inputs['Green'])
    nm = nodes.new('ShaderNodeNormalMap')
    links.new(combine.outputs[0], nm.inputs['Color'])
    links.new(nm.outputs[0], bsdf.inputs['Normal'])
    links.new(tex['diffuse'].outputs['Color'], bsdf.inputs['Emission Color'])
    links.new(normal.outputs['Blue'], bsdf.inputs['Emission Strength'])
    return mat


def simplified(source, level, ratio):
    """保存独立替代网格，不臆造引擎LOD字段；自动距离切换留待接入。"""
    c = group(source.name + '_lod' + str(level))
    for original in source.objects:
        obj = original.copy()
        if obj.data:
            obj.data = original.data.copy()
        c.objects.link(obj)
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj
            mod = obj.modifiers.new('远景简化', 'DECIMATE')
            mod.ratio = ratio
            mod.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=mod.name)
    return c


def definitions(records):
    gfx = ['# 独立候选注册；尚未安装，LOD替代文件不自动触发距离切换。', 'objectTypes = {']
    entities = ['# 独立预接入样品，不覆盖原版/当前玩法实体。']
    for record in records:
        name = record['part']
        gfx.extend(['    pdxmesh = {', f'        name = "{name}_mesh"',
                    f'        file = "gfx/models/central_court_surface_candidates_v02/{name}.mesh"', '        scale = 1.0'])
        for index, shape in enumerate(record['shape_names']):
            gfx.extend(['        meshsettings = {', f'            name = "{shape}"', f'            index = {index}',
                        '            texture_diffuse = "cc_surface_v02_diffuse.dds"',
                        '            texture_normal = "cc_surface_v02_normal.dds"',
                        '            texture_specular = "cc_surface_v02_properties.dds"',
                        '            shader = "PdxMeshShip"', '        }'])
        gfx.append('    }')
        if record['lod'] == 0:
            entities.extend(['entity = {', f'    name = "{name}_entity"', f'    pdxmesh = "{name}_mesh"',
                             '    default_state = "idle"', '    state = { name = "idle" }', '}'])
    gfx.append('}')
    (EXP / '_central_court_v02_meshes.gfx').write_text('\n'.join(gfx) + '\n', encoding='utf-8')
    (EXP / '_central_court_v02_entities.asset').write_text('\n'.join(entities) + '\n', encoding='utf-8')


def render_setup():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 20
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'Standard'
    scene.world = bpy.data.worlds.new('深空离线评审背景')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.035, .045, .065, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .35
    for position, power, size in (((-25, 10, 48), 58000, 30), ((30, -25, 25), 40000, 25), ((8, 35, 12), 28000, 18)):
        bpy.ops.object.light_add(type='AREA', location=position)
        light = bpy.context.object
        light.data.energy, light.data.size = power, size
        light.rotation_euler = (-light.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = 'ORTHO'
    scene.camera = camera
    return scene, camera


def main():
    global MAT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdx-addon-root', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('只允许独立后台factory-startup，禁止修改用户交互场景。')
    assert (OUT / 'surface_manifest.json').is_file(), '先运行prepare_central_court_surface_v02.py'
    sys.path.insert(0, str(args.pdx_addon_root))
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene['status'] = 'draft_pending_human_review'
    bpy.context.scene['runtime_installed'] = False
    bpy.context.scene['unit_note'] = '建模网格单位；未校准为米制或游戏尺度'
    bpy.context.preferences.filepaths.save_version = 0
    MAT = texture_material()
    pipeline.EXPORT, pipeline.ROOT = EXP, ROOT
    bases = [bow(False), bow(True), middle(False), middle(True), stern(), platform(False), platform(True)]
    assert {c.name for c in bases} == set(PARTS)
    records, variants = [], []
    for c in bases:
        source_objects = len([o for o in c.objects if o.type == 'MESH'])
        record = pipeline.export_group(c, export_meshfile, read_meshfile)
        record.update(lod=0, source_parts=source_objects, gameplay_target=PARTS[c.name])
        obj = next(o for o in c.objects if o.type == 'MESH')
        assert len(obj.data.materials) == 1
        assert all(0 <= value <= 1 for loop in obj.data.uv_layers.active.data for value in loop.uv)
        record['uv_in_bounds'] = True
        record['bounds'] = [[min(v.co[i] for v in obj.data.vertices) for i in range(3)],
                            [max(v.co[i] for v in obj.data.vertices) for i in range(3)]]
        records.append(record)
        for level, ratio in ((1, .5), (2, .23)):
            reduced = simplified(c, level, ratio)
            child = pipeline.export_group(reduced, export_meshfile, read_meshfile)
            child.update(lod=level, source_part=c.name, gameplay_target=PARTS[c.name], automatic_lod_switching=False)
            assert child['triangles'] < record['triangles']
            assert child['locators'] == record['locators']
            records.append(child)
            variants.append(reduced)
    definitions(records)
    reference = group('仅预览天体_不导出')
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=7.1, location=(0, 8.5, 9))
    planet = bpy.context.object
    geometry.add_to_group(planet, reference)
    planet_mat = bpy.data.materials.new('天体比例参照_非游戏资产')
    planet_mat.diffuse_color = (.15, .23, .29, 1)
    planet_mat.use_nodes = True
    planet_bsdf = next(n for n in planet_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    planet_bsdf.inputs['Base Color'].default_value = (.08, .13, .18, 1)
    planet_bsdf.inputs['Roughness'].default_value = .88
    planet.data.materials.append(planet_mat)
    for face in planet.data.polygons:
        face.use_smooth = True
    scene, camera = render_setup()
    scene.name = '中庭级及造境平台_材质候选v02'
    lookup = {c.name: c for c in bases}
    previews = []
    views = [
        ('cruiser_spinal_artillery', ['ccv02_bow_spinal', 'ccv02_mid_artillery', 'ccv02_stern'], (0, -1, 0), (43, 59, 49), 77),
        ('cruiser_standard_carrier', ['ccv02_bow_standard', 'ccv02_mid_carrier', 'ccv02_stern'], (0, -1, 0), (43, 59, 49), 77),
        ('worldformer_foundation', ['ccv02_worldformer_base'], (0, -2, 4.5), (44, -50, 38), 60),
        ('worldformer_operational', ['ccv02_worldformer_active'], (0, -2, 4.5), (44, -50, 38), 60),
    ]
    (OUT / 'previews').mkdir(parents=True, exist_ok=True)
    for stem, names, target, offset, scale in views:
        shown = [lookup[name] for name in names]
        if 'worldformer' in stem:
            shown.append(reference)
        for c in GROUPS:
            c.hide_render = c not in shown
            c.hide_viewport = False
        camera.location = Vector(target) + Vector(offset)
        camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = scale
        path = OUT / 'previews' / (stem + '.png')
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        previews.append(path.relative_to(ROOT).as_posix())
        print('CC_V02_RENDERED', stem, flush=True)
    # 默认展示传承炮击构型；其他构型/阶段和远景替代组保留但隐藏。
    default = [lookup[n] for n in views[0][1]]
    for c in GROUPS:
        c.hide_render = c not in default
        c.hide_viewport = c not in default
    camera.location = Vector(views[0][2]) + Vector(views[0][3])
    camera.rotation_euler = (Vector(views[0][2]) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = views[0][4]
    for image in bpy.data.images:
        if image.filepath.lower().endswith('.dds'):
            image.pack()
    assert len(bpy.data.libraries) == 0
    blend = OUT / 'central_court_surface_candidates_v02.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    # 重开一次核对真实落盘文件，不测试游戏或反复载档。
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    assert len(bpy.data.libraries) == 0
    for record in records:
        c = bpy.data.collections[record['part']]
        obj = next(o for o in c.objects if o.type == 'MESH')
        assert len(obj.data.polygons) == record['triangles']
        assert sorted(o['pdx_locator_name'] for o in c.objects if o.type == 'EMPTY') == record['locators']
    assert len([i for i in bpy.data.images if i.filepath.lower().endswith('.dds') and i.packed_file]) == 3
    manifest = {
        'date': '2026-11-01', 'source_base': '27c4b6a', 'status': 'draft_pending_human_review',
        'runtime_installed': False, 'formal_asset_approved': False, 'game_operated': False,
        'blender': bpy.app.version_string, 'source_blend': blend.relative_to(ROOT).as_posix(),
        'concept_reference': 'art/concepts/central_court_completion_preview_20261031/concept_board_v01.png',
        'concept_pixels_sampled': False, 'native_geometry_or_texture_reused': False,
        'palette_reference': 'docs/art/calibration/CENTRAL_COURT_MATERIAL_CALIBRATION.md',
        'mesh_count': len(records), 'base_part_count': len(bases), 'meshes': records, 'previews': previews,
        'uv_method': '8 material tiles / shared atlas / axis-projected faces / 5 percent inset',
        'unique_uv_bake': False, 'lod_method': 'independent 0.5 and 0.23 ratio decimation alternatives',
        'automatic_lod_switching': False, 'saved_file_reopened': True, 'packed_project_dds': 3,
        'external_blend_libraries': 0, 'user_live_scene_modified': False,
        'engine_scale_locators_particles_exposure': 'not_run',
        'planet_reference': 'self-created sphere, preview only, not exported; engine size/offset not calibrated',
        'unchanged': ['weapon_slots/components', 'ship/hub identity and acquisition', 'F08 mechanics/fees', 'all mod runtime paths'],
    }
    (OUT / 'model_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('CC_SURFACE_MODELS_V02_OK 7 base parts, 14 LOD alternatives, 4 previews, source reopened', flush=True)


if __name__ == '__main__':
    main()
