"""在隔离Blender进程细化本项目新灰模，导出带材质的模型草案和实体样品。"""

import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_milestone4_graybox as geometry

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "art/models/milestone4_surface_v02"
EXPORT = OUTPUT / "export"
STYLES = ("armor", "plate", "silver", "warm", "glass", "vent", "cyan", "amber")


def texture_material():
    mat = bpy.data.materials.new("中央庭公共材质样品v02")
    mat["shader"] = "PdxMeshShip"
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    diffuse, prop, normal = [nodes.new("ShaderNodeTexImage") for _ in range(3)]
    for node, suffix in ((diffuse, "diffuse"), (prop, "properties"), (normal, "normal")):
        # 离线预览直接读取运行格式DDS；PNG保留为可编辑的生成源。
        node.image = bpy.data.images.load(str(EXPORT / f"reality_surface_{suffix}.dds"), check_existing=True)
        node.interpolation = "Linear"
        if suffix != "diffuse":
            node.image.colorspace_settings.name = "Non-Color"
    links.new(diffuse.outputs["Color"], bsdf.inputs["Base Color"])
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(prop.outputs["Color"], split.inputs["Color"])
    links.new(split.outputs["Blue"], bsdf.inputs["Metallic"])
    rough = nodes.new("ShaderNodeMath")
    rough.operation = "SUBTRACT"
    rough.inputs[0].default_value = 1
    links.new(prop.outputs["Alpha"], rough.inputs[1])
    links.new(rough.outputs[0], bsdf.inputs["Roughness"])
    # 解包Stellaris法线供Blender预览；导出器沿连接读取原始压缩图。
    separate = nodes.new("ShaderNodeSeparateColor")
    links.new(normal.outputs["Color"], separate.inputs["Color"])
    combine = nodes.new("ShaderNodeCombineColor")
    combine.inputs["Blue"].default_value = 1
    links.new(separate.outputs["Green"], combine.inputs["Red"])
    flip = nodes.new("ShaderNodeMath")
    flip.operation = "SUBTRACT"
    flip.inputs[0].default_value = 1
    links.new(normal.outputs["Alpha"], flip.inputs[1])
    links.new(flip.outputs[0], combine.inputs["Green"])
    nm = nodes.new("ShaderNodeNormalMap")
    links.new(combine.outputs[0], nm.inputs["Color"])
    links.new(nm.outputs[0], bsdf.inputs["Normal"])
    links.new(diffuse.outputs["Color"], bsdf.inputs["Emission Color"])
    links.new(separate.outputs["Blue"], bsdf.inputs["Emission Strength"])
    return mat


