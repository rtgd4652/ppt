# 命运之主精修包 A：在已可导出的 Stage8 基础上强化轮廓、命运环和炮列层次。
# 本脚本只生成独立预览源文件，不覆盖游戏内 mesh；验证通过后再进入 PDX 导出。
import math
from pathlib import Path

import bpy
from mathutils import Vector, geometry


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\ai_generated\destiny_lord")
INPUT = ASSET_DIR / "destiny_lord_stage8_pdx_ready.blend"
OUTPUT = ASSET_DIR / "destiny_lord_stage9_refined_A.blend"
PREVIEW = ASSET_DIR / "destiny_lord_stage9_refined_A_preview.png"


def material(name):
    return bpy.data.materials[name]


def collection(name):
    found = bpy.data.collections.get(name)
    if found is None:
        found = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(found)
    return found


def move_to_collection(obj, target):
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    target.objects.link(obj)


def cube(name, location, scale, mat, rotation=(0.0, 0.0, 0.0), bevel=0.12, target=None):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel > 0:
        mod = obj.modifiers.new("DL9_Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    if target is not None:
        move_to_collection(obj, target)
    return obj


def cone(name, location, radius1, radius2, depth, mat, rotation=(0.0, 0.0, 0.0), target=None):
    bpy.ops.mesh.primitive_cone_add(
        vertices=6,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    if target is not None:
        move_to_collection(obj, target)
    return obj


def torus(name, location, major_radius, minor_radius, mat, rotation=(0.0, 0.0, 0.0), target=None):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=96,
        minor_segments=8,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    if target is not None:
        move_to_collection(obj, target)
    return obj


def wing_plate(name, side, mat, target):
    y = side
    thickness = 1.25
    top_z = 1.6
    bottom_z = top_z - thickness
    outline = [
        (-28.6, y * 8.0),
        (6.0, y * 8.0),
        (14.8, y * 14.6),
        (14.8, y * 22.0),
        (11.0, y * 22.0),
        (11.0, y * 27.9),
        (5.8, y * 34.2),
        (-20.0, y * 34.2),
        (-20.0, y * 31.3),
        (-28.6, y * 34.2),
    ]
    verts = [(x, yy, top_z) for x, yy in outline] + [(x, yy, bottom_z) for x, yy in outline]
    count = len(outline)
    triangles = geometry.tessellate_polygon([[Vector((x, yy, top_z)) for x, yy in outline]])
    faces = []
    for triangle in triangles:
        if side > 0:
            faces.append(tuple(triangle))
            faces.append(tuple(reversed([index + count for index in triangle])))
        else:
            faces.append(tuple(reversed(triangle)))
            faces.append(tuple(index + count for index in triangle))
    for index in range(count):
        next_index = (index + 1) % count
        if side > 0:
            faces.append((index, next_index, next_index + count, index + count))
        else:
            faces.append((next_index, index, index + count, next_index + count))

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    target.objects.link(obj)
    mod = obj.modifiers.new("DL9_Bevel", "BEVEL")
    mod.width = 0.10
    mod.segments = 2
    return obj


def add_bow_and_wing_silhouette(target, hull, armor, ice):
    # 舰艏加长主脊与双侧“判定刃”，让远景轮廓更接近超旗舰。
    cube("DL9_Bow_Long_Keel", (43.0, 0.0, 2.0), (8.5, 1.0, 0.55), armor, rotation=(0, 0, 0.02), bevel=0.08, target=target)
    cube("DL9_Bow_Crown_Plate", (39.5, 0.0, 5.35), (5.8, 3.2, 0.42), hull, bevel=0.10, target=target)
    cube("DL9_Bow_Crown_Light", (41.2, 0.0, 5.85), (4.6, 0.16, 0.07), ice, bevel=0.03, target=target)
    for side in (-1, 1):
        cube(
            f"DL9_Bow_Judgement_Blade_{side}",
            (34.0, side * 14.6, 1.35),
            (3.2, 0.42, 0.32),
            armor,
            rotation=(0, 0, side * 0.28),
            bevel=0.06,
            target=target,
        )
        # 外侧翼缘只保留极短端帽，避免游戏内长条在单侧视角下像翅膀被拉裂。
        for index, x in enumerate((-9.0, 6.5)):
            cube(
                f"DL9_Outer_Wing_Rim_{side}_{index}",
                (x, side * 27.8, 1.0),
                (1.25, 0.36, 0.26),
                hull,
                rotation=(0, 0, side * -0.02),
                bevel=0.05,
                target=target,
            )
            cube(
                f"DL9_Outer_Wing_Rim_Light_{side}_{index}",
                (x + 0.1, side * 27.35, 1.32),
                (0.8, 0.08, 0.05),
                ice,
                rotation=(0, 0, side * -0.02),
                bevel=0.02,
                target=target,
            )


def add_central_ridge_layers(target, hull, armor, ice):
    cube("DL9_Center_Ridge_Aft", (-15.0, 0.0, 5.35), (9.5, 2.8, 0.32), armor, bevel=0.07, target=target)
    cube("DL9_Center_Ridge_Mid", (0.0, 0.0, 5.55), (7.0, 2.2, 0.32), hull, bevel=0.07, target=target)
    cube("DL9_Center_Ridge_Fwd", (13.0, 0.0, 5.20), (5.4, 1.7, 0.28), armor, bevel=0.06, target=target)
    for x in (-18.0, -4.0, 9.0):
        cube(f"DL9_Center_Ridge_Mark_{int(x * 10)}", (x, 0.0, 5.95), (2.6, 0.12, 0.05), ice, bevel=0.02, target=target)


def add_flagship_surface_details(target, hull, armor, ice, red):
    for index, angle in enumerate((0.35, 1.2, 1.95, 2.8, 3.55, 4.35, 5.05, 5.9)):
        x = math.cos(angle) * 14.4
        y = math.sin(angle) * 14.4
        cube(
            f"DL9_Fate_Ring_Node_{index}",
            (x, y, 6.88),
            (1.25, 0.34, 0.28),
            armor if index % 2 else hull,
            rotation=(0, 0, angle),
            bevel=0.04,
            target=target,
        )

    cube("DL9_Bridge_Collar_Aft", (-5.4, 0.0, 8.35), (4.8, 3.2, 0.24), armor, bevel=0.06, target=target)
    cube("DL9_Bridge_Collar_Fwd", (-1.2, 0.0, 8.70), (3.4, 2.4, 0.22), hull, bevel=0.05, target=target)
    cube("DL9_Bridge_Judgement_Mark", (-3.0, 0.0, 9.05), (1.7, 0.10, 0.05), red, bevel=0.02, target=target)
    cube("DL9_Observation_Spire_Crown", (-7.0, 0.0, 13.55), (1.05, 1.05, 0.28), ice, bevel=0.04, target=target)
    for side in (-1, 1):
        cube("DL9_Bow_Crown_SideBrace_" + str(side), (39.5, side * 3.55, 5.58), (4.2, 0.18, 0.16), armor, bevel=0.03, target=target)
        prefix = "Port_Wing" if side > 0 else "Starboard_Wing"
        for index, (x, y, sx, sy, rot) in enumerate(((-9.5, 10.4, 7.0, 1.05, 0.10), (6.5, 10.9, 6.2, 0.90, -0.14))):
            cube(
                f"DL9_{prefix}_Root_Shoulder_{index}",
                (x, side * y, 2.05),
                (sx, sy, 0.14),
                armor if index == 0 else hull,
                rotation=(0.0, 0.0, side * rot),
                bevel=0.04,
                target=target,
            )
        for index, (x, y, sx, rot) in enumerate(((-7.5, 9.25, 4.2, 0.08), (6.2, 9.55, 3.6, -0.12))):
            cube(
                f"DL9_{prefix}_Root_Glow_Notch_{index}",
                (x, side * y, 2.24),
                (sx, 0.08, 0.035),
                ice,
                rotation=(0.0, 0.0, side * rot),
                bevel=0.01,
                target=target,
            )
        for index, (x, y, sx, sy, rot) in enumerate(((-18.0, 17.4, 5.8, 0.42, 0.04), (-5.0, 21.0, 6.8, 0.48, -0.08), (7.5, 25.0, 4.6, 0.38, -0.14))):
            cube(
                f"DL9_{prefix}_Top_Armor_Facet_{index}",
                (x, side * y, 1.86),
                (sx, sy, 0.08),
                armor,
                rotation=(0.0, 0.0, side * rot),
                bevel=0.018,
                target=target,
            )
        for index, (x, y, sx, rot) in enumerate(((-14.0, 16.0, 2.8, 0.03), (2.5, 23.5, 2.4, -0.12))):
            cube(
                f"DL9_{prefix}_Top_Glow_Slit_{index}",
                (x, side * y, 1.96),
                (sx, 0.055, 0.035),
                ice,
                rotation=(0.0, 0.0, side * rot),
                bevel=0.006,
                target=target,
            )
        for index, (x, z, sx) in enumerate(((-15.5, 2.02, 8.5), (-2.0, 2.08, 8.0), (8.5, 1.98, 4.5))):
            cube(
                f"DL9_Main_Hull_Side_Belt_{side}_{index}",
                (x, side * 8.16, z),
                (sx, 0.16, 0.07),
                armor,
                bevel=0.018,
                target=target,
            )
        for index, (x, z, sx) in enumerate(((-10.0, 0.92, 7.0), (5.5, 0.94, 5.4))):
            cube(
                f"DL9_Main_Hull_Lower_Belt_{side}_{index}",
                (x, side * 8.18, z),
                (sx, 0.14, 0.06),
                armor,
                bevel=0.015,
                target=target,
            )
        for index, x in enumerate((-20.0, -8.0, 4.0, 14.0)):
            cube(
                f"DL9_Main_Hull_Side_Break_{side}_{index}",
                (x, side * 8.22, 1.45),
                (0.18, 0.12, 0.64),
                armor,
                bevel=0.012,
                target=target,
            )
        for index, (x, z, sx, sz) in enumerate(((-15.5, 1.20, 8.0, 0.34), (0.0, 1.18, 8.5, 0.32), (13.0, 1.16, 5.8, 0.30))):
            cube(
                f"DL9_Main_Hull_Side_Shadow_Armor_{side}_{index}",
                (x, side * 8.30, z),
                (sx, 0.18, sz),
                armor,
                bevel=0.018,
                target=target,
            )
        for index, (x, z, sx, sz) in enumerate(((-18.5, 0.62, 5.2, 0.22), (-6.5, 0.58, 6.0, 0.24), (7.0, 0.60, 5.6, 0.22), (18.0, 0.64, 3.6, 0.20))):
            cube(
                f"DL9_Main_Hull_Side_Shadow_Skirt_{side}_{index}",
                (x, side * 8.42, z),
                (sx, 0.16, sz),
                hull,
                bevel=0.014,
                target=target,
            )
        for index, (x, z, sx, sz) in enumerate(((23.5, 1.06, 5.0, 0.28), (30.5, 1.00, 4.2, 0.24))):
            cube(
                f"DL9_Main_Hull_Side_Forward_Dark_Cowl_{side}_{index}",
                (x, side * 8.46, z),
                (sx, 0.17, sz),
                hull,
                bevel=0.014,
                target=target,
            )
        for index, x in enumerate((-12.5, 2.0, 15.0)):
            cube(
                f"DL9_Main_Hull_Side_Shadow_Divider_{side}_{index}",
                (x, side * 8.48, 0.86),
                (0.16, 0.12, 0.46),
                armor,
                bevel=0.01,
                target=target,
            )
        for index, (x, z, sx) in enumerate(((-20.0, 1.36, 1.7), (-8.0, 1.30, 1.5), (5.5, 1.34, 1.6), (18.0, 1.38, 1.4))):
            cube(
                f"DL9_Main_Hull_Side_Glow_Slit_{side}_{index}",
                (x, side * 8.56, z),
                (sx, 0.055, 0.045),
                ice,
                bevel=0.008,
                target=target,
            )
        for index, (x, z) in enumerate(((-23.0, 0.92), (-3.5, 0.88), (12.0, 0.96))):
            cube(
                f"DL9_Main_Hull_Side_Glow_Window_{side}_{index}",
                (x, side * 8.58, z),
                (0.22, 0.05, 0.26),
                ice,
                bevel=0.006,
                target=target,
            )
        for index, (x, z, sx) in enumerate(((-22.0, 1.74, 3.4), (-10.0, 1.70, 3.8), (4.0, 1.72, 3.6), (17.0, 1.76, 3.0))):
            cube(
                f"DL9_Main_Hull_Side_Casemate_{side}_{index}",
                (x, side * 8.53, z),
                (sx, 0.12, 0.13),
                armor,
                bevel=0.012,
                target=target,
            )
        for index, (x, z) in enumerate(((-18.5, 1.92), (-6.0, 1.88), (8.5, 1.90), (20.0, 1.94))):
            cube(
                f"DL9_Main_Hull_Side_Casemate_Glimmer_{side}_{index}",
                (x, side * 8.60, z),
                (0.52, 0.045, 0.035),
                ice,
                bevel=0.006,
                target=target,
            )
        for index, (x, z, sx) in enumerate(((-13.5, 0.36, 3.6), (1.0, 0.34, 4.2), (15.0, 0.38, 3.2))):
            cube(
                f"DL9_Main_Hull_Side_Lower_Facet_{side}_{index}",
                (x, side * 8.50, z),
                (sx, 0.13, 0.12),
                armor,
                bevel=0.012,
                target=target,
            )


def add_concept_fate_apparatus(target, hull, armor, ice, red):
    # 包 B：向概念图靠拢的命运核心装置。全部为贴体短件/环件，避免独立长杆。
    torus("DL9_Fate_Ring_Vertical_Fore", (0.0, 0.0, 8.15), 4.45, 0.18, ice, rotation=(math.radians(90), 0.0, 0.0), target=target)
    torus("DL9_Fate_Ring_Vertical_Athwart", (0.0, 0.0, 8.05), 3.55, 0.12, ice, rotation=(0.0, math.radians(90), 0.0), target=target)
    cone("DL9_Core_Crystal_Prism", (0.0, 0.0, 8.45), 1.45, 0.22, 4.7, ice, target=target)
    cone("DL9_Core_Crystal_Inverted", (0.0, 0.0, 5.85), 0.22, 1.10, 2.9, ice, target=target)
    torus("DL9_Fate_Ring_Core_Halo", (0.0, 0.0, 7.25), 4.0, 0.10, ice, target=target)
    for index, angle in enumerate((math.pi / 4, math.pi * 0.75, math.pi * 1.25, math.pi * 1.75)):
        x = math.cos(angle) * 3.65
        y = math.sin(angle) * 3.65
        cube(
            f"DL9_Core_Halo_Gem_{index}",
            (x, y, 7.45),
            (0.58, 0.18, 0.46),
            ice,
            rotation=(0.0, 0.0, angle),
            bevel=0.02,
            target=target,
        )
    for index, angle in enumerate((math.radians(28), math.radians(-28))):
        cube(
            f"DL9_Core_Crystal_Brace_{index}",
            (0.0, 0.0, 7.05),
            (1.1, 0.12, 0.08),
            armor,
            rotation=(0.0, 0.0, angle),
            bevel=0.015,
            target=target,
        )
    for index, angle in enumerate((0.0, math.pi / 2, math.pi, math.pi * 1.5)):
        x = math.cos(angle) * 1.45
        y = math.sin(angle) * 1.45
        cube(
            f"DL9_Core_Focus_Light_{index}",
            (x, y, 8.15),
            (0.13, 0.06, 0.74),
            ice,
            rotation=(0.0, 0.0, angle),
            bevel=0.012,
            target=target,
        )
    for index, angle in enumerate((math.radians(45), math.radians(135), math.radians(225), math.radians(315))):
        x = math.cos(angle) * 2.15
        y = math.sin(angle) * 2.15
        cube(
            f"DL9_Core_Beacon_Pane_{index}",
            (x, y, 8.55),
            (0.16, 0.07, 0.92),
            ice,
            rotation=(0.0, 0.0, angle),
            bevel=0.012,
            target=target,
        )
    for index, x in enumerate((-1.05, 1.05)):
        cube(
            f"DL9_Core_Beacon_Crown_{index}",
            (x, 0.0, 10.35),
            (0.26, 0.10, 0.82),
            ice,
            bevel=0.012,
            target=target,
        )
    for index, angle in enumerate((0.0, math.pi / 2, math.pi, math.pi * 1.5)):
        x = math.cos(angle) * 5.8
        y = math.sin(angle) * 5.8
        cube(
            f"DL9_Fate_Ring_ShortPillar_{index}",
            (x, y, 6.95),
            (0.62, 0.28, 1.05),
            armor,
            rotation=(0.0, 0.0, angle),
            bevel=0.04,
            target=target,
        )
    for side in (-1, 1):
        for index, x in enumerate((18.0, 25.0)):
            cube(
                f"DL9_Bow_Crown_BlueChannel_{side}_{index}",
                (x, side * (2.3 + index * 0.32), 5.84),
                (1.8, 0.07, 0.035),
                ice,
                rotation=(0.0, 0.0, side * -0.18),
                bevel=0.01,
                target=target,
            )


def add_destiny_core(target, hull, armor, ice):
    # 加厚命运环，并给中央核心增加上/下两层约束框，减少单薄发光圈的贴片感。
    torus("DL9_Fate_Ring_Outer", (0.0, 0.0, 6.55), 14.4, 0.38, ice, target=target)
    torus("DL9_Fate_Ring_Armor", (0.0, 0.0, 6.50), 13.1, 0.22, armor, target=target)
    for angle in (0, math.pi / 2, math.pi, math.pi * 1.5):
        x = math.cos(angle) * 10.8
        y = math.sin(angle) * 10.8
        cube(
            f"DL9_Ring_Anchor_{int(angle * 100)}",
            (x, y, 5.95),
            (2.2, 0.42, 0.42),
            hull,
            rotation=(0, 0, angle),
            bevel=0.05,
            target=target,
        )
    cube("DL9_Core_Lower_Dais", (0.0, 0.0, 4.75), (4.0, 4.0, 0.34), armor, bevel=0.08, target=target)
    cone("DL9_Core_Crystal_Upper", (0.0, 0.0, 10.2), 1.25, 0.24, 5.4, ice, target=target)
    cone("DL9_Core_Crystal_Lower", (0.0, 0.0, 3.6), 0.22, 1.05, 3.0, ice, target=target)


def add_weapon_and_engine_layers(target, hull, armor, ice, red):
    # 保持原 locator 名称不动，只增强炮座、导轨和引擎周边结构。
    for side in (-1, 1):
        cube(f"DL9_Titanic_Rail_Long_{side}", (25.0, side * 8.8, 3.05), (4.0, 0.18, 0.12), red, bevel=0.03, target=target)
        cube(f"DL9_Titanic_Rail_Back_{side}", (21.0, side * 11.0, 2.75), (3.2, 0.18, 0.10), red, rotation=(0, 0, side * 0.08), bevel=0.03, target=target)
        for index in range(4):
            cube(
                f"DL9_XL_Recess_{side}_{index}",
                (11.0 - index * 6.2, side * (15.2 + index * 1.35), 1.15),
                (1.5, 0.55, 0.22),
                armor,
                rotation=(0, 0, side * 0.18),
                bevel=0.04,
                target=target,
            )
        for index in range(3):
            y = side * (4.5 + index * 4.1)
            cube(f"DL9_Engine_Cowl_{side}_{index}", (-43.5, y, 1.5), (5.2, 1.35, 0.70), hull, bevel=0.08, target=target)
            cube(f"DL9_Engine_Glow_Slit_{side}_{index}", (-47.0, y, 1.95), (2.2, 0.16, 0.08), ice, bevel=0.02, target=target)


def remove_problem_side_rails(source):
    # 旧版侧翼长导轨在游戏高倍缩放和斜视角下容易像漂浮破片，包 A 改为不导出这组独立长杆。
    for obj in list(source.objects):
        if obj.type == "MESH" and "Turret_Rail" in obj.name:
            bpy.data.objects.remove(obj, do_unlink=True)


def replace_primary_wings_with_stable_plates(source, hull, ice):
    for obj in list(source.objects):
        if obj.type == "MESH" and obj.name in {"DL2_Port_Wing", "DL2_Starboard_Wing"}:
            bpy.data.objects.remove(obj, do_unlink=True)

    for side, name in ((1, "DL9_Port_Wing_Stable"), (-1, "DL9_Starboard_Wing_Stable")):
        for index, (x, y, sx, sy, rot) in enumerate((
            (-17.0, 15.2, 18.8, 6.2, 0.02),
            (-6.0, 22.4, 18.0, 6.4, -0.04),
            (6.5, 27.3, 13.8, 4.9, -0.08),
            (-22.5, 29.8, 8.2, 3.2, 0.10),
        )):
            cube(
                f"{name}_Plate_{index}",
                (x, side * y, 1.0),
                (sx, sy, 0.62),
                hull,
                rotation=(0.0, 0.0, side * rot),
                bevel=0.08,
                target=source,
            )
        for index, x in enumerate((-18.0, -6.0, 6.0)):
            cube(
                f"{name}_Panel_Inboard_{index}",
                (x, side * 10.0, 1.92),
                (4.6, 0.14, 0.05),
                ice,
                bevel=0.03,
                target=source,
            )


def clear_collection(coll):
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def link_copy(coll, source):
    clone = source.copy()
    clone.data = source.data.copy()
    clone.name = source.name.replace("DL2_", "DL_").replace("DL3_", "DL_").replace("DL9_", "DL_")
    coll.objects.link(clone)
    return clone


def should_export_pdx_object(obj):
    name = obj.name
    if name.startswith("LOD") or name.startswith("DL_Bake_Merged"):
        return False

    blocked = (
        "Turret" in name
        or "_T_Base_" in name
        or "_X_Base_" in name
        or "Wing_Armor" in name
        or "Wing_Light" in name
        or "Titanic_Rail" in name
        or "XL_Recess" in name
        or "Outer_Wing_Rim" in name
        or "Judgement_Blade" in name
        or "Spine_" in name
        or "Bow_Crest" in name
        or "Bow_Long_Keel" in name
        or "Stable_Edge" in name
        or "Light" in name
        or "Ring_Support" in name
        or "Engine_Cowl" in name
        or "Engine_Pylon" in name
        or "Engine_Glow_Slit" in name
        or "Engine_Flame" in name
        or "Engine_Nozzle" in name
        or "Upper_Wing" in name
        or "Lower_Wing" in name
        or "Fate_Ring_Vertical" in name
        or "Fate_Ring_Core_Halo" in name
        or "Core_Halo_Gem" in name
        or "Core_Crystal_Brace" in name
        or "Core_Focus_Light" in name
        or "Core_Beacon" in name
    )
    if blocked:
        return False

    allowed_tokens = (
        "Main_Hull",
        "Upper_Armor",
        "Port_Wing",
        "Starboard_Wing",
        "Fate_Ring",
        "Fate_Crystal",
        "Bridge",
        "Observation_Spire",
        "Engine",
        "Spire_",
        "Bow_Long_Keel",
        "Bow_Crown",
        "Fate_Ring_Outer",
        "Fate_Ring_Armor",
        "Ring_Anchor",
        "Core_",
        "Center_Ridge",
    )
    return any(token in name for token in allowed_tokens)


def section_for_object(obj):
    if "Port_Wing" in obj.name or "Starboard_Wing" in obj.name:
        return "DL_PDX_Mid"
    if "Main_Hull_Side_Belt" in obj.name or "Main_Hull_Lower_Belt" in obj.name or "Main_Hull_Side_Break" in obj.name or "Main_Hull_Side_Shadow" in obj.name or "Main_Hull_Side_Glow" in obj.name or "Main_Hull_Side_Lower_Facet" in obj.name or "Main_Hull_Side_Casemate" in obj.name or "Main_Hull_Side_Forward_Dark_Cowl" in obj.name:
        return "DL_PDX_Mid"
    x = obj.location.x
    if x >= 12.0:
        return "DL_PDX_Bow"
    if x <= -20.0:
        return "DL_PDX_Stern"
    return "DL_PDX_Mid"


def add_locator(coll, name, position):
    locator = bpy.data.objects.new(name, None)
    locator.empty_display_type = "ARROWS"
    locator.empty_display_size = 0.75
    locator.location = position
    coll.objects.link(locator)
    return locator


def rebuild_pdx_collections(source):
    cols = {name: collection(name) for name in ("DL_PDX_Bow", "DL_PDX_Mid", "DL_PDX_Stern")}
    for coll in cols.values():
        clear_collection(coll)
    for obj in source.objects:
        if obj.type == "MESH" and should_export_pdx_object(obj):
            link_copy(cols[section_for_object(obj)], obj)
    # 不导出武器可视 locator：当前武器实体会被游戏渲染成侧向长杆，影响舰体轮廓。
    add_locator(cols["DL_PDX_Bow"], "root", (0.0, 0.0, 0.0))
    add_locator(cols["DL_PDX_Bow"], "explosion_locator_01", (27.0, 0.0, 2.0))
    # 同样不导出 extra_large_gun_*，只隐藏武器实体外观，不改槽位脚本。
    for name, pos in {
        "explosion_locator_02": (0.0, 0.0, 4.0),
        "explosion_locator_03": (-12.0, 0.0, 3.0),
        "destiny_ring_light_01": (12.0, 0.0, 6.4),
        "destiny_ring_light_02": (-12.0, 0.0, 6.4),
        "destiny_ring_light_03": (0.0, 12.0, 6.4),
        "destiny_ring_light_04": (0.0, -12.0, 6.4),
        "destiny_core_light": (0.0, 0.0, 6.4),
    }.items():
        add_locator(cols["DL_PDX_Mid"], name, pos)
    for name, pos in {
        "engine_large_01": (-40.0, -5.0, 0.0),
        "engine_large_02": (-40.0, 5.0, 0.0),
        "explosion_locator_04": (-27.0, 0.0, 2.0),
        "explosion_locator_05": (-38.0, 0.0, 0.0),
    }.items():
        add_locator(cols["DL_PDX_Stern"], name, pos)
    return cols


def export_obj(coll, filename):
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in coll.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.obj_export(filepath=str(ASSET_DIR / filename), export_selected_objects=True)


def configure_preview():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 80
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.008, 0.010, 0.015)
    camera_data = bpy.data.cameras.new("DL9_Preview_Camera")
    camera = bpy.data.objects.new("DL9_Preview_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = (70.0, -88.0, 48.0)
    camera.rotation_euler = (math.radians(62), 0, math.radians(42))
    camera.data.lens = 36
    scene.camera = camera
    light_data = bpy.data.lights.new("DL9_Key_Light", "AREA")
    light = bpy.data.objects.new("DL9_Key_Light", light_data)
    bpy.context.scene.collection.objects.link(light)
    light.location = (12.0, -18.0, 36.0)
    light.data.energy = 450
    light.data.size = 10


def main():
    bpy.ops.wm.open_mainfile(filepath=str(INPUT))
    source = collection("DL_LOD0_High")
    hull = material("DL2_Hull_Silver")
    armor = material("DL2_Armor_Indigo")
    ice = material("DL2_IceBlue")
    red = material("DL2_Judgement_Red")
    remove_problem_side_rails(source)
    replace_primary_wings_with_stable_plates(source, hull, ice)
    add_bow_and_wing_silhouette(source, hull, armor, ice)
    add_central_ridge_layers(source, hull, armor, ice)
    add_destiny_core(source, hull, armor, ice)
    add_flagship_surface_details(source, hull, armor, ice, red)
    add_concept_fate_apparatus(source, hull, armor, ice, red)
    add_weapon_and_engine_layers(source, hull, armor, ice, red)
    cols = rebuild_pdx_collections(source)
    export_obj(cols["DL_PDX_Bow"], "destiny_lord_bow_stage9_refined_A.obj")
    export_obj(cols["DL_PDX_Mid"], "destiny_lord_mid_stage9_refined_A.obj")
    export_obj(cols["DL_PDX_Stern"], "destiny_lord_stern_stage9_refined_A.obj")
    configure_preview()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    bpy.context.scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)
    print(f"命运之主精修包 A 独立源文件已生成：{OUTPUT}")
    print(f"命运之主精修包 A 预览图已生成：{PREVIEW}")


if __name__ == "__main__":
    main()

