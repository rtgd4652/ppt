# 命运之主第三阶段硬表面细化：在 stage2 模型上补充装甲分件、尖塔、炮座和推进器喷口。
# 该脚本必须以 destiny_lord_stage2.blend 为输入运行，并保存为 stage3 版本。

import bpy
import math
from pathlib import Path


OUTPUT = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\destiny_lord\destiny_lord_stage3.blend")


def mat(name):
    """取得前一阶段已建立的材质。"""
    return bpy.data.materials[name]


def cube(name, location, scale, material, rotation=(0, 0, 0), bevel=0.16):
    """创建装甲分件或炮座。"""
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    modifier = obj.modifiers.new("DL3_Bevel", "BEVEL")
    modifier.width = bevel
    modifier.segments = 2
    return obj


def cone(name, location, radius1, radius2, depth, material, rotation=(0, 0, 0)):
    """创建中央庭尖塔与舰桥晶体。"""
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=radius1, radius2=radius2, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def cylinder(name, location, radius, depth, material, rotation=(0, math.pi / 2, 0)):
    """创建炮座、推进器喷口与阵列节点。"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def add_armor_panels(silver, dark, ice):
    """在双翼与主舰体布置大块低面数装甲，细节将来交由法线贴图。"""
    for side in (-1, 1):
        for index in range(5):
            x = 13 - index * 8
            y = side * (12 + index * 3.0)
            cube(f"DL3_Wing_Armor_{side}_{index}", (x, y, 2.0), (3.2, 1.4, 0.42), silver, rotation=(0, 0, side * 0.24))
            cube(f"DL3_Wing_Light_{side}_{index}", (x, y - side * 1.55, 2.5), (2.0, 0.16, 0.08), ice, rotation=(0, 0, side * 0.24), bevel=0.04)
    for index in range(6):
        cube(f"DL3_Spine_Armor_{index}", (19 - index * 6.0, 0, 5.4), (2.4, 3.4, 0.38), silver)
        cube(f"DL3_Spine_Light_{index}", (19 - index * 6.0, 0, 5.85), (1.8, 0.2, 0.06), ice, bevel=0.03)
    # 舰首楔形装甲延伸，强化“命运之主”的箭头剪影。
    cube("DL3_Bow_Crest", (35, 0, 4.2), (7.0, 2.0, 0.55), dark, rotation=(0, 0, 0.08))
    cube("DL3_Bow_Crest_Light", (36, 0, 4.85), (5.5, 0.22, 0.08), ice, bevel=0.03)


def add_spires_and_ring_support(silver, ice):
    """增加中央庭神圣未来科技尖塔与命运环的四向支撑。"""
    for side in (-1, 1):
        for index in range(2):
            x = -5 - index * 8
            y = side * (5.0 + index * 3.2)
            cone(f"DL3_Spire_{side}_{index}", (x, y, 8.0 + index), 0.9, 0.15, 7.0 + index * 1.5, silver)
            cone(f"DL3_Spire_Core_{side}_{index}", (x, y, 11.5 + index), 0.32, 0.05, 3.5, ice)
    for side in (-1, 1):
        cube(f"DL3_Ring_Support_{side}", (-2, side * 8.8, 5.4), (1.0, 0.45, 3.0), silver, rotation=(0, side * 0.38, 0))
        cube(f"DL3_Ring_Support_Light_{side}", (-2, side * 9.25, 6.0), (0.25, 0.07, 2.3), ice, rotation=(0, side * 0.38, 0), bevel=0.03)


def add_turret_bases_and_engines(silver, dark, ice, red):
    """为已有主炮增设炮座，并把推进器从占位圆柱升级为喷口组。"""
    for side in (-1, 1):
        for index in range(8):
            x = 30 - index * 1.4
            y = side * (3.5 + index * 1.55)
            cylinder(f"DL3_T_Base_{side}_{index}", (x - 2.8, y, 2.15), 0.82, 1.4, dark)
        for index in range(10):
            x = 17 - index * 4.2
            y = side * (10.5 + (index % 5) * 4.0)
            cylinder(f"DL3_X_Base_{side}_{index}", (x - 1.6, y, 1.45), 0.62, 1.0, silver)
    for side in (-1, 1):
        for index in range(2):
            y = side * (4.5 + index * 5.5)
            cylinder(f"DL3_Engine_Nozzle_{side}_{index}", (-49.0, y, 0), 2.2, 1.0, dark)
            cylinder(f"DL3_Engine_Flame_{side}_{index}", (-50.0, y, 0), 1.35, 2.2, ice)
            cube(f"DL3_Engine_Pylon_{side}_{index}", (-39, y, 0), (4.0, 1.3, 1.2), silver)
    # 红金主炮阵列添加少量亮条，保持不额外堆叠高面数。
    for side in (-1, 1):
        cube(f"DL3_Turret_Rail_{side}", (25, side * 7.0, 2.8), (8.0, 0.18, 0.10), red, bevel=0.03)


def main():
    silver = mat("DL2_Hull_Silver")
    dark = mat("DL2_Armor_Indigo")
    ice = mat("DL2_IceBlue")
    red = mat("DL2_Judgement_Red")
    add_armor_panels(silver, dark, ice)
    add_spires_and_ring_support(silver, ice)
    add_turret_bases_and_engines(silver, dark, ice, red)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print(f"命运之主第三阶段模型已保存：{OUTPUT}")


if __name__ == "__main__":
    main()
