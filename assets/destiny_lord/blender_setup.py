# 命运之主 Blender 场景配置脚本。
# 用途：导入低面数 OBJ 骨架，建立专属集合、PBR 材质占位、相机与三点灯光。
# 兼容 Blender 4.x；不会删除用户已有对象，只新增 DestinyLord_Work 集合。

import bpy
from pathlib import Path


# Mod 内模型源文件的绝对路径。
ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\destiny_lord")
OBJ_PATH = ASSET_DIR / "destiny_lord_blockout.obj"
COLLECTION_NAME = "DestinyLord_Work"


def get_or_create_collection(name: str):
    """取得命运之主工作集合，并确保它挂在场景根集合中。"""
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def get_or_create_material(name: str, color, metallic, roughness, emission=None):
    """创建可直接用于预览的 Principled BSDF 材质。"""
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        # Blender 4.x 的自发光颜色与强度输入。
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 4.0
    return material


def link_to_work_collection(objects, collection):
    """将导入对象链接到专属工作集合，同时保留 Blender 的默认导入链接。"""
    for obj in objects:
        if obj.name not in collection.objects:
            collection.objects.link(obj)


def import_blockout():
    """导入 OBJ 骨架；若文件路径不存在则明确报错。"""
    if not OBJ_PATH.exists():
        raise FileNotFoundError(f"未找到命运之主 OBJ：{OBJ_PATH}")
    before = set(bpy.context.scene.objects)
    bpy.ops.wm.obj_import(filepath=str(OBJ_PATH))
    return [obj for obj in bpy.context.scene.objects if obj not in before]


def setup_preview_camera(collection):
    """创建建模预览相机，便于核对舰体比例与轮廓。"""
    camera_data = bpy.data.cameras.new("DestinyLord_PreviewCamera")
    camera = bpy.data.objects.new("DestinyLord_PreviewCamera", camera_data)
    collection.objects.link(camera)
    camera.location = (70.0, -70.0, 50.0)
    camera.rotation_euler = (0.96, 0.0, 0.78)
    camera_data.lens = 55
    bpy.context.scene.camera = camera


def setup_preview_lights(collection):
    """建立冷白主光、冰蓝辅光与暖色轮廓光，模拟概念图的未来圣域气氛。"""
    light_specs = [
        ("DestinyLord_Key", "AREA", (25.0, -25.0, 35.0), (0.75, 0.87, 1.0), 2500),
        ("DestinyLord_Fill", "AREA", (-25.0, 20.0, 15.0), (0.15, 0.45, 1.0), 1500),
        ("DestinyLord_Rim", "AREA", (-10.0, -35.0, 20.0), (1.0, 0.35, 0.18), 1000),
    ]
    for name, light_type, location, color, energy in light_specs:
        light_data = bpy.data.lights.new(name, light_type)
        light_data.energy = energy
        light_data.color = color
        light_data.shape = "DISK"
        light_data.size = 12.0
        light = bpy.data.objects.new(name, light_data)
        light.location = location
        collection.objects.link(light)


def main():
    """执行命运之主建模场景的首次配置。"""
    work_collection = get_or_create_collection(COLLECTION_NAME)
    imported = import_blockout()
    link_to_work_collection(imported, work_collection)

    # 创建三种基础材质；后续可替换为群星需要的贴图与 shader 配置。
    hull = get_or_create_material("DL_Hull_Silver", (0.55, 0.64, 0.78), 0.85, 0.24)
    ice = get_or_create_material("DL_Emissive_IceBlue", (0.05, 0.25, 0.9), 0.55, 0.16, (0.05, 0.4, 1.0))
    engine = get_or_create_material("DL_Engine_Blue", (0.03, 0.12, 0.55), 0.75, 0.18, (0.02, 0.3, 1.0))

    for obj in imported:
        if obj.type != "MESH":
            continue
        obj.name = f"DL_{obj.name}"
        obj.data.materials.clear()
        if "Fate_Ring" in obj.name or "Aura_Projector" in obj.name:
            obj.data.materials.append(ice)
        elif "Engine" in obj.name:
            obj.data.materials.append(engine)
        else:
            obj.data.materials.append(hull)
        # 启用平滑着色并保留自动平滑边界，方便后续硬表面细化。
        for polygon in obj.data.polygons:
            polygon.use_smooth = True

    setup_preview_camera(work_collection)
    setup_preview_lights(work_collection)
    print("命运之主：OBJ 骨架、材质、相机与灯光已配置完成。")


if __name__ == "__main__":
    main()
