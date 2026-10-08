"""Blender后台生成独立灰模和PDX样品，不加载旧模型、不改运行资源或用户场景。"""

import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "art/models/milestone4_graybox"
EXPORT = OUTPUT / "export"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdx-addon-root", required=True, type=Path)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


def material(name, diffuse, tint):
    mat = bpy.data.materials.new(name)
    mat["shader"] = "PdxMeshShip"
    mat.diffuse_color = (*tint, 1)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    for socket, filename in (("Base Color", diffuse), ("Roughness", "gray_spec.dds")):
        node = nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(str(EXPORT / filename), check_existing=True)
        links.new(node.outputs["Color"], bsdf.inputs[socket])
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(EXPORT / "gray_normal.dds"), check_existing=True)
    normal = nodes.new("ShaderNodeNormalMap")
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def add_to_group(obj, group, mat=None):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    group.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj


def box(name, pos, size, group, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return add_to_group(obj, group, mat)


def prism(name, points, zmin, zmax, group, mat):
    count = len(points)
    vertices = [(x, y, z) for z in (zmin, zmax) for x, y in points]
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    faces += [(i, (i + 1) % count, (i + 1) % count + count, i + count) for i in range(count)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    group.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def locator(group, name, position, rotation=(0, 0, 0)):
    obj = bpy.data.objects.new(group.name + "__" + name, None)
    group.objects.link(obj)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.7
    obj.location, obj.rotation_euler = position, rotation
    obj["pdx_locator_name"] = name
    return obj


def prepare_and_export(group, export_meshfile, read_meshfile):
    meshes = [obj for obj in group.objects if obj.type == "MESH"]
    empties = [obj for obj in group.objects if obj.type == "EMPTY"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = obj.data.name = group.name
    obj.data["meshindex"] = 0
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    tri = obj.modifiers.new("灰模导出三角化", "TRIANGULATE")
    bpy.ops.object.modifier_apply(modifier=tri.name)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=0.025)
    bpy.ops.object.mode_set(mode="OBJECT")
    old_names = [(empty, empty.name) for empty in empties]
    for empty in empties:
        empty.name = empty["pdx_locator_name"]
        empty.select_set(True)
    destination = EXPORT / (group.name + ".mesh")
    try:
        export_meshfile(str(destination), exp_mesh=True, exp_skel=False, exp_locs=True, exp_selected=True)
        parsed = read_meshfile(str(destination))
    finally:
        for empty, name in old_names:
            empty.name = name
    materials = [node.attrib for node in parsed.findall("./object/*/mesh/material")]
    for data in materials:
        for key in ("diff", "spec", "n"):
            for texture in data.get(key, []):
                if not (EXPORT / texture).is_file():
                    raise ValueError(f"导出材质引用缺失：{texture}")
    exported_locators = sorted(node.tag for node in parsed.findall("./locator/*"))
    expected = sorted(empty["pdx_locator_name"] for empty in empties)
    if exported_locators != expected:
        raise ValueError(f"定位器往返不一致：{group.name}")
    return {"part": group.name, "triangles": len(obj.data.polygons),
            "locators": exported_locators, "materials": len(materials),
            "mesh": destination.relative_to(ROOT).as_posix(), "pdx_readback": "passed"}


def render_views(groups):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x, scene.render.resolution_y = 640, 420
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.background_type = "WORLD"
    scene.world.color = (0.04, 0.05, 0.07)
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = "灰模检查相机"
    camera.data.type = "ORTHO"
    scene.camera = camera
    renders = []
    for label, visible, scale in (
        ("flagship", groups[:3], 48), ("hub_base", [groups[3]], 30), ("hub_active", [groups[4]], 30)
    ):
        for group in groups:
            group.hide_render = group not in visible
        for view, position in (("top", (0, 0, 70)), ("side", (65, 0, 0)), ("oblique", (44, -52, 46))):
            camera.location = position
            direction = Vector((0, 0, 0)) - camera.location
            camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
            # 正俯视必须按画面高度容纳纵向舰体及四臂，避免切掉前后端。
            camera.data.ortho_scale = (64 if label == "flagship" else 40) if view == "top" else scale
            destination = OUTPUT / "previews" / f"{label}_{view}.png"
            scene.render.filepath = str(destination)
            bpy.ops.render.render(write_still=True)
            renders.append(destination.relative_to(ROOT).as_posix())
    # 源文件默认显示旗舰；两阶段枢纽分别在独立集合，绝不改动用户已打开的场景。
    for group in groups:
        group.hide_render = False
        group.hide_viewport = group not in groups[:3]
    return renders


def main():
    args = parse_args()
    sys.path.insert(0, str(args.pdx_addon_root))
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile

    EXPORT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "previews").mkdir(exist_ok=True)
    # 本脚本只在 --background --factory-startup 的新进程运行。
    if not bpy.app.background:
        raise RuntimeError("灰模构建必须运行在隔离后台进程。")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    dark = material("承力深灰", "gray_dark.dds", (0.18, 0.23, 0.28))
    silver = material("雾银承力边", "gray_silver.dds", (0.52, 0.57, 0.61))
    plate = material("分舱蓝灰", "gray_plate.dds", (0.29, 0.36, 0.41))
    groups = [bpy.data.collections.new(name) for name in (
        "reality_flagship_bow_gray", "reality_flagship_mid_gray", "reality_flagship_stern_gray",
        "reality_baseline_base_gray", "reality_baseline_active_gray"
    )]
    for group in groups:
        bpy.context.scene.collection.children.link(group)
    bow, mid, stern = groups[:3]
    prism("钝楔舰首", [(-4, 6), (4, 6), (4.5, 11), (2, 20), (-2, 20), (-4.5, 11)], -1, 1.5, bow, dark)
    box("舰首承力脊柱", (0, 11, 1.7), (2.4, 9, 0.8), bow, silver)
    for x in (-2.7, 2.7):
        box("舰首分层装甲", (x, 9.3, 1.6), (2.2, 5.5, 0.4), bow, plate)
    box("中段舰体", (0, -0.5, 0), (8, 13, 2), mid, dark)
    for x in (-4.25, 4.25):
        box("中段防护外框", (x, -0.5, 0.3), (0.7, 12, 2.6), mid, silver)
    box("有限恒定模块", (0, -0.5, 2.0), (3.4, 5, 2), mid, plate)
    box("低矮指挥舱", (0, 3.8, 1.8), (3, 2.4, 1.6), mid, silver)
    box("舰艉承力体", (0, -13, 0), (8, 12, 2), stern, dark)
    for x in (-2.4, 2.4):
        box("推进舱", (x, -15.3, -0.2), (2.8, 8, 2.5), stern, plate)
        box("散热装甲", (x, -10.3, 1.4), (2.2, 4.5, 0.5), stern, silver)
    for i, position in enumerate(((-2, 11, 2.4), (2, 11, 2.4)), 1):
        locator(bow, f"large_gun_{i:02d}", position)
    for i, position in enumerate(((-2.7, 2, 2), (2.7, 2, 2), (0, -4.2, 3.1)), 1):
        locator(mid, f"large_gun_{i:02d}", position)
    locator(stern, "large_gun_01", (0, -8.7, 1.9))
    for i, x in enumerate((-2.4, 2.4), 1):
        locator(stern, f"engine_large_{i:02d}", (x, -19.4, -0.2), (math.pi / 2, 0, 0))
    for stage, group in enumerate(groups[3:]):
        # 两阶段共用相同基座、中心、四向支臂和固定模块接口。
        outline = [(4 * math.cos(i * math.pi / 4), 4 * math.sin(i * math.pi / 4)) for i in range(8)]
        prism("共同中枢基座", outline, -0.7, 0.7, group, dark)
        for axis in range(2):
            for sign in (-1, 1):
                p = (sign * 6.8, 0, 0) if axis == 0 else (0, sign * 6.8, 0)
                size = (9, 1.3, 0.6) if axis == 0 else (1.3, 9, 0.6)
                box("固定支臂", p, size, group, silver)
                end = (sign * 10, 0, 0.45) if axis == 0 else (0, sign * 10, 0.45)
                box("维护平台", end, (3.2, 3.2, 0.9), group, plate)
                if stage:
                    box("屏蔽分析舱", (end[0], end[1], 1.65), (2.5, 2.5, 1.5), group, dark)
        if stage:
            box("运行中枢资料舱", (0, 0, 2), (4.5, 4.5, 2.5), group, plate)
        locator(group, "hub_center", (0, 0, 0))
    records = [prepare_and_export(group, export_meshfile, read_meshfile) for group in groups]
    renders = render_views(groups)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "reality_assets_graybox_v01.blend"))
    report = {"status": "draft_pending_human_review", "blender": bpy.app.version_string,
              "runtime_installed": False, "legacy_geometry_used": False,
              "axis": "Blender +Y前/+Z上，经现有PDX插件转换", "ship_length": 39.3,
              "root_part_locators": {name: [0, 0, 0] for name in ("part1", "part2", "part3")},
              "hub_shared_layout": {"center": [0, 0, 0], "arm_module_centers": [[-10, 0], [10, 0], [0, -10], [0, 10]]},
              "meshes": records, "previews": renders,
              "limits": ["仅灰模、定位器及文件导出往返，不代表正式材质或游戏显示", "武器朝向、整舰比例和根实体挂接需正式接入时检查"]}
    (OUTPUT / "graybox_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("M4_GRAYBOX_OK=" + json.dumps({"blender": report["blender"], "meshes": len(records), "previews": len(renders)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
