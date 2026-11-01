"""在独立后台精修v02结构/共享UV与材质；保留游戏中已验证的v02。"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_central_court_surface_v02 as base

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/models/central_court_surface_candidates_v03'
EXP = OUT / 'export'
PREVIEW = OUT / 'previews'
ORIGINAL_BOX = base.box
COUNTS = Counter()
PANELS = {'分层舰首装甲', '肩甲分区', '后段分层护板', '推进舱上护板',
          '横梁上护板', '作业台可替换护板', '控制枢纽分层甲板', '上方服务甲板'}


def metric_uv(obj, role, mat):
    """按尺寸取用材料格，细边只采样窄条；大面封顶，不承诺全模型等密度。"""
    index = base.pipeline.STYLES.index(role)
    uv = obj.data.uv_layers.active or obj.data.uv_layers.new(name='UVMap')
    seed = sum(ord(c) for c in obj.name)
    for face in obj.data.polygons:
        dominant = max(range(3), key=lambda i: abs(face.normal[i]))
        axes = [i for i in range(3) if i != dominant]
        points = [obj.data.vertices[obj.data.loops[k].vertex_index].co for k in face.loop_indices]
        low = [min(p[a] for p in points) for a in axes]
        spans = [max(p[a] for p in points) - low[j] for j, a in enumerate(axes)]
        extent = [.9 * min(s / 4.0, 1.0) for s in spans]
        shift = [((seed + j * 3) % 7) / 7 * (.9 - extent[j]) for j in range(2)]
        for loop in face.loop_indices:
            p = obj.data.vertices[obj.data.loops[loop].vertex_index].co
            u, v = [(p[a] - low[j]) / max(spans[j], .0001) * extent[j] + shift[j]
                    for j, a in enumerate(axes)]
            uv.data[loop].uv = ((index % 4 + .05 + u) / 4,
                                (1 - index // 4 + .05 + v) / 2)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.material_index = 0


def cut_plate(c, label, position, dimensions, role):
    width, length, height = dimensions
    cx, cy = min(.24, width * .15), min(.3, length * .12)
    points = [(-width / 2 + cx, -length / 2), (width / 2 - cx, -length / 2),
              (width / 2, -length / 2 + cy), (width / 2, length / 2 - cy),
              (width / 2 - cx, length / 2), (-width / 2 + cx, length / 2),
              (-width / 2, length / 2 - cy), (-width / 2, -length / 2 + cy)]
    obj = base.geometry.prism(c.name + '__' + label, points, -height / 2, height / 2, c, base.MAT)
    obj.location = position
    return base.style(obj, role)


def refined_box(c, label, position, dimensions, role='armor', rotation=(0, 0, 0), bevel=True):
    if label == '舰桥玻璃带':
        dimensions = (1.95, dimensions[1], dimensions[2])
    if label in {'舰桥控制层', '工程控制楼'}:
        COUNTS['matte_control_shells'] += 1
        return cut_plate(c, label + '_低反射外壳', position, dimensions, 'plate')
    if label == '中央庭识别护板':
        obj = cut_plate(c, label + '_深色底', position, dimensions, 'plate')
        ORIGINAL_BOX(c, '小型识别饰面', (position[0], position[1] - .5, position[2] + dimensions[2] / 2 + .02),
                     (.8, .24, .04), 'warm', bevel=False)
        return obj
    if label in PANELS and rotation == (0, 0, 0):
        width, length, height = dimensions
        x, y, z = position
        COUNTS['layered_cut_plates'] += 1
        # 下层承载唇与上层护板齐平到原高度，保留既有炮座和接口净空。
        cut_plate(c, label + '_承载唇', (x, y, z - height * .325), (width, length, height * .35), 'armor')
        if width >= 3.2:
            span = (width - .18) / 2
            for side in (-1, 1):
                cut_plate(c, label + '_分盖', (x + side * (span + .18) / 2, y, z + height * .175),
                          (span - .07, length - .1, height * .65), role)
            COUNTS['real_plate_gaps'] += 1
        else:
            cut_plate(c, label + '_上盖', (x, y, z + height * .175),
                      (width - .1, length - .1, height * .65), role)
        return next(o for o in reversed(list(c.objects)) if o.type == 'MESH')
    return ORIGINAL_BOX(c, label, position, dimensions, role, rotation, bevel)


def service_bank(c, x, y, z, length=3, width=1):
    """按真实场地分成推进散热、平台检修、舰面维护三种结构。"""
    cut_plate(c, '嵌入检修基座', (x, y, z), (width + .18, length + .14, .1), 'plate')
    ORIGINAL_BOX(c, '维护凹面', (x, y, z + .075), (width, length, .045), 'vent', bevel=False)
    if 'stern' in c.name:
        COUNTS['engine_cooling_banks'] += 1
        for offset in (-.3, 0, .3):
            base.cylinder(c, '轴向换热管', (x + offset * width, y, z + .15), .035, length * .82,
                          'silver' if offset == 0 else 'plate', (math.pi / 2, 0, 0), 8)
        for end in (-1, 1):
            ORIGINAL_BOX(c, '换热管固定箍', (x, y + end * length * .37, z + .15),
                         (width * .9, .1, .1), 'plate')
    elif 'worldformer' in c.name:
        COUNTS['platform_access_banks'] += 1
        for offset in (-.3, 0, .3):
            ORIGINAL_BOX(c, '检修盖横向筋', (x, y + offset * length, z + .12),
                         (width * .85, .075, .07), 'plate', bevel=False)
        ORIGINAL_BOX(c, '作业端检修锁', (x + width * .37, y - length * .3, z + .16),
                     (.08, .18, .05), 'amber', bevel=False)
    else:
        COUNTS['deck_access_banks'] += 1
        for side in (-1, 1):
            cut_plate(c, '成对检修分盖', (x + side * width * .24, y, z + .13),
                      (width * .43, length * .84, .08), 'plate')
        for end in (-1, 1):
            ORIGINAL_BOX(c, '小型检修铰链', (x, y + end * length * .38, z + .18),
                         (width * .4, .1, .06), 'silver', bevel=False)


def shared_specular_proxy(mat):
    """两版对照都使用同一预览通道解释，避免只给新版换灯光/着色逻辑。"""
    if not mat.use_nodes:
        return
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None or 'Specular IOR Level' not in bsdf.inputs:
        return
    prop = next((n for n in nodes if n.type == 'TEX_IMAGE' and n.image and 'properties' in n.image.filepath), None)
    if prop is None:
        return
    split = next((link.to_node for link in links if link.from_node == prop and link.to_node.type == 'SEPARATE_COLOR'), None)
    if split:
        links.new(split.outputs['Green'], bsdf.inputs['Specular IOR Level'])


def camera_view(scene, camera, target, offset, scale):
    camera.location = Vector(target) + Vector(offset)
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = scale
    scene.cycles.samples = 16


def render_baselines():
    source = ROOT / 'art/models/central_court_surface_candidates_v02/central_court_surface_candidates_v02.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source))
    for obj in list(bpy.data.objects):
        if obj.type in {'LIGHT', 'CAMERA'}:
            bpy.data.objects.remove(obj, do_unlink=True)
    for mat in bpy.data.materials:
        shared_specular_proxy(mat)
    scene, camera = base.render_setup()
    for stem, shown, target, offset, scale in (
        ('v02_ship_same_lighting', {'ccv02_bow_spinal', 'ccv02_mid_artillery', 'ccv02_stern'}, (0, -1, 0), (43, 59, 49), 77),
        ('v02_platform_same_lighting', {'ccv02_worldformer_active', '仅预览天体_不导出'}, (0, -2, 4.5), (44, -50, 38), 60),
    ):
        for collection in bpy.data.collections:
            collection.hide_render = collection.name not in shown
            collection.hide_viewport = False
        camera_view(scene, camera, target, offset, scale)
        scene.render.filepath = str(PREVIEW / (stem + '.png'))
        bpy.ops.render.render(write_still=True)
    # 仅渲染旧文件的内存副本；不保存回旧源文件。
    bpy.ops.wm.read_factory_settings(use_empty=True)


def definitions(records):
    gfx = ['# v03作者空间精修候选；需原生方向转换，未安装游戏。', 'objectTypes = {']
    for r in records:
        name = r['part']
        gfx += ['    pdxmesh = {', f'        name = "{name}_mesh"',
                f'        file = "gfx/models/central_court_surface_candidates_v03/{name}.mesh"', '        scale = 1.0']
        for index, shape in enumerate(r['shape_names']):
            gfx += ['        meshsettings = {', f'            name = "{shape}"', f'            index = {index}',
                    '            texture_diffuse = "cc_surface_v03_diffuse.dds"',
                    '            texture_normal = "cc_surface_v03_normal.dds"',
                    '            texture_specular = "cc_surface_v03_properties.dds"',
                    '            shader = "PdxMeshShip"', '        }']
        gfx += ['    }']
    gfx += ['}']
    (EXP / '_central_court_v03_meshes.gfx').write_text('\n'.join(gfx) + '\n', encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pdx-addon-root', required=True)
    args = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('仅独立后台factory-startup，禁止用户交互场景。')
    assert (OUT / 'surface_manifest.json').is_file(), '先准备v03纹理'
    PREVIEW.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, args.pdx_addon_root)
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    render_baselines()
    bpy.context.preferences.filepaths.save_version = 0
    base.GROUPS.clear()
    base.EXP = EXP
    base.pipeline.EXPORT, base.pipeline.ROOT = EXP, ROOT
    base.pipeline.map_style = metric_uv
    base.box, base.service_bank = refined_box, service_bank
    base.MAT = base.texture_material('cc_surface_v03')
    base.MAT.name = '中央庭共享图集v03_精修'
    shared_specular_proxy(base.MAT)
    bases = [base.bow(False), base.bow(True), base.middle(False), base.middle(True),
             base.stern(), base.platform(False), base.platform(True)]
    target_map = {}
    for collection in bases:
        old = collection.name
        collection.name = old.replace('ccv02_', 'ccv03_', 1)
        target_map[collection.name] = base.PARTS[old]
    records, retained = [], []
    for collection in bases:
        name = collection.name
        record = base.pipeline.export_group(collection, export_meshfile, read_meshfile)
        old_path = ROOT / ('art/models/central_court_surface_candidates_v02/export/' + name.replace('ccv03_', 'ccv02_', 1) + '.mesh')
        old_pdx = read_meshfile(str(old_path))
        new_pdx = read_meshfile(str(ROOT / record['mesh']))
        assert {n.tag: n.attrib for n in old_pdx.findall('./locator/*')} == {n.tag: n.attrib for n in new_pdx.findall('./locator/*')}, name
        obj = next(o for o in collection.objects if o.type == 'MESH')
        assert all(0 <= v <= 1 for loop in obj.data.uv_layers.active.data for v in loop.uv)
        record.update(lod=0, gameplay_target=target_map[name], locator_transforms_unchanged=True, uv_in_bounds=True)
        records.append(record)
        for level, ratio in ((1, .5), (2, .23)):
            reduced = base.simplified(collection, level, ratio)
            child = base.pipeline.export_group(reduced, export_meshfile, read_meshfile)
            child.update(lod=level, source_part=name, automatic_lod_switching=False)
            assert child['triangles'] < record['triangles'] and child['locators'] == record['locators']
            records.append(child)
        retained.append(name)
    definitions(records)
    reference = base.group('仅预览天体_不导出')
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=7.1, location=(0, 8.5, 9))
    planet = bpy.context.object
    base.geometry.add_to_group(planet, reference)
    mat = bpy.data.materials.new('天体参照_非游戏资源')
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value, bsdf.inputs['Roughness'].default_value = (.08, .13, .18, 1), .88
    planet.data.materials.append(mat)
    for face in planet.data.polygons:
        face.use_smooth = True
    scene, camera = base.render_setup()
    scene.name = '中央庭材质与结构精修候选v03'
    previews = []
    views = (
        ('ship_refined', {'ccv03_bow_spinal', 'ccv03_mid_artillery', 'ccv03_stern'}, (0, -1, 0), (43, 59, 49), 77),
        ('carrier_refined', {'ccv03_bow_standard', 'ccv03_mid_carrier', 'ccv03_stern'}, (0, -1, 0), (43, 59, 49), 77),
        ('platform_foundation_refined', {'ccv03_worldformer_base', reference.name}, (0, -2, 4.5), (44, -50, 38), 60),
        ('platform_operational_refined', {'ccv03_worldformer_active', reference.name}, (0, -2, 4.5), (44, -50, 38), 60),
    )
    for stem, shown, target, offset, scale in views:
        for collection in bpy.data.collections:
            collection.hide_render = collection.name not in shown
            collection.hide_viewport = False
        camera_view(scene, camera, target, offset, scale)
        scene.render.filepath = str(PREVIEW / (stem + '.png'))
        bpy.ops.render.render(write_still=True)
        previews.append((PREVIEW / (stem + '.png')).relative_to(ROOT).as_posix())
        print('CC_V03_RENDERED', stem, flush=True)
    shown = views[0][1]
    for collection in bpy.data.collections:
        collection.hide_render = collection.hide_viewport = collection.name not in shown
    camera_view(scene, camera, *views[0][2:])
    for image in bpy.data.images:
        if image.filepath.lower().endswith('.dds'):
            image.pack()
    assert len(bpy.data.libraries) == 0
    blend = OUT / 'central_court_surface_candidates_v03.blend'
    assert blend.resolve() != (ROOT / 'art/models/central_court_surface_candidates_v02/central_court_surface_candidates_v02.blend').resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    assert len(bpy.data.libraries) == 0
    for r in records:
        collection = bpy.data.collections[r['part']]
        obj = next(o for o in collection.objects if o.type == 'MESH')
        assert len(obj.data.polygons) == r['triangles']
        assert sorted(o['pdx_locator_name'] for o in collection.objects if o.type == 'EMPTY') == r['locators']
    assert len([i for i in bpy.data.images if i.filepath.lower().endswith('.dds') and i.packed_file]) == 3
    report = {'date': '2026-11-01', 'source_base': 'dfcc660', 'status': 'draft_pending_human_review',
              'runtime_installed': False, 'formal_asset_approved': False, 'game_operated': False,
              'source_blend': blend.relative_to(ROOT).as_posix(), 'blender': bpy.app.version_string,
              'meshes': records, 'base_parts': 7, 'mesh_count': len(records), 'refinement_counts': dict(COUNTS),
              'previews': previews, 'same_lighting_baselines': ['previews/v02_ship_same_lighting.png', 'previews/v02_platform_same_lighting.png'],
              'comparison': 'same CYCLES rig/camera/exposure, 16 samples, same Green specular proxy on both versions',
              'uv_method': '8 material tiles, face dimensions scaled to 4 author units and capped, 5 percent inset; not globally uniform density or unique bake',
              'locator_transforms_unchanged': True, 'saved_file_reopened': True, 'packed_project_dds': 3,
              'external_blend_libraries': 0, 'authoring_axes': '+Y forward/+Z up, needs native conversion before installation',
              'automatic_lod_switching': False, 'game_exposure_and_performance': 'not_run',
              'unchanged': ['v02 authoring/output files', 'all mod runtime resources', 'all gameplay/weapon slots/identity and acquisition', 'user live Blender scene']}
    (OUT / 'refinement_manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('CC_V03_REFINEMENT_OK 7 base parts, 14 LOD alternatives, 6 previews, locator transforms retained, source reopened', flush=True)


if __name__ == '__main__':
    main()
