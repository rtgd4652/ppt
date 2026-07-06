# 命运之主第八阶段：拆分为群星三段舰体，并建立 PDX/Clausewitz 导出所需的定位器。
# 本脚本不依赖导出插件；安装 PDX Blender Exporter 后，只需对三个集合分别导出 .mesh。
import bpy
from pathlib import Path


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\ai_generated\destiny_lord")
INPUT = ASSET_DIR / "destiny_lord_stage7_baked.blend"
OUTPUT = ASSET_DIR / "destiny_lord_stage8_pdx_ready.blend"


def ensure_collection(name):
    """获取或创建导出集合。"""
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def clear_collection(collection):
    """清理旧的导出副本，使脚本可以重复运行。"""
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def link_copy(collection, source):
    """复制网格对象及其网格数据，避免改变原始 LOD0。"""
    clone = source.copy()
    clone.data = source.data.copy()
    clone.name = source.name.replace("DL2_", "DL_").replace("DL3_", "DL_")
    collection.objects.link(clone)
    return clone


def add_locator(collection, name, position, rotation=(0.0, 0.0, 0.0)):
    """添加 PDX 导出器会识别的空物体定位器。"""
    locator = bpy.data.objects.new(name, None)
    locator.empty_display_type = 'ARROWS'
    locator.empty_display_size = 0.75
    locator.location = position
    locator.rotation_euler = rotation
    collection.objects.link(locator)
    return locator


def section_for_object(obj):
    """按物体原点的 X 位置划分舰艏、舰体、舰艉；X 正方向为舰首。"""
    x = obj.location.x
    if x >= 12.0:
        return "DL_PDX_Bow"
    if x <= -20.0:
        return "DL_PDX_Stern"
    return "DL_PDX_Mid"


def build_mesh_sections():
    """从高模 LOD0 复制出三段可单独导出的舰体。"""
    source = bpy.data.collections.get("DL_LOD0_High")
    if source is None:
        raise RuntimeError("未找到 DL_LOD0_High 集合，请先完成第七阶段。")

    collections = {
        "DL_PDX_Bow": ensure_collection("DL_PDX_Bow"),
        "DL_PDX_Mid": ensure_collection("DL_PDX_Mid"),
        "DL_PDX_Stern": ensure_collection("DL_PDX_Stern"),
    }
    for collection in collections.values():
        clear_collection(collection)

    for obj in source.objects:
        if obj.type == 'MESH':
            link_copy(collections[section_for_object(obj)], obj)
    return collections


def build_bow_locators(collection):
    """建立 16 个泰坦级武器定位器，对应 DESTINY_LORD_BOW 的 T_01 至 T_16。"""
    for side in (-1, 1):
        for index in range(8):
            number = index + 1 if side == -1 else index + 9
            position = (30 - index * 1.4, side * (3.5 + index * 1.55), 2.4)
            add_locator(collection, f"titanic_gun_{number:02d}", position)
    add_locator(collection, "root", (0.0, 0.0, 0.0))
    add_locator(collection, "explosion_locator_01", (27.0, 0.0, 2.0))


def build_mid_locators(collection):
    """建立 20 个 X 槽定位器，对应 DESTINY_LORD_MID 的 X_01 至 X_20。"""
    for side in (-1, 1):
        for index in range(10):
            number = index + 1 if side == -1 else index + 11
            position = (17 - index * 4.2, side * (10.5 + (index % 5) * 4.0), 1.7)
            add_locator(collection, f"extra_large_gun_{number:02d}", position)
    add_locator(collection, "explosion_locator_02", (0.0, 0.0, 4.0))
    add_locator(collection, "explosion_locator_03", (-12.0, 0.0, 3.0))


def build_stern_locators(collection):
    """建立双光环、引擎和爆炸定位器。"""
    add_locator(collection, "aura_slot_01", (-27.0, 9.0, 5.0))
    add_locator(collection, "aura_slot_02", (-27.0, -9.0, 5.0))
    add_locator(collection, "engine_large_01", (-40.0, -5.0, 0.0))
    add_locator(collection, "engine_large_02", (-40.0, 5.0, 0.0))
    add_locator(collection, "explosion_locator_04", (-27.0, 0.0, 2.0))
    add_locator(collection, "explosion_locator_05", (-38.0, 0.0, 0.0))


def export_obj(collection, filename):
    """同时导出 OBJ 交换文件，方便在 PDX 导出器外复核三段模型。"""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = next(obj for obj in collection.objects if obj.type == 'MESH')
    bpy.ops.wm.obj_export(filepath=str(ASSET_DIR / filename), export_selected_objects=True)


def main():
    # 先确保从第七阶段文件开始，避免在用户当前 Blender 场景中意外改动原模型。
    bpy.ops.wm.open_mainfile(filepath=str(INPUT))
    collections = build_mesh_sections()
    build_bow_locators(collections["DL_PDX_Bow"])
    build_mid_locators(collections["DL_PDX_Mid"])
    build_stern_locators(collections["DL_PDX_Stern"])

    export_obj(collections["DL_PDX_Bow"], "destiny_lord_bow_pdx_source.obj")
    export_obj(collections["DL_PDX_Mid"], "destiny_lord_mid_pdx_source.obj")
    export_obj(collections["DL_PDX_Stern"], "destiny_lord_stern_pdx_source.obj")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print(f"命运之主 PDX 导出准备已完成：{OUTPUT}")


if __name__ == "__main__":
    main()

