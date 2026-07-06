# 命运之主第七阶段：以 LOD0 的副本打包 UV，并烘焙基础 BaseColor、Emissive 与 Normal 贴图。
# 原始 LOD0、LOD1、LOD2 与定位器不会被修改；烘焙副本保存在 DL_Bake_Source 集合。

import bpy
from pathlib import Path


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\ai_generated\destiny_lord")
TEXTURE_DIR = ASSET_DIR / "textures"
OUTPUT = ASSET_DIR / "destiny_lord_stage7_baked.blend"
RESOLUTION = 1024


def ensure_collection(name):
    """获取或创建烘焙集合。"""
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def create_bake_image(name):
    """创建可保存的非颜色贴图图像。"""
    image = bpy.data.images.get(name)
    if image is not None:
        bpy.data.images.remove(image)
    image = bpy.data.images.new(name, width=RESOLUTION, height=RESOLUTION, alpha=True, float_buffer=False)
    image.file_format = 'PNG'
    return image


def set_active_bake_image(material, image):
    """在每个材质中创建并激活 Image Texture 节点，供 Cycles 烘焙写入。"""
    material.use_nodes = True
    nodes = material.node_tree.nodes
    for node in list(nodes):
        if node.name.startswith("DL_Bake_Target"):
            nodes.remove(node)
    node = nodes.new("ShaderNodeTexImage")
    node.name = "DL_Bake_Target"
    node.label = "DL Bake Target"
    node.image = image
    node.select = True
    nodes.active = node


def duplicate_and_join_lod0():
    """复制 LOD0 网格，应用可视修饰器后合并为单一烘焙对象。"""
    source = bpy.data.collections.get("DL_LOD0_High")
    if source is None:
        raise RuntimeError("未找到 DL_LOD0_High 集合")
    bake_collection = ensure_collection("DL_Bake_Source")
    for obj in list(bake_collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    copies = []
    for obj in source.objects:
        if obj.type != 'MESH':
            continue
        clone = obj.copy()
        clone.data = obj.data.copy()
        clone.name = "BAKE_" + obj.name
        bake_collection.objects.link(clone)
        clone.hide_set(False)
        copies.append(clone)
    if not copies:
        raise RuntimeError("LOD0 中没有可烘焙网格")
    bpy.ops.object.select_all(action='DESELECT')
    for obj in copies:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        # 依次应用副本上的装甲倒角等修饰器，确保烘焙与可见模型一致。
        for modifier in list(obj.modifiers):
            try:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            except RuntimeError:
                pass
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    merged = bpy.context.object
    merged.name = "DL_Bake_Merged_LOD0"
    return merged, bake_collection


def unwrap_merged(obj):
    """为合并副本生成唯一且打包的 UV 岛。"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.012, area_weight=0.0, correct_aspect=True, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')


def bake(obj, image, bake_type, filepath):
    """烘焙指定贴图并保存为 PNG。"""
    for slot in obj.material_slots:
        if slot.material:
            set_active_bake_image(slot.material, image)
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 32
    bpy.context.scene.render.bake.margin = 12
    bpy.context.scene.render.bake.use_clear = True
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if bake_type == 'DIFFUSE':
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False
        bpy.context.scene.render.bake.use_pass_color = True
    bpy.ops.object.bake(type=bake_type)
    image.filepath_raw = str(filepath)
    image.save()


def main():
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
    merged, bake_collection = duplicate_and_join_lod0()
    unwrap_merged(merged)
    base = create_bake_image("DL_Bake_BaseColor")
    emissive = create_bake_image("DL_Bake_Emissive")
    normal = create_bake_image("DL_Bake_Normal")
    bake(merged, base, 'DIFFUSE', TEXTURE_DIR / "destiny_lord_basecolor.png")
    bake(merged, emissive, 'EMIT', TEXTURE_DIR / "destiny_lord_emissive.png")
    bake(merged, normal, 'NORMAL', TEXTURE_DIR / "destiny_lord_normal.png")
    # 烘焙副本仅为源资产，不参与最终游戏导出时可隐藏。
    bake_collection.hide_viewport = True
    bake_collection.hide_render = True
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print(f"命运之主贴图烘焙已完成：{OUTPUT}")


if __name__ == "__main__":
    main()

