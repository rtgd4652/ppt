# 为命运之主生成可重复平铺的冰蓝未来科技舰体 DDS 贴图。
# 贴图不依赖单一 UV 图集，因此可安全用于所有独立舰体部件。
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict")
TARGET_DIR = ASSET_DIR / "gfx" / "models" / "ships" / "destiny_lord"
SIZE = 1024
CELL = 128


def draw_glow_line(base, glow, coords, color, glow_color, width=3, glow_width=10):
    ImageDraw.Draw(glow).line(coords, fill=glow_color, width=glow_width)
    ImageDraw.Draw(base).line(coords, fill=color, width=width)


def draw_corner_marks(draw, x, y, bright, mid):
    draw.line((x + 12, y + 12, x + 50, y + 12), fill=bright, width=4)
    draw.line((x + 12, y + 12, x + 12, y + 50), fill=bright, width=4)
    draw.line((x + CELL - 12, y + CELL - 12, x + CELL - 50, y + CELL - 12), fill=mid, width=3)
    draw.line((x + CELL - 12, y + CELL - 12, x + CELL - 12, y + CELL - 50), fill=mid, width=3)


def create_diffuse():
    """生成深靛装甲、冰蓝命运线和少量金色裁决标记。"""
    image = Image.new("RGB", (SIZE, SIZE), (46, 57, 74))
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    for y in range(0, SIZE, CELL):
        for x in range(0, SIZE, CELL):
            shade = 10 if ((x // CELL) + (y // CELL)) % 2 == 0 else -8
            blue_shift = 6 if (x // CELL) % 3 == 0 else 0
            color = (max(0, 54 + shade), max(0, 66 + shade), max(0, 88 + shade + blue_shift))
            draw.rectangle((x + 5, y + 5, x + CELL - 5, y + CELL - 5), fill=color)
            if ((x // CELL) + (y // CELL)) % 4 == 1:
                draw.rectangle((x + 18, y + 18, x + CELL - 22, y + CELL - 22), outline=(68, 82, 104), width=2)

    for value in range(0, SIZE + 1, CELL):
        draw_glow_line(image, glow, (value, 0, value, SIZE), (84, 148, 206), (62, 170, 238, 38), width=3, glow_width=8)
        draw_glow_line(image, glow, (0, value, SIZE, value), (76, 136, 196), (50, 156, 226, 34), width=3, glow_width=8)

    for y in range(0, SIZE, CELL):
        for x in range(0, SIZE, CELL):
            draw_corner_marks(draw, x, y, (146, 208, 238), (92, 166, 218))
            if ((x // CELL) + (y // CELL)) % 5 == 0:
                draw.line((x + 36, y + CELL - 24, x + 64, y + CELL - 24), fill=(158, 118, 78), width=2)
                draw.line((x + 64, y + CELL - 24, x + 78, y + CELL - 38), fill=(196, 156, 102), width=2)
            if ((x // CELL) * 2 + (y // CELL)) % 4 == 2:
                draw.line((x + 72, y + 24, x + 104, y + 24), fill=(94, 170, 226), width=3)
                draw.line((x + 24, y + 74, x + 24, y + 104), fill=(86, 158, 216), width=3)

    # 命运环识别纹样：在平铺贴图中加入圆弧和节点，实际落到舰体上会形成“观测/裁决”感。
    for cx, cy in ((CELL, CELL), (CELL * 5, CELL * 3), (CELL * 3, CELL * 6), (CELL * 7, CELL * 7)):
        bbox = (cx - 38, cy - 38, cx + 38, cy + 38)
        draw.arc(bbox, start=18, end=154, fill=(132, 206, 246), width=4)
        draw.arc(bbox, start=206, end=322, fill=(62, 136, 206), width=3)
        draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(184, 232, 250))
        ImageDraw.Draw(glow).arc((cx - 44, cy - 44, cx + 44, cy + 44), start=18, end=154, fill=(82, 198, 246, 76), width=10)

    blurred = glow.filter(ImageFilter.GaussianBlur(5))
    image = Image.alpha_composite(image.convert("RGBA"), blurred).convert("RGB")
    return image


def create_normal():
    """生成低强度面板法线，并提高线条自发光通道。"""
    image = Image.new("RGBA", (SIZE, SIZE), (128, 128, 0, 138))
    draw = ImageDraw.Draw(image)
    for value in range(0, SIZE + 1, CELL):
        draw.line((value, 0, value, SIZE), fill=(146, 128, 50, 142), width=3)
        draw.line((0, value, SIZE, value), fill=(128, 146, 50, 142), width=3)
    for y in range(0, SIZE, CELL):
        for x in range(0, SIZE, CELL):
            draw.line((x + 12, y + 12, x + 50, y + 12), fill=(158, 128, 76, 164), width=3)
            draw.line((x + 12, y + 12, x + 12, y + 50), fill=(128, 158, 76, 164), width=3)
    return image


def create_specular():
    """生成金属/粗糙度参数：装甲柔和，命运线与节点更亮。"""
    image = Image.new("RGBA", (SIZE, SIZE), (0, 92, 150, 124))
    draw = ImageDraw.Draw(image)
    for value in range(0, SIZE + 1, CELL):
        draw.line((value, 0, value, SIZE), fill=(0, 178, 238, 42), width=4)
        draw.line((0, value, SIZE, value), fill=(0, 166, 228, 40), width=4)
    for cx, cy in ((CELL, CELL), (CELL * 5, CELL * 3), (CELL * 3, CELL * 6), (CELL * 7, CELL * 7)):
        draw.arc((cx - 38, cy - 38, cx + 38, cy + 38), start=18, end=154, fill=(0, 230, 255, 64), width=5)
        draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(0, 240, 255, 70))
    return image


def main():
    """写出与群星资产表一致的 DXT 压缩贴图文件。"""
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    diffuse = create_diffuse()
    normal = create_normal()
    specular = create_specular()
    diffuse.save(TARGET_DIR / "destiny_lord_basecolor.dds", format="DDS", pixel_format="DXT1")
    normal.save(TARGET_DIR / "destiny_lord_normal.dds", format="DDS", pixel_format="DXT5")
    specular.save(TARGET_DIR / "destiny_lord_specular.dds", format="DDS", pixel_format="DXT5")
    diffuse.save(TARGET_DIR / "destiny_lord_basecolor_preview.png")
    normal.save(TARGET_DIR / "destiny_lord_normal_preview.png")
    specular.save(TARGET_DIR / "destiny_lord_specular_preview.png")
    print(f"命运之主舰体贴图已生成：{TARGET_DIR}")


if __name__ == "__main__":
    main()
