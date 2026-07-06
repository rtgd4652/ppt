# 将命运之主烘焙贴图转换为 Stellaris 可读取的 DDS（DXT5）格式。
# 需要使用已安装 Pillow 的 Blender 内置 Python 运行本文件。
from pathlib import Path
from PIL import Image


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict")
SOURCE_DIR = ASSET_DIR / "assets" / "ai_generated" / "destiny_lord" / "textures"
TARGET_DIR = ASSET_DIR / "mod" / "gfx" / "models" / "ships" / "destiny_lord"


def create_flat_ship_textures(size):
    """创建不依赖 UV 图集的稳定船体贴图，避免原始 UV 与烘焙图集不一致造成碎片化。"""
    # 群星舰船漫反射通常使用 DXT1；银蓝主色适配冰晶未来科技风格。
    diffuse = Image.new("RGB", size, (142, 170, 210))
    # PdxMeshShip 的法线贴图：RG 为平面法线、B 保持低值防止误触发高强度自发光、A 为材质遮罩。
    normal = Image.new("RGBA", size, (128, 128, 0, 128))
    # R 为保留遮罩、G 为高光强度、B 为金属度、A 为粗糙度参数。
    specular = Image.new("RGBA", size, (0, 100, 170, 72))
    return diffuse, normal, specular


def main():
    """输出与 _destiny_lord_meshes.gfx 中名称完全一致的三张 DDS 贴图。"""
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    # 仍以原始烘焙图尺寸为输出尺寸，但运行时使用稳定的平铺材质。
    base_source = SOURCE_DIR / "destiny_lord_basecolor.png"
    diffuse, normal, specular = create_flat_ship_textures(Image.open(base_source).size)
    diffuse.save(TARGET_DIR / "destiny_lord_basecolor.dds", format="DDS", pixel_format="DXT1")
    normal.save(TARGET_DIR / "destiny_lord_normal.dds", format="DDS", pixel_format="DXT5")
    specular.save(TARGET_DIR / "destiny_lord_specular.dds", format="DDS", pixel_format="DXT5")
    print(f"DDS 贴图已生成：{TARGET_DIR}")


if __name__ == "__main__":
    main()


