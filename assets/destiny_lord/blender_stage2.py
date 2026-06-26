# 命运之主第二阶段低面数模型：重建为平放的星舰轮廓，而非第一版技术骨架。
# 坐标约定：+X 为舰艏，-X 为舰艉，Z 为上方。脚本会创建独立的新场景文件。

import bpy
import math
from pathlib import Path


OUTPUT = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\destiny_lord\destiny_lord_stage2.blend")


def material(name, color, metallic=0.0, roughness=0.4, emission=None):
    """建立简洁的预览材质。"""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    node = mat.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (*color, 1.0)
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = roughness
    if emission:
        node.inputs["Emission Color"].default_value = (*emission, 1.0)
        node.inputs["Emission Strength"].default_value = 5.0
    return mat


def prism(name, points, z_bottom, z_top, mat):
    """以 XY 平面轮廓创建闭合棱柱，是低面数舰体与翼面的基础。"""
    count = len(points)
    verts = [(x, y, z_bottom) for x, y in points] + [(x, y, z_top) for x, y in points]
    faces = [list(range(count)), list(range(count, count * 2))]
    for i in range(count):
        j = (i + 1) % count
        faces.append([i, j, j + count, i + count])
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = False
    bevel = obj.modifiers.new("DL_Armor_Edge", "BEVEL")
    bevel.width = 0.45
    bevel.segments = 2
    return obj


def cube(name, location, scale, mat, bevel=0.2):
    """创建模块化装甲、炮塔基座与舰桥的低面数方块。"""
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    mod = obj.modifiers.new("DL_Bevel", "BEVEL")
    mod.width = bevel
    mod.segments = 2
    return obj


def cylinder(name, location, radius, depth, mat, rotation=(0, math.pi / 2, 0)):
    """创建沿 X 轴的炮管或推进器。"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def torus(name, location, major, minor, mat, rotation=(0, 0, 0)):
    """创建命运环与双光环投射器。"""
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=20, minor_segments=6, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def look_at(obj, target):
    """让相机和灯光面向舰体中心。"""
    direction = mathutils.Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def main():
    # 新文件使用干净场景，避免第一版骨架影响观察。
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    global mathutils
    import mathutils

    silver = material("DL2_Hull_Silver", (0.52, 0.62, 0.78), 0.88, 0.22)
    dark = material("DL2_Armor_Indigo", (0.03, 0.06, 0.15), 0.75, 0.28)
    ice = material("DL2_IceBlue", (0.05, 0.22, 0.85), 0.55, 0.18, (0.04, 0.45, 1.0))
    red = material("DL2_Judgement_Red", (0.55, 0.04, 0.02), 0.65, 0.22, (1.0, 0.06, 0.01))

    # 主舰体：箭头形低面数轮廓。
    prism("DL2_Main_Hull", [(44, 0), (20, 11), (-8, 13), (-38, 8), (-46, 0), (-38, -8), (-8, -13), (20, -11)], -2.6, 2.6, silver)
    prism("DL2_Upper_Armor", [(30, 0), (12, 7), (-18, 8), (-28, 0), (-18, -8), (12, -7)], 2.6, 5.1, dark)

    # 六翼结构：两大翼与四片小翼，保留概念图的中心权威轮廓。
    prism("DL2_Port_Wing", [(14, 8), (-2, 34), (-28, 29), (-18, 10)], -1.0, 1.7, silver)
    prism("DL2_Starboard_Wing", [(14, -8), (-2, -34), (-28, -29), (-18, -10)], -1.0, 1.7, silver)
    prism("DL2_Port_Upper_Wing", [(10, 6), (2, 22), (-8, 19), (-4, 7)], 2.0, 4.1, dark)
    prism("DL2_Starboard_Upper_Wing", [(10, -6), (2, -22), (-8, -19), (-4, -7)], 2.0, 4.1, dark)
    prism("DL2_Port_Lower_Wing", [(-5, 8), (-16, 24), (-30, 21), (-20, 7)], -2.2, -0.3, dark)
    prism("DL2_Starboard_Lower_Wing", [(-5, -8), (-16, -24), (-30, -21), (-20, -7)], -2.2, -0.3, dark)

    # 中央命运环与核心晶体。
    torus("DL2_Fate_Ring", (0, 0, 6.2), 9.5, 0.65, ice)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=3.0, radius2=0.8, depth=7.0, location=(0, 0, 6.4), rotation=(0, 0, math.radians(45)))
    core = bpy.context.object
    core.name = "DL2_Fate_Crystal"
    core.data.materials.append(ice)

    # 舰桥与装甲阶梯。
    cube("DL2_Bridge", (-5, 0, 7.0), (4.2, 3.0, 1.2), silver)
    cube("DL2_Observation_Spire", (-7, 0, 10.0), (1.2, 1.2, 3.5), ice)

    # 16 门 T 槽主炮：左右各八门红金炮管。
    for side in (-1, 1):
        for index in range(8):
            y = side * (3.5 + index * 1.55)
            cylinder(f"DL2_Turret_T_{side}_{index}", (30 - index * 1.4, y, 2.4), 0.55, 9.0, red)

    # 20 门 X 槽炮：两翼各十门冰蓝炮塔。
    for side in (-1, 1):
        for index in range(10):
            x = 17 - index * 4.2
            y = side * (10.5 + (index % 5) * 4.0)
            cylinder(f"DL2_Turret_X_{side}_{index}", (x, y, 1.7), 0.42, 5.6, ice)

    # 双光环投射器与四组推进器。
    torus("DL2_Aura_Guardian", (-27, 9, 5.0), 4.0, 0.38, ice, (math.pi / 2, 0, 0))
    torus("DL2_Aura_Suppression", (-27, -9, 5.0), 4.0, 0.38, ice, (math.pi / 2, 0, 0))
    for side in (-1, 1):
        for index in range(2):
            cylinder(f"DL2_Engine_{side}_{index}", (-45, side * (4.5 + index * 5.5), 0), 1.6, 6.0, ice)

    # 预览相机与灯光：打开文件后默认即可看到俯视三分之四视图。
    bpy.ops.object.camera_add(location=(82, -88, 76))
    cam = bpy.context.object
    cam.name = "DL2_PreviewCamera"
    look_at(cam, (0, 0, 0))
    cam.data.lens = 58
    bpy.context.scene.camera = cam
    for name, location, energy, color in [
        ("DL2_Key", (35, -40, 65), 2200, (0.72, 0.86, 1.0)),
        ("DL2_Fill", (-45, 30, 35), 1500, (0.10, 0.35, 1.0)),
        ("DL2_Rim", (-20, -40, 20), 1000, (1.0, 0.18, 0.05)),
    ]:
        bpy.ops.object.light_add(type='AREA', location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = 'DISK'
        light.data.size = 18
        light.data.color = color
        look_at(light, (0, 0, 0))

    bpy.context.scene.world.color = (0.005, 0.01, 0.03)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print(f"命运之主第二阶段模型已保存：{OUTPUT}")


if __name__ == "__main__":
    main()
