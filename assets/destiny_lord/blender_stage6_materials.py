# 命运之主第六阶段：建立正式预览材质与渲染设置。
# 现阶段采用程序化节点材质；后续可基于已展开 UV 烘焙为 BaseColor、Emissive 和 Normal 贴图。

import bpy
from pathlib import Path


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\destiny_lord")
OUTPUT = ASSET_DIR / "destiny_lord_stage6_materials.blend"


def clear_nodes(material):
    """清理旧节点，避免前序占位材质干扰正式预览。"""
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    return nodes, material.node_tree.links


def create_hull_material():
    """银白舰体：金属装甲与冷色细微变化。"""
    material = bpy.data.materials.get("DL2_Hull_Silver")
    nodes, links = clear_nodes(material)
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = 5.5
    noise.inputs["Detail"].default_value = 3.0
    ramp.color_ramp.elements[0].color = (0.13, 0.18, 0.28, 1.0)
    ramp.color_ramp.elements[1].color = (0.62, 0.73, 0.92, 1.0)
    shader.inputs["Metallic"].default_value = 0.88
    shader.inputs["Roughness"].default_value = 0.26
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.12
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])


def create_dark_armor_material():
    """深靛装甲：用于舰桥、装甲台阶与结构缝隙。"""
    material = bpy.data.materials.get("DL2_Armor_Indigo")
    nodes, links = clear_nodes(material)
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (0.008, 0.018, 0.07, 1.0)
    shader.inputs["Metallic"].default_value = 0.75
    shader.inputs["Roughness"].default_value = 0.20
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])


def create_emissive_material(name, base_color, emission_color, strength):
    """冰蓝能量与红金主炮的自发光材质。"""
    material = bpy.data.materials.get(name)
    nodes, links = clear_nodes(material)
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (*base_color, 1.0)
    shader.inputs["Metallic"].default_value = 0.55
    shader.inputs["Roughness"].default_value = 0.18
    shader.inputs["Emission Color"].default_value = (*emission_color, 1.0)
    shader.inputs["Emission Strength"].default_value = strength
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])


def configure_render():
    """设置深空背景、Bloom 与高质量 EEVEE 预览。"""
    scene = bpy.context.scene
    # 当前安装的 Blender 5.1 使用 BLENDER_EEVEE 枚举名称。
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 60
    scene.render.image_settings.file_format = 'PNG'
    scene.world.color = (0.001, 0.003, 0.012)
    scene.view_settings.look = 'AgX - Medium High Contrast'


def main():
    create_hull_material()
    create_dark_armor_material()
    create_emissive_material("DL2_IceBlue", (0.03, 0.14, 0.65), (0.02, 0.42, 1.0), 8.0)
    create_emissive_material("DL2_Judgement_Red", (0.42, 0.015, 0.006), (1.0, 0.035, 0.005), 7.0)
    configure_render()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print(f"命运之主第六阶段材质文件已保存：{OUTPUT}")


if __name__ == "__main__":
    main()
