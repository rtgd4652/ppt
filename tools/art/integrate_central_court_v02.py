"""独立后台将v02作者空间转为原生舰首方向，并安装可逆的开发候选资源。"""

import argparse
import json
import math
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_milestone4_surface as pipeline

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'art/models/central_court_surface_candidates_v02'
OUT = ROOT / 'art/models/central_court_runtime_v02'
EXPORT = OUT / 'export'
DEST = ROOT / 'mod/gfx/models/central_court_v02'
PARTS = ('bow_standard', 'bow_spinal', 'mid_artillery', 'mid_carrier', 'stern', 'worldformer_base', 'worldformer_active')


def graphics(records):
    gfx = ['# 中央庭v02开发候选；本文件接入不代表正式外观/发布许可批准。', 'objectTypes = {']
    for r in records:
        name = r['part']
        gfx += ['    pdxmesh = {', f'        name = "{name}_mesh"',
                f'        file = "gfx/models/central_court_v02/{name}.mesh"', '        scale = 1.0']
        for index, shape in enumerate(r['shape_names']):
            gfx += ['        meshsettings = {', f'            name = "{shape}"', f'            index = {index}',
                    '            texture_diffuse = "cc_surface_v02_diffuse.dds"',
                    '            texture_normal = "cc_surface_v02_normal.dds"',
                    '            texture_specular = "cc_surface_v02_properties.dds"',
                    '            shader = "PdxMeshShip"', '        }']
        gfx += ['    }']
    gfx += ['}']
    return '\n'.join(gfx) + '\n'