def map_style(obj, style, mat):
    # 每个独立面按主轴投影到指定材料格；限制边界采样，避免UV落入邻格。
    index = STYLES.index(style)
    uv = obj.data.uv_layers.active or obj.data.uv_layers.new(name="UVMap")
    for face in obj.data.polygons:
        axes = [i for i in range(3) if i != max(range(3), key=lambda i: abs(face.normal[i]))]
        points = [obj.data.vertices[obj.data.loops[i].vertex_index].co for i in face.loop_indices]
        low = [min(point[axis] for point in points) for axis in axes]
        span = [max(point[axis] for point in points) - low[j] for j, axis in enumerate(axes)]
        for loop in face.loop_indices:
            point = obj.data.vertices[obj.data.loops[loop].vertex_index].co
            u, v = [(point[axis] - low[j]) / max(span[j], 0.0001) for j, axis in enumerate(axes)]
            uv.data[loop].uv = ((index % 4 + 0.05 + 0.9 * u) / 4,
                                (1 - index // 4 + 0.05 + 0.9 * v) / 2)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.material_index = 0


def detail(name, position, size, group, style, mat, bevel=True):
    obj = geometry.box(name, position, size, group, mat)
    if bevel and min(size) > 0.18:
        modifier = obj.modifiers.new("工程边倒角", "BEVEL")
        modifier.width = min(min(size) * 0.16, 0.12)
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    map_style(obj, style, mat)
    return obj


def export_group(group, export_meshfile, read_meshfile):
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
    modifier = obj.modifiers.new("运行网格三角化", "TRIANGULATE")
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    names = [(empty, empty.name) for empty in empties]
    for empty in empties:
        empty.name = empty["pdx_locator_name"]
        empty.select_set(True)
    path = EXPORT / (group.name + ".mesh")
    try:
        export_meshfile(str(path), exp_mesh=True, exp_skel=False, exp_locs=True, exp_selected=True)
        parsed = read_meshfile(str(path))
    finally:
        for empty, name in names:
            empty.name = name
    locators = sorted(node.tag for node in parsed.findall("./locator/*"))
    assert locators == sorted(empty["pdx_locator_name"] for empty in empties)
    materials = [node.attrib for node in parsed.findall("./object/*/mesh/material")]
    for material in materials:
        for key in ("diff", "spec", "n"):
            assert len(material.get(key, [])) == 1
            assert (EXPORT / material[key][0]).is_file()
    # 读取实际导出的子网格名称，不猜测meshsettings名称。
    shapes = [node.tag for node in parsed.findall("./object/*")]
    return {"part": group.name, "triangles": len(obj.data.polygons), "locators": locators,
            "mesh": path.relative_to(ROOT).as_posix(), "shape_names": shapes,
            "material_count": len(materials), "pdx_readback": "pass"}


def definitions(records):
    gfx = ["# 带材质草案的PDX注册；安装时复制同目录DDS及网格。", "objectTypes = {"]
    for record in records:
        name = record["part"]
        gfx.extend(["    pdxmesh = {", f'        name = "{name}_mesh"',
                    f'        file = "gfx/models/milestone4_surface_v02/{name}.mesh"',
                    "        scale = 1.0"])
        for index, shape in enumerate(record["shape_names"]):
            gfx.extend(["        meshsettings = {", f'            name = "{shape}"',
                        f"            index = {index}", '            texture_diffuse = "reality_surface_diffuse.dds"',
                        '            texture_normal = "reality_surface_normal.dds"',
                        '            texture_specular = "reality_surface_properties.dds"',
                        '            shader = "PdxMeshShip"', "        }"])
        gfx.append("    }")
    gfx.append("}")
    (EXPORT / "_reality_surface_meshes.gfx").write_text("\n".join(gfx) + "\n", encoding="utf-8")
    entities = ['# 本文件是待安装样品；不引用旧舰旧塔。', 'entity = {',
                '    name = "aemusa_reality_flagship_entity"']
    for part in ("part1", "part2", "part3"):
        entities.append(f"    locator = {{ name = {part} position = {{ 0 0 0 }} }}")
    # 本机原版战列舰使用target_locator_1～4，不使用零填充编号。
    for index, (x, y, z) in enumerate(((0, 0, 11), (-3, 0, 0), (3, 0, 0), (0, 0, -13)), 1):
        entities.append(f"    locator = {{ name = target_locator_{index} position = {{ {x} {y} {z} }} }}")
    entities.extend(['    default_state = "idle"', '    state = { name = "idle" state_time = 5 }',
                     '    state = { name = "moving" state_time = 5 }',
                     '    state = { name = "death" state_time = 5 looping = no }', '}'])
    for record in records:
        name = record["part"]
        entities.extend(['entity = {', f'    name = "{name}_entity"', f'    pdxmesh = "{name}_mesh"',
                         '    default_state = "idle"', '    state = { name = "idle" state_time = 5 }',
                         '    state = { name = "moving" state_time = 5 }',
                         '    state = { name = "death" state_time = 5 looping = no }', '}'])
    (EXPORT / "_reality_surface_entities.asset").write_text("\n".join(entities) + "\n", encoding="utf-8")


def render(groups):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 800, 520
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.08, 0.10, 0.13, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.55
    for position, power, size in (((15, 12, 30), 24000, 20), ((-20, -12, 12), 15000, 20)):
        bpy.ops.object.light_add(type="AREA", location=position)
        light = bpy.context.object
        light.data.energy, light.data.shape, light.data.size = power, "DISK", size
        light.rotation_euler = (-light.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.camera_add(location=(44, -52, 46))
    camera = bpy.context.object
    camera.name = "材质样品检查相机"
    camera.data.type = "ORTHO"
    camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    frames = []
    for label, shown, scale in (("flagship", groups[:3], 48), ("hub_base", [groups[3]], 30),
                                ("hub_active", [groups[4]], 30)):
        for group in groups:
            group.hide_render = group not in shown
            group.hide_viewport = False
        camera.data.ortho_scale = scale
        path = OUTPUT / "previews" / (label + "_surface.png")
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        frames.append(path.relative_to(ROOT).as_posix())
    for group in groups:
        group.hide_render = False
        group.hide_viewport = group not in groups[:3]
    return frames


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdx-addon-root", required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if not bpy.app.background:
        raise RuntimeError("仅允许隔离后台构建。")
    sys.path.insert(0, str(args.pdx_addon_root))
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile

    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "art/models/milestone4_graybox/reality_assets_graybox_v01.blend"))
    # 清理旧检查相机，源灰模和用户交互场景都不写回。
    for obj in list(bpy.data.objects):
        if obj.type in ("CAMERA", "LIGHT"):
            bpy.data.objects.remove(obj, do_unlink=True)
    groups = [bpy.data.collections[name] for name in (
        "reality_flagship_bow_gray", "reality_flagship_mid_gray", "reality_flagship_stern_gray",
        "reality_baseline_base_gray", "reality_baseline_active_gray")]
    mat = texture_material()
    for group in groups:
        group.name = group.name.removesuffix("_gray")
        group.hide_viewport = False
        group.hide_render = False
        for obj in [obj for obj in group.objects if obj.type == "MESH"]:
            # 灰模三个材料按职责映射；保留原UV，再缩入各自图集格。
            mapping = {0: 0, 1: 2, 2: 1}
            uv = obj.data.uv_layers.active
            for face in obj.data.polygons:
                style = mapping.get(face.material_index, 0)
                for loop in face.loop_indices:
                    u, v = uv.data[loop].uv
                    uv.data[loop].uv = ((style % 4 + 0.05 + 0.9 * u) / 4,
                                        (1 - style // 4 + 0.05 + 0.9 * v) / 2)
                face.material_index = 0
            obj.data.materials.clear()
            obj.data.materials.append(mat)
    bow, mid, stern, base, active = groups
    for sign in (-1, 1):
        for y in (7.5, 10, 12.5):
            detail("可更换舰首装甲", (sign * 3.1, y, 1.95), (1.5, 1.9, 0.35), bow, "plate", mat)
        detail("舰首观测窗", (sign * 0.95, 17, 1.7), (0.55, 1.3, 0.12), bow, "glass", mat, False)
        detail("舰首低亮航行灯", (sign * 1.9, 18.5, 1.56), (0.2, 0.55, 0.06), bow, "cyan", mat, False)
        for y in (-4, -1, 2):
            detail("中段分舱覆盖", (sign * 2.4, y, 1.25), (1.8, 2.2, 0.35), mid, "plate", mat)
        detail("恒定模块外框", (sign * 1.85, -0.5, 2.8), (0.35, 5.8, 0.45), mid, "silver", mat)
        detail("低亮恒定状态线", (sign * 1.4, -0.5, 3.06), (0.12, 3.8, 0.08), mid, "cyan", mat, False)
        detail("舰桥观察窗", (sign * 0.75, 4.5, 2.62), (0.95, 0.75, 0.09), mid, "glass", mat, False)
        for y in (-17, -14, -11):
            detail("供能舱分层盖板", (sign * 2.4, y, 1.15), (2.5, 2, 0.35), stern, "plate", mat)
        detail("散热格栅", (sign * 2.4, -11, 1.7), (1.8, 3.1, 0.12), stern, "vent", mat, False)
        detail("推进端雾银护套", (sign * 2.4, -19.25, -0.2), (3.05, 0.6, 2.8), stern, "silver", mat)
        detail("推进喷口", (sign * 2.4, -19.6, -0.2), (2.1, 0.08, 1.6), stern, "cyan", mat, False)
        detail("舰桥人居小灯", (sign * 1.48, 3.8, 2.35), (0.07, 0.45, 0.12), mid, "amber", mat, False)
    detail("模块维护盖板", (0, -0.5, 3.08), (2.2, 3.1, 0.15), mid, "armor", mat, False)
    detail("舰艉中央承力脊柱", (0, -13, 1.15), (1.4, 9, 0.6), stern, "silver", mat)
    for stage, group in enumerate((base, active)):
        for x, y in ((-10, 0), (10, 0), (0, -10), (0, 10)):
            detail("维护接口外圈", (x, y, 0.99), (2.8, 2.8, 0.2), group, "silver", mat, False)
            detail("工程维护口", (x + 0.55, y, 1.11), (0.7, 1, 0.06), group, "warm", mat, False)
            if stage:
                detail("分析舱低亮状态线", (x, y - 1.27, 2.0), (1.6, 0.08, 0.12), group, "cyan", mat, False)
                detail("分析舱顶部防护", (x, y, 2.46), (1.8, 1.8, 0.15), group, "plate", mat, False)
            else:
                detail("待装设备框", (x, y, 1.08), (1.6, 1.6, 0.12), group, "vent", mat, False)
            detail("维护平台有人作业灯", (x + 1.25, y + 1.25, 1.12), (0.18, 0.18, 0.08), group, "amber", mat, False)
        for sign in (-1, 1):
            detail("维护运输轨", (sign * 6.2, 0, 0.4), (4.7, 0.3, 0.08), group, "plate", mat, False)
            detail("维护运输轨", (0, sign * 6.2, 0.4), (0.3, 4.7, 0.08), group, "plate", mat, False)
        if stage:
            detail("中枢资料舱雾银上框", (0, 0, 3.29), (4.6, 4.6, 0.24), group, "silver", mat)
            detail("中枢受控解析窗", (0, 0, 3.45), (2.8, 2.8, 0.12), group, "glass", mat, False)
        geometry.locator(group, "build_point", (0, 0, 0))
    (OUTPUT / "previews").mkdir(parents=True, exist_ok=True)
    for empty in [obj for obj in stern.objects if obj.type == "EMPTY" and obj["pdx_locator_name"].startswith("engine_")]:
        empty.location.y = -19.65
    records = [export_group(group, export_meshfile, read_meshfile) for group in groups]
    definitions(records)
    frames = render(groups)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "reality_assets_surface_v02.blend"))
    report = {"status": "draft_pending_human_review", "runtime_installed": False,
              "blender": bpy.app.version_string, "legacy_geometry_used": False,
              "derived_from": "art/models/milestone4_graybox/reality_assets_graybox_v01.blend",
              "meshes": records, "previews": frames,
              "definitions": ["export/_reality_surface_meshes.gfx", "export/_reality_surface_entities.asset"],
              "limits": ["文件导出回读与离线材质预览，不代表游戏显示或最终外观批准",
                         "根目标定位器、武器朝向与推进效果待游戏核对；未改运行引用"]}
    (OUTPUT / "model_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("M4_SURFACE_MODEL_OK=" + json.dumps({"meshes": len(records), "previews": len(frames)}))


if __name__ == "__main__":
    main()
