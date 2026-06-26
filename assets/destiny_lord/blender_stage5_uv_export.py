# 命运之主第五阶段：为 LOD0 展开 UV，并导出三个 LOD 的 OBJ 源资产。
# 该脚本以 stage4_lod 为输入，不会删除现有集合或定位器。

import bpy
from pathlib import Path


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\destiny_lord")
OUTPUT_BLEND = ASSET_DIR / "destiny_lord_stage5_uv.blend"


def mesh_objects(collection_name):
    """获取集合中的网格对象，并排除重复链接造成的同名引用。"""
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        raise RuntimeError(f"缺少集合：{collection_name}")
    return [obj for obj in collection.objects if obj.type == 'MESH']


def prepare_uv(objects):
    """应用网格缩放并进行保守的智能 UV 展开，保留硬表面分件。"""
    for obj in objects:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        # 只应用缩放，避免破坏炮塔、光环和尖塔的位置与朝向。
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.025, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)


def ensure_preview_materials():
    """标记材质为可导出预览材质；群星最终贴图将在此基础上烘焙。"""
    for name in ("DL2_Hull_Silver", "DL2_Armor_Indigo", "DL2_IceBlue", "DL2_Judgement_Red"):
        material = bpy.data.materials.get(name)
        if material is not None:
            material.use_nodes = True
            material.diffuse_color[3] = 1.0


def export_obj(collection_name, filename):
    """将指定 LOD 单独导出为 OBJ，供后续转换和贴图烘焙。"""
    collection = bpy.data.collections[collection_name]
    # LOD1/LOD2 默认隐藏；导出前临时解除隐藏，否则 Blender 不会把它们加入 selected_objects。
    collection.hide_viewport = False
    objects = mesh_objects(collection_name)
    for obj in objects:
        obj.hide_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.wm.obj_export(
        filepath=str(ASSET_DIR / filename),
        export_selected_objects=True,
        export_materials=True,
        export_uv=True,
        export_normals=True,
        export_triangulated_mesh=True,
    )
    # 恢复中远景 LOD 的隐藏状态，保持打开 Blend 时只有 LOD0 可见。
    if collection_name != "DL_LOD0_High":
        collection.hide_viewport = True
        collection.hide_render = True


def main():
    lod0 = mesh_objects("DL_LOD0_High")
    prepare_uv(lod0)
    ensure_preview_materials()
    export_obj("DL_LOD0_High", "destiny_lord_lod0.obj")
    export_obj("DL_LOD1_Medium", "destiny_lord_lod1.obj")
    export_obj("DL_LOD2_Far", "destiny_lord_lod2.obj")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
    print(f"命运之主 UV 与 LOD 导出已完成：{OUTPUT_BLEND}")


if __name__ == "__main__":
    main()
