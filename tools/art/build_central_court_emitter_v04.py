"""独立后台把传承舰首双长导轨改为分段场约束阵面；不写运行Mod。"""

import argparse
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_central_court_surface_v02 as base
import build_central_court_surface_v03 as refinement

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'art/models/central_court_surface_candidates_v03'
OUT = ROOT / 'art/models/central_court_spinal_emitter_v04'
EXP = OUT / 'export'


def remove_old_channel(mesh):
    """按断开几何的包围盒移除已知27个中轴导轨/节点/底脊，保留外侧舰体。"""
    neighbors = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        neighbors[a].append(b)
        neighbors[b].append(a)
    unseen, removed, components = set(range(len(mesh.vertices))), [], 0
    while unseen:
        start = unseen.pop()
        stack, group = [start], [start]
        while stack:
            vertex = stack.pop()
            for adjacent in neighbors[vertex]:
                if adjacent in unseen:
                    unseen.remove(adjacent)
                    group.append(adjacent)
                    stack.append(adjacent)
        points = [mesh.vertices[i].co for i in group]
        in_old_channel = (max(abs(p.x) for p in points) <= 1.2 and
                          min(p.y for p in points) >= 7.99 and
                          min(p.z for p in points) >= -1.0 and max(p.z for p in points) <= .5)
        if in_old_channel:
            components += 1
            removed.extend(group)
    assert components == 27, f'预期27个已知中轴几何组件，实际{components}，停止而非扩大删除区域'
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in removed], context='VERTS')
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return components


def build_field_array(collection):
    # 后部汇流座表现供能入口；开放工作段由短而宽、部分嵌入舰首的模块组织。
    refinement.cut_plate(collection, '后部汇流座', (0, 10.2, .58), (2.7, 2.1, .3), 'plate')
    base.box(collection, '汇流座工作面', (0, 11.29, .58), (1.7, .07, .18), 'cyan', bevel=False)
    stages = []
    for index, y in enumerate((12.8, 16.6, 20.4, 24.2), 1):
        opening = .88 + (y - 12) * .03
        # 横向支承位于发射轴以下；不以顶梁或连续长杆封住中央工作空腔。
        base.box(collection, '场约束下承载桥', (0, y, -.89), (2 * (opening + 1.45), 1.45, .18), 'armor')
        for side in (-1, 1):
            x = side * (opening + .76)
            base.loft(collection, '短宽约束模块', [(y - .65, .73, -.03, .43),
                      (y - .3, .85, .03, .52), (y + .43, .78, .03, .48),
                      (y + .67, .64, -.03, .38)], 'plate', x)
            refinement.cut_plate(collection, '约束单元上护板', (x, y, .57), (1.7, 1.38, .12), 'armor')
            base.box(collection, '向内场整形工作面', (side * (opening - .025), y, .02),
                     (.065, 1.02, .54), 'cyan', bevel=False)
            base.box(collection, '嵌入式接续座', (side * (opening + 1.35), y, -.22),
                     (.55, 1.1, .5), 'armor')
        name = 'cc_field_stage_0' + str(index)
        base.locator(collection, name, (0, y, -.08))
        # 这是设计开口值；实际护板/工作面会略侵入，不能当完整体积净空证明。
        stages.append({'index': index, 'author_y': y, 'visual_locator': name,
                       'nominal_opening_width': opening * 2, 'module_length': 1.32})
    # 宽而浅的定向发射阵面，不增加炮管；真实射击点仍位于其前方。
    refinement.cut_plate(collection, '发射阵面下基座', (0, 27.35, -.84), (4.5, 1.7, .3), 'armor')
    for side in (-1, 1):
        base.box(collection, '发射阵面侧支承', (side * 1.7, 27.48, -.31), (.34, .72, .9), 'plate')
    base.box(collection, '前向发射阵面', (0, 27.86, -.08), (2.82, .12, .44), 'cyan', bevel=False)
    base.box(collection, '阵面上护缘', (0, 27.53, .43), (3.8, .62, .15), 'plate')
    return stages


