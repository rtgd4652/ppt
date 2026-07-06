# 命运之主第四阶段：为群星接入准备 LOD 集合与武器/核心定位器。
# 以 stage3 为输入，保留 LOD0 原模型，并建立可继续导出的 LOD1/LOD2 副本。

import bpy
from pathlib import Path


OUTPUT = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\ai_generated\destiny_lord\destiny_lord_stage4_lod.blend")


def get_collection(name):
    """获取或创建场景中的指定集合。"""
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def link_once(collection, obj):
    """避免重复链接对象。"""
    if collection.objects.get(obj.name) is None:
        collection.objects.link(obj)


def duplicate_lod(source_objects, collection, ratio, prefix):
    """复制网格并应用减面，用于群星的中远景 LOD。"""
    for source in source_objects:
        if source.type != 'MESH':
            continue
        duplicate = source.copy()
        duplicate.data = source.data.copy()
        duplicate.name = prefix + source.name
        collection.objects.link(duplicate)
        decimate = duplicate.modifiers.new("DL_LOD_Decimate", 'DECIMATE')
        decimate.ratio = ratio
        bpy.context.view_layer.objects.active = duplicate
        duplicate.select_set(True)
        try:
            bpy.ops.object.modifier_apply(modifier=decimate.name)
        except RuntimeError:
            # 少数极低面数部件无需继续减面，保留原几何即可。
            duplicate.modifiers.remove(decimate)
        duplicate.select_set(False)


def add_locator(collection, name, location, locator_type):
    """建立空物体定位器；后续导出时可映射为群星炮塔与组件定位点。"""
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = locator_type
    empty.empty_display_size = 0.8
    empty.location = location
    collection.objects.link(empty)
    return empty


def main():
    # 第二、三阶段的源模型位于默认 Collection，而非场景根集合。
    source_collection = bpy.data.collections.get("Collection")
    if source_collection is None:
        raise RuntimeError("缺少阶段三的源模型集合 Collection")
    lod0 = get_collection("DL_LOD0_High")
    lod1 = get_collection("DL_LOD1_Medium")
    lod2 = get_collection("DL_LOD2_Far")
    locators = get_collection("DL_Game_Locators")

    # 仅筛选阶段 2/3 的舰体网格，不复制相机、灯光或旧的 LOD 副本。
    source = [obj for obj in list(source_collection.objects) if obj.type == 'MESH' and not obj.name.startswith('LOD')]
    for obj in source:
        link_once(lod0, obj)
    duplicate_lod(source, lod1, 0.45, "LOD1_")
    duplicate_lod(source, lod2, 0.12, "LOD2_")

    # 16 个 T 槽定位器：两侧各八个，匹配命运之主舰艏的主炮阵列。
    for side in (-1, 1):
        for index in range(8):
            x = 30 - index * 1.4
            y = side * (3.5 + index * 1.55)
            add_locator(locators, f"locator_turret_T_{side}_{index:02d}", (x, y, 2.4), 'ARROWS')

    # 20 个 X 槽定位器：两翼各十个，用于超大型射线炮。
    for side in (-1, 1):
        for index in range(10):
            x = 17 - index * 4.2
            y = side * (10.5 + (index % 5) * 4.0)
            add_locator(locators, f"locator_turret_X_{side}_{index:02d}", (x, y, 1.7), 'ARROWS')

    # 必需核心与双光环定位器。
    core_locations = {
        "locator_power_core": (-12, 0, 4.0),
        "locator_ftl_core": (-22, 0, 3.0),
        "locator_thruster_core": (-40, 0, 0.0),
        "locator_combat_computer": (-5, 0, 7.0),
        "locator_aura_guardian": (-27, 9, 5.0),
        "locator_aura_suppression": (-27, -9, 5.0),
    }
    for name, location in core_locations.items():
        add_locator(locators, name, location, 'SPHERE')

    # LOD1 与 LOD2 默认隐藏，避免用户打开文件时看到三层重叠舰体。
    lod1.hide_viewport = True
    lod1.hide_render = True
    lod2.hide_viewport = True
    lod2.hide_render = True
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print(f"命运之主第四阶段 LOD 文件已保存：{OUTPUT}")


if __name__ == "__main__":
    main()

