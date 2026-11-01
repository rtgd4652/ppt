"""独立后台合并v03整体精修与v04场约束舰首，沿已验证原生变换安装开发候选。"""

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
import build_milestone4_graybox as geometry
import integrate_central_court_v02 as prior

ROOT = Path(__file__).resolve().parents[2]
SURFACE = ROOT / 'art/models/central_court_surface_candidates_v03'
BOW = ROOT / 'art/models/central_court_spinal_emitter_v04'
OUT = ROOT / 'art/models/central_court_runtime_v04'
EXPORT = OUT / 'export'
DEST = ROOT / 'mod/gfx/models/central_court_v04'


def export_part(part, collection, export_meshfile, read_meshfile, native):
    """与v02同一变换；新增场约束点随位置翻转，不改变唯一主炮接口。"""
    collection.hide_viewport = collection.hide_render = False
    if part == 'bow_spinal':
        # 原版tachyon_lance_windup_entity按8/7→6/5→4/3→2/1分四段。
        # 只新增粒子兼容挂点；既有cc_field_stage与xl_gun_01均保持，绝非八门炮。
        for index, y in enumerate((12.8, 16.6, 20.4, 24.2)):
            opening = .88 + (y - 12) * .03
            for side, number in ((-1, 8 - index * 2), (1, 7 - index * 2)):
                geometry.locator(collection, f'xl_windup_{number}', (side * (opening - .025), y, .02))
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
    collection.name = 'ccv04_runtime_' + part
    record = pipeline.export_group(collection, export_meshfile, read_meshfile)
    obj = next(o for o in collection.objects if o.type == 'MESH')
    assert all(0 <= v <= 1 for loop in obj.data.uv_layers.active.data for v in loop.uv)
    pdx = read_meshfile(str(ROOT / record['mesh']))
    for loc in pdx.findall('./locator/*'):
        quat = loc.attrib['q']
        if 'gun_' in loc.tag:
            assert abs(sum(a * b for a, b in zip(quat, native['gun']))) > .9999
        if loc.tag.startswith('engine_'):
            assert abs(sum(a * b for a, b in zip(quat, native['engine']))) > .9999
        if loc.tag.startswith('strike_craft_'):
            direction = Quaternion((quat[3], quat[0], quat[1], quat[2])) @ Vector((0, 0, -1))
            assert direction.x * loc.attrib['p'][0] > 0
    vertices = [v for mesh in pdx.findall('./object/*/mesh') for v in mesh.attrib['p'][2::3]]
    if part.startswith('bow'):
        assert max(vertices) < 0, '舰首须沿原生PDX负Z'
    if part == 'stern':
        assert min(vertices) > 0, '舰尾须沿原生PDX正Z'
    if part == 'bow_spinal':
        locs = {n.tag: n.attrib for n in pdx.findall('./locator/*')}
        old = read_meshfile(str(ROOT / 'mod/gfx/models/central_court_v02/ccv02_runtime_bow_spinal.mesh'))
        assert locs['xl_gun_01'] == next(n.attrib for n in old.findall('./locator/*') if n.tag == 'xl_gun_01')
        assert len([key for key in locs if key.startswith('xl_gun_')]) == 1
        for index, y in enumerate((12.8, 16.6, 20.4, 24.2), 1):
            assert abs(locs[f'cc_field_stage_0{index}']['p'][2] + y) < .0001
            assert abs(locs[f'xl_windup_{10 - index * 2}']['p'][2] + y) < .0001
            assert abs(locs[f'xl_windup_{9 - index * 2}']['p'][2] + y) < .0001
    record.update(uv_in_bounds=True, orientation_checked_against_native=not part.startswith('worldformer'),
                  source_generation='v04' if part == 'bow_spinal' else 'v03',
                  mod_path=(DEST / (record['part'] + '.mesh')).relative_to(ROOT).as_posix())
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdx-addon-root', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('只允许独立后台factory-startup，禁止用户当前交互场景。')
    assert DEST.resolve().is_relative_to((ROOT / 'mod/gfx/models').resolve())
    for path in (SURFACE / 'refinement_manifest.json', BOW / 'emitter_manifest.json'):
        assert json.loads(path.read_text(encoding='utf-8'))['saved_file_reopened']
    inspected = json.loads((ROOT / 'reports/central_court_engine_space_2026-11-01.json').read_text(encoding='utf-8'))
    by_file = {Path(item['file']).name: item for item in inspected}
    native = {'gun': by_file['mammalian_01_battleship_bow_XL1.mesh']['locators']['xl_gun_01']['q'],
              'engine': by_file['mammalian_01_battleship_stern_L1.mesh']['locators']['engine_medium_01']['q']}
    sys.path.insert(0, args.pdx_addon_root)
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    EXPORT.mkdir(parents=True, exist_ok=True)
    for suffix in ('diffuse', 'normal', 'properties'):
        name = 'cc_surface_v03_' + suffix + '.dds'
        shutil.copy2(SURFACE / 'export' / name, EXPORT / name)
    pipeline.EXPORT, pipeline.ROOT = EXPORT, ROOT
    records = []
    # 两份源文件分别只读打开；不把v04整舰预览里的中/尾段再次导出或修改原源文件。
    bpy.ops.wm.open_mainfile(filepath=str(SURFACE / 'central_court_surface_candidates_v03.blend'))
    for part in prior.PARTS:
        if part != 'bow_spinal':
            records.append(export_part(part, bpy.data.collections['ccv03_' + part], export_meshfile, read_meshfile, native))
    bpy.ops.wm.open_mainfile(filepath=str(BOW / 'central_court_spinal_emitter_v04.blend'))
    records.append(export_part('bow_spinal', bpy.data.collections['ccv04_bow_field'], export_meshfile, read_meshfile, native))
    records.sort(key=lambda r: prior.PARTS.index(r['part'].removeprefix('ccv04_runtime_')))
    gfx = prior.graphics(records).replace('中央庭v02', '中央庭v04').replace('central_court_v02/', 'central_court_v04/').replace('cc_surface_v02_', 'cc_surface_v03_')
    entity = prior.entities().replace('ccv02_', 'ccv04_')
    (EXPORT / '_central_court_v04_meshes.gfx').write_text(gfx, encoding='utf-8')
    (EXPORT / '_central_court_v04_entities.asset').write_text(entity, encoding='utf-8')
    # 七网格全部导出/回读成功后再写独立运行目录；旧v02保留，不覆盖兼容资源。
    DEST.mkdir(parents=True, exist_ok=True)
    for source in EXPORT.iterdir():
        if source.is_file():
            shutil.copy2(source, DEST / source.name)
    result = {'date': '2026-11-01', 'source_base': 'ea9b5f6', 'status': 'draft_integrated_runtime_pending',
              'formal_asset_approved': False, 'source_authoring_files_unchanged': True,
              'meshes': records, 'ship_root_entity': 'ccv04_strategic_cruiser_entity',
              'preview_entities': ['ccv04_preview_spinal_artillery_entity', 'ccv04_preview_standard_carrier_entity'],
              'ship_root_scale': .75, 'native_forward_axis': 'PDX negative Z',
              'native_transform': 'same as validated v02: ship author Z180, gun identity, native engines, outward hangars',
              'root_assembly': 'same as v02; zero part1/2/3 and four native target locators',
              'spinal_muzzle_identical_to_installed_v02': True,
              'custom_charging_animation_implemented': False, 'automatic_lod_switching': False,
              'native_windup_locators_installed': ['xl_windup_' + str(i) for i in range(1, 9)],
              'native_windup_sequence': 'existing tachyon_lance: 8/7 at 0s, 6/5 at 0.2s, 4/3 at 0.4s, 2/1 at 0.6s',
              'native_windup_runtime_observed': False,
              'game_display_verified': False, 'user_live_blender_scene_modified': False,
              'megastructure_entity_offset': {'x': 0, 'y': -25},
              'old_v02_resources_preserved': True,
              'source_files': ['art/models/central_court_surface_candidates_v03/central_court_surface_candidates_v03.blend',
                               'art/models/central_court_spinal_emitter_v04/central_court_spinal_emitter_v04.blend']}
    (OUT / 'integration_manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('CC_V04_INTEGRATION_OK six v03 parts and v04 bow, seven PDX, native axes and single muzzle verified', flush=True)


if __name__ == '__main__':
    main()