def graphics(records):
    lines = ['# v04作者空间舰首候选；沿v03材质，安装前须原生方向转换。', 'objectTypes = {']
    for r in records:
        name = r['part']
        lines += ['    pdxmesh = {', f'        name = "{name}_mesh"',
                  f'        file = "gfx/models/central_court_spinal_emitter_v04/{name}.mesh"', '        scale = 1.0']
        for index, shape in enumerate(r['shape_names']):
            lines += ['        meshsettings = {', f'            name = "{shape}"', f'            index = {index}',
                      '            texture_diffuse = "cc_surface_v03_diffuse.dds"',
                      '            texture_normal = "cc_surface_v03_normal.dds"',
                      '            texture_specular = "cc_surface_v03_properties.dds"',
                      '            shader = "PdxMeshShip"', '        }']
        lines += ['    }']
    lines += ['}']
    (EXP / '_central_court_emitter_v04.gfx').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdx-addon-root', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('仅独立后台factory-startup，禁止用户交互场景。')
    sys.path.insert(0, args.pdx_addon_root)
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    EXP.mkdir(parents=True, exist_ok=True)
    previews = OUT / 'previews'
    previews.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE / 'previews/ship_refined.png', previews / 'v03_reference.png')
    for suffix in ('diffuse', 'normal', 'properties'):
        name = 'cc_surface_v03_' + suffix + '.dds'
        shutil.copy2(SOURCE / 'export' / name, EXP / name)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE / 'central_court_surface_candidates_v03.blend'))
    bpy.context.preferences.filepaths.save_version = 0
    keep = {'ccv03_bow_spinal', 'ccv03_mid_artillery', 'ccv03_stern'}
    for collection in list(bpy.data.collections):
        if collection.name not in keep:
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)
        else:
            collection.hide_viewport = collection.hide_render = False
    bow = bpy.data.collections['ccv03_bow_spinal']
    bow.name = 'ccv04_bow_field'
    obj = next(o for o in bow.objects if o.type == 'MESH')
    base.MAT = obj.data.materials[0]
    base.pipeline.EXPORT, base.pipeline.ROOT = EXP, ROOT
    base.pipeline.map_style = refinement.metric_uv
    removed = remove_old_channel(obj.data)
    stages = build_field_array(bow)
    original = read_meshfile(str(SOURCE / 'export/ccv03_bow_spinal.mesh'))
    old_muzzle = next(n.attrib for n in original.findall('./locator/*') if n.tag == 'xl_gun_01')
    record = base.pipeline.export_group(bow, export_meshfile, read_meshfile)
    parsed = read_meshfile(str(ROOT / record['mesh']))
    new_muzzle = next(n.attrib for n in parsed.findall('./locator/*') if n.tag == 'xl_gun_01')
    assert new_muzzle == old_muzzle, '真实X槽发射点不能随静态外观修改漂移'
    assert len([n for n in parsed.findall('./locator/*') if n.tag.startswith('xl_gun_')]) == 1
    obj = next(o for o in bow.objects if o.type == 'MESH')
    axis_clear = not obj.ray_cast(Vector((0, 13, -.08)), Vector((0, 1, 0)), distance=13.0)[0]
    muzzle_clear = not obj.ray_cast(Vector((0, 28.5, -.08)), Vector((0, 1, 0)), distance=15.0)[0]
    assert axis_clear and muzzle_clear, '中央工作段和发射点前方须保持几何净空'
    records = [record]
    for level, ratio in ((1, .5), (2, .23)):
        lod = base.simplified(bow, level, ratio)
        child = base.pipeline.export_group(lod, export_meshfile, read_meshfile)
        child.update(lod=level, automatic_lod_switching=False)
        assert child['locators'] == record['locators'] and child['triangles'] < record['triangles']
        records.append(child)
    graphics(records)
    scene = bpy.context.scene
    scene.name = '分段场约束主炮_静态候选v04'
    camera = scene.camera
    shown = {bow.name, 'ccv03_mid_artillery', 'ccv03_stern'}
    for collection in bpy.data.collections:
        collection.hide_render = collection.name not in shown
        collection.hide_viewport = False
    images = []
    for stem, target, offset, scale in (
        ('ship_field_array', (0, -1, 0), (43, 59, 49), 77),
        ('field_array_closeup', (0, 20, 0), (18, 30, 22), 32),
    ):
        refinement.camera_view(scene, camera, target, offset, scale)
        scene.render.filepath = str(previews / (stem + '.png'))
        bpy.ops.render.render(write_still=True)
        images.append((previews / (stem + '.png')).relative_to(ROOT).as_posix())
    refinement.camera_view(scene, camera, (0, -1, 0), (43, 59, 49), 77)
    for collection in bpy.data.collections:
        collection.hide_render = collection.hide_viewport = collection.name not in shown
    bpy.data.orphans_purge(do_recursive=True)
    assert len(bpy.data.libraries) == 0
    for image in bpy.data.images:
        if image.filepath.lower().endswith('.dds'):
            image.pack()
    blend = OUT / 'central_court_spinal_emitter_v04.blend'
    assert blend.resolve() != (SOURCE / 'central_court_surface_candidates_v03.blend').resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    assert len(bpy.data.libraries) == 0
    for r in records:
        collection = bpy.data.collections[r['part']]
        mesh = next(o for o in collection.objects if o.type == 'MESH')
        assert len(mesh.data.polygons) == r['triangles']
        assert len(mesh.data.materials) == 1
        assert all(0 <= v <= 1 for loop in mesh.data.uv_layers.active.data for v in loop.uv)
        assert sorted(o['pdx_locator_name'] for o in collection.objects if o.type == 'EMPTY') == r['locators']
        r['uv_in_bounds'] = True
    assert len([i for i in bpy.data.images if i.filepath.lower().endswith('.dds') and i.packed_file]) == 3
    report = {'date': '2026-11-01', 'source_base': '4d4eeb3', 'status': 'draft_pending_human_review',
              'direction_confirmed_by_user': True, 'formal_asset_approved': False, 'runtime_installed': False,
              'design': 'one spinal emitter, four short wide field-shaping stages and one shallow forward emission plane',
              'removed_old_components': removed, 'stages': stages, 'meshes': records,
              'muzzle_locator': 'xl_gun_01', 'muzzle_transform_unchanged': True, 'actual_weapon_slots_changed': False,
              'reserved_visual_locators': [s['visual_locator'] for s in stages], 'charging_animation_implemented': False,
              'central_axis_geometry_clear': axis_clear, 'muzzle_forward_geometry_clear': muzzle_clear,
              'clearance_scope': 'two centreline rays only; not full beam-volume or runtime collision proof',
              'source_blend': blend.relative_to(ROOT).as_posix(), 'previews': images,
              'reference_preview': (previews / 'v03_reference.png').relative_to(ROOT).as_posix(),
              'full_ship_context': ['v03 mid artillery', 'v03 stern'], 'full_ship_context_exported': False,
              'textures': 'v03 shared DDS reused unchanged', 'saved_file_reopened': True, 'packed_dds': 3,
              'external_blend_libraries': 0, 'authoring_axes': '+Y forward/+Z up; native conversion required',
              'game_or_user_live_blender_operated': False, 'gameplay_and_mod_resources_changed': False,
              'automatic_lod_switching': False}
    (OUT / 'emitter_manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('CC_EMITTER_V04_OK four stages, one original muzzle, open axis, 3 PDX, source reopened', flush=True)


if __name__ == '__main__':
    main()
