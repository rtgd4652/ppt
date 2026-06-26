# 为命运之主生成可重复平铺的冰蓝未来科技舰体 DDS 贴图。
# 贴图不依赖单一 UV 图集，因此可安全用于所有独立舰体部件。
from pathlib import Path
from PIL import Image, ImageDraw


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict")
TARGET_DIR = ASSET_DIR / "gfx" / "models" / "ships" / "destiny_lord"
SIZE = 1024
CELL = 128


def create_diffuse():
    """生成银蓝深靛金属板与冰晶能量线的漫反射贴图。"""
    # 提高中间亮度，使巨舰在星系远景与暗色星云中仍保持清晰轮廓。
    image = Image.new("RGB", (SIZE, SIZE), (80, 110, 160))
    draw = ImageDraw.Draw(image)

    # 交错的深靛金属装甲分区，避免舰体成为单调纯色。
    for y in range(0, SIZE, CELL):
        for x in range(0, SIZE, CELL):
            shade = 14 if ((x // CELL) + (y // CELL)) % 2 == 0 else -4
            color = (max(0, 80 + shade), max(0, 110 + shade), max(0, 160 + shade))
            draw.rectangle((x + 4, y + 4, x + CELL - 4, y + CELL - 4), fill=color)

    # 冰蓝细线与斜向切角形成未来科技结构感。
    for value in range(0, SIZE + 1, CELL):
        draw.line((value, 0, value, SIZE), fill=(126, 168, 210), width=3)
        draw.line((0, value, SIZE, value), fill=(111, 152, 196), width=3)
    for y in range(0, SIZE, CELL):
        for x in range(0, SIZE, CELL):
            draw.line((x + 10, y + 10, x + 34, y + 10), fill=(175, 210, 235), width=3)
            draw.line((x + 10, y + 10, x + 10, y + 34), fill=(175, 210, 235), width=3)
            draw.line((x + CELL - 10, y + CELL - 10, x + CELL - 34, y + CELL - 10), fill=(109, 154, 205), width=3)
            draw.line((x + CELL - 10, y + CELL - 10, x + CELL - 10, y + CELL - 34), fill=(109, 154, 205), width=3)
    return image


def create_normal():
    """生成低强度面板法线；仅让面板线使用安全的低值自发光通道。"""
    image = Image.new("RGBA", (SIZE, SIZE), (128, 128, 0, 128))
    draw = ImageDraw.Draw(image)
    for value in range(0, SIZE + 1, CELL):
        # B=18 只提供轻微圣辉，不会重现整舰高强度红色发光。
        draw.line((value, 0, value, SIZE), fill=(145, 128, 18, 128), width=2)
        draw.line((0, value, SIZE, value), fill=(128, 145, 18, 128), width=2)
    return image


def create_specular():
    """生成金属度与粗糙度参数，面板线略亮、装甲面保持柔和反射。"""
    image = Image.new("RGBA", (SIZE, SIZE), (0, 92, 156, 82))
    draw = ImageDraw.Draw(image)
    for value in range(0, SIZE + 1, CELL):
        draw.line((value, 0, value, SIZE), fill=(0, 150, 220, 58), width=3)
        draw.line((0, value, SIZE, value), fill=(0, 150, 220, 58), width=3)
    return image


def main():
    """写出与群星资产表一致的 DXT 压缩贴图文件。"""
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    create_diffuse().save(TARGET_DIR / "destiny_lord_basecolor.dds", format="DDS", pixel_format="DXT1")
    create_normal().save(TARGET_DIR / "destiny_lord_normal.dds", format="DDS", pixel_format="DXT5")
    create_specular().save(TARGET_DIR / "destiny_lord_specular.dds", format="DDS", pixel_format="DXT5")
    print(f"冰晶圣域舰体贴图已生成：{TARGET_DIR}")


if __name__ == "__main__":
    main()