def entities():
    # 原版frame的target_locator_1..4为真实名字；同原点区段不使用原版分段骨架偏移。
    lines = ['# 公共中庭级独立开发根实体；旧个人舰/旧塔完全独立。',
             'entity = {', '    name = "ccv02_strategic_cruiser_entity"', '    scale = 0.75']
    for name in ('part1', 'part2', 'part3'):
        lines.append(f'    locator = {{ name = "{name}" position = {{ 0 0 0 }} }}')
    for i, z in enumerate((-24, -4, 8, 24), 1):
        lines.append(f'    locator = {{ name = "target_locator_{i}" position = {{ 0 0 {z} }} }}')
    lines += ['    default_state = "idle"', '    state = { name = "idle" state_time = 5 }',
              '    state = { name = "moving" state_time = 5 }',
              '    state = { name = "death" state_time = 5 looping = no',
              '        event = { time = 0 node = "part2" particle = "large_player_ship_explosion_particle" trigger_once = yes }',
              '    }', '    game_data = { size = 16 emissive_recolor_crunch = 5.0 }', '}']
    for part in PARTS:
        name = 'ccv02_runtime_' + part
        lines += ['entity = {', f'    name = "{name}_entity"', f'    pdxmesh = "{name}_mesh"',
                  '    default_state = "idle"']
        for state, particle in (('idle', 'generic_big_2_5_exhaust_circle_idle'), ('moving', 'generic_big_3_exhaust_circle_moving')):
            lines.append(f'    state = {{ name = "{state}" state_time = 5')
            if part == 'stern':
                for index in (1, 2):
                    lines.append(f'        event = {{ time = 0 node = "engine_large_0{index}" particle = "{particle}" keep_particle = yes trigger_once = yes }}')
            lines.append('    }')
        lines += ['    state = { name = "death" state_time = 5 looping = no }', '}']
    # 仅供实体显示检查的完整组合；不作为舰种/剧情入口，也不发放舰船。
    for key, bow, mid in (('spinal_artillery', 'bow_spinal', 'mid_artillery'),
                          ('standard_carrier', 'bow_standard', 'mid_carrier')):
        lines += ['entity = {', f'    name = "ccv02_preview_{key}_entity"',
                  '    clone = "ccv02_strategic_cruiser_entity"',
                  f'    attach = {{ part1 = "ccv02_runtime_{bow}_entity" }}',
                  f'    attach = {{ part2 = "ccv02_runtime_{mid}_entity" }}',
                  '    attach = { part3 = "ccv02_runtime_stern_entity" }', '}']
    return '\n'.join(lines) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pdx-addon-root', required=True)
    args = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('只允许独立后台factory-startup；禁止用户当前交互场景。')
    assert DEST.resolve().is_relative_to((ROOT / 'mod/gfx/models').resolve())
    assert json.loads((SOURCE / 'model_manifest.json').read_text(encoding='utf-8'))['saved_file_reopened']
    inspected = json.loads((ROOT / 'reports/central_court_engine_space_2026-11-01.json').read_text(encoding='utf-8'))
    native = {Path(x['file']).name: x for x in inspected}
    native_gun_q = native['mammalian_01_battleship_bow_XL1.mesh']['locators']['xl_gun_01']['q']
    native_engine_q = native['mammalian_01_battleship_stern_L1.mesh']['locators']['engine_medium_01']['q']
    sys.path.insert(0, args.pdx_addon_root)
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE / 'central_court_surface_candidates_v02.blend'))
    # 只转换导出副本所在后台内存；作者空间源文件不重新保存。
    EXPORT.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(parents=True, exist_ok=True)
    for suffix in ('diffuse', 'normal', 'properties'):
        filename = 'cc_surface_v02_' + suffix + '.dds'
        for target in (EXPORT, DEST):
            shutil.copy2(SOURCE / 'export' / filename, target / filename)
    pipeline.EXPORT, pipeline.ROOT = EXPORT, ROOT
    records = []
    for part in PARTS:
        collection = bpy.data.collections['ccv02_' + part]
        collection.hide_viewport = collection.hide_render = False
        if not part.startswith('worldformer'):
            for obj in collection.objects:
                if obj.type == 'MESH':
                    obj.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
                    obj.data.update()
                elif obj.type == 'EMPTY':
                    obj.location.x *= -1
                    obj.location.y *= -1
                    key = obj['pdx_locator_name']
                    if key.startswith('engine_'):
                        obj.rotation_euler = (0, 0, math.pi)
                    elif key.startswith('strike_craft_'):
                        obj.rotation_euler.z *= -1
                    else:
                        obj.rotation_euler = (0, 0, 0)
        collection.name = 'ccv02_runtime_' + part
        record = pipeline.export_group(collection, export_meshfile, read_meshfile)
        pdx = read_meshfile(str(ROOT / record['mesh']))
        # 与真实原版方向比较四元数，q和-q视作同一旋转，不只核对定位器名字。
        for loc in pdx.findall('./locator/*'):
            quat = loc.attrib['q']
            if 'gun_' in loc.tag:
                assert abs(sum(a * b for a, b in zip(quat, native_gun_q))) > .9999
            if loc.tag.startswith('engine_'):
                assert abs(sum(a * b for a, b in zip(quat, native_engine_q))) > .9999
            if loc.tag.startswith('strike_craft_'):
                direction = Quaternion((quat[3], quat[0], quat[1], quat[2])) @ Vector((0, 0, -1))
                assert direction.x * loc.attrib['p'][0] > 0, '机库方向必须朝舰体外侧'
        vertices = [v for mesh in pdx.findall('./object/*/mesh') for v in mesh.attrib['p'][2::3]]
        if part.startswith('bow'):
            assert max(vertices) < 0, '原版舰首应为PDX负Z'
        if part == 'stern':
            assert min(vertices) > 0, '舰尾应为PDX正Z'
        target = DEST / (record['part'] + '.mesh')
        shutil.copy2(ROOT / record['mesh'], target)
        record['mod_path'] = target.relative_to(ROOT).as_posix()
        record['orientation_checked_against_native'] = not part.startswith('worldformer')
        records.append(record)
    for filename, body in (('_central_court_v02_meshes.gfx', graphics(records)),
                           ('_central_court_v02_entities.asset', entities())):
        for target in (EXPORT, DEST):
            (target / filename).write_text(body, encoding='utf-8')
    result = {'date': '2026-11-01', 'source_base': '8e743e1', 'status': 'draft_integrated_runtime_pending',
              'formal_asset_approved': False, 'source_authoring_file_unchanged': True,
              'meshes': records, 'ship_root_entity': 'ccv02_strategic_cruiser_entity',
              'preview_entities': ['ccv02_preview_spinal_artillery_entity', 'ccv02_preview_standard_carrier_entity'],
              'native_forward_axis': 'PDX negative Z', 'ship_coordinate_conversion': 'Blender mesh/position rotate Z 180; gun identity; engines match native; hangars outward',
              'ship_root_scale': .75, 'megastructure_common_entity_offset': {'x': 0, 'y': -25},
              'lod_installed': 'LOD0 only; 14 authoring alternatives preserved offline',
              'automatic_lod_switching': False, 'root_assembly': 'part1/part2/part3 all zero, 4 native-name target locators',
              'game_display_verified': False, 'user_live_blender_scene_modified': False,
              'native_reference': 'reports/central_court_engine_space_2026-11-01.json'}
    (OUT / 'integration_manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('CC_V02_INTEGRATION_OK seven PDX, native axes/locators checked, candidate resources installed', flush=True)


if __name__ == '__main__':
    main()
