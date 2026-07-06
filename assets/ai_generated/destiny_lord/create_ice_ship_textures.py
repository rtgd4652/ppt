# 为命运之主生成可重复平铺的冰蓝未来科技舰体 DDS 贴图。
# 贴图不依赖单一 UV 图集，因此可安全用于所有独立舰体部件。
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict")
TARGET_DIR = ASSET_DIR / "mod" / "gfx" / "models" / "ships" / "destiny_lord"
SIZE = 1024
CELL = 128
DETAIL_CELL = 64


def draw_glow_line(base, glow, coords, color, glow_color, width=3, glow_width=10):
    ImageDraw.Draw(glow).line(coords, fill=glow_color, width=glow_width)
    ImageDraw.Draw(base).line(coords, fill=color, width=width)


def draw_corner_marks(draw, x, y, bright, mid):
    draw.line((x + 18, y + 18, x + 34, y + 18), fill=bright, width=1)
    draw.line((x + 18, y + 18, x + 18, y + 34), fill=bright, width=1)
    draw.line((x + CELL - 18, y + CELL - 18, x + CELL - 34, y + CELL - 18), fill=mid, width=1)
    draw.line((x + CELL - 18, y + CELL - 18, x + CELL - 18, y + CELL - 34), fill=mid, width=1)


def create_diffuse():
    """生成深靛装甲、冰蓝命运线和少量金色裁决标记。"""
    image = Image.new("RGB", (SIZE, SIZE), (42, 54, 72))
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    for y in range(0, SIZE, CELL):
        for x in range(0, SIZE, CELL):
            shade = 7 if ((x // CELL) + (y // CELL)) % 2 == 0 else -6
            blue_shift = 4 if (x // CELL) % 3 == 0 else 0
            color = (max(0, 50 + shade), max(0, 62 + shade), max(0, 82 + shade + blue_shift))
            draw.rectangle((x + 5, y + 5, x + CELL - 5, y + CELL - 5), fill=color)
            if ((x // CELL) + (y // CELL)) % 4 == 1:
                draw.rectangle((x + 20, y + 20, x + CELL - 24, y + CELL - 24), outline=(58, 72, 94), width=1)

    for value in range(0, SIZE + 1, CELL):
        draw_glow_line(image, glow, (value, 0, value, SIZE), (45, 78, 108), (50, 140, 210, 6), width=1, glow_width=3)
        draw_glow_line(image, glow, (0, value, SIZE, value), (44, 74, 104), (45, 132, 198, 5), width=1, glow_width=3)
    for value in range(DETAIL_CELL, SIZE, DETAIL_CELL):
        if value % CELL:
            draw.line((value, 0, value, SIZE), fill=(38, 50, 68), width=1)
            draw.line((0, value, SIZE, value), fill=(38, 50, 68), width=1)

    for y in range(0, SIZE, CELL):
        for x in range(0, SIZE, CELL):
            draw_corner_marks(draw, x, y, (86, 152, 206), (66, 116, 170))
            if ((x // CELL) + (y // CELL)) % 5 == 0:
                draw.line((x + 40, y + CELL - 28, x + 62, y + CELL - 28), fill=(132, 102, 70), width=1)
                draw.line((x + 62, y + CELL - 28, x + 74, y + CELL - 40), fill=(164, 132, 88), width=1)
            if ((x // CELL) * 2 + (y // CELL)) % 4 == 2:
                draw.line((x + 78, y + 26, x + 98, y + 26), fill=(72, 136, 194), width=1)
                draw.line((x + 26, y + 80, x + 26, y + 100), fill=(66, 128, 186), width=1)
            draw.line((x + 30, y + 62, x + 58, y + 62), fill=(48, 68, 88), width=1)
            draw.line((x + 70, y + 88, x + 100, y + 88), fill=(48, 68, 88), width=1)

    # 命运环识别纹样：在平铺贴图中加入圆弧和节点，实际落到舰体上会形成“观测/裁决”感。
    for cx, cy in ((CELL, CELL), (CELL * 5, CELL * 3), (CELL * 3, CELL * 6), (CELL * 7, CELL * 7)):
        draw.line((cx - 36, cy - 18, cx - 10, cy - 18), fill=(118, 196, 238), width=2)
        draw.line((cx - 36, cy - 18, cx - 36, cy + 8), fill=(96, 172, 224), width=2)
        draw.line((cx + 12, cy + 20, cx + 34, cy + 20), fill=(74, 142, 202), width=1)
        draw.line((cx + 34, cy - 2, cx + 34, cy + 20), fill=(74, 142, 202), width=1)
        draw.rectangle((cx - 4, cy - 4, cx + 4, cy + 4), outline=(150, 226, 248), width=1)
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.line((cx - 36, cy - 18, cx - 10, cy - 18), fill=(86, 206, 250, 48), width=5)
        glow_draw.line((cx - 36, cy - 18, cx - 36, cy + 8), fill=(86, 206, 250, 42), width=5)

    blurred = glow.filter(ImageFilter.GaussianBlur(5))
    image = Image.alpha_composite(image.convert("RGBA"), blurred).convert("RGB")
    return image


def create_normal():
    """生成低强度面板法线，并提高线条自发光通道。"""
    image = Image.new("RGBA", (SIZE, SIZE), (128, 128, 0, 138))
    draw = ImageDraw.Draw(image)
    for value in range(0, SIZE + 1, CELL):
        draw.line((value, 0, value, SIZE), fill=(138, 128, 62, 92), width=2)
        draw.line((0, value, SIZE, value), fill=(128, 138, 62, 92), width=2)
    for y in range(0, SIZE, CELL):
        for x in range(0, SIZE, CELL):
            draw.line((x + 18, y + 18, x + 42, y + 18), fill=(148, 128, 82, 118), width=2)
            draw.line((x + 18, y + 18, x + 18, y + 42), fill=(128, 148, 82, 118), width=2)
    return image


def create_specular():
    """生成金属/粗糙度参数：装甲柔和，命运线与节点更亮。"""
    image = Image.new("RGBA", (SIZE, SIZE), (0, 92, 150, 124))
    draw = ImageDraw.Draw(image)
    for value in range(0, SIZE + 1, CELL):
        draw.line((value, 0, value, SIZE), fill=(0, 150, 220, 18), width=2)
        draw.line((0, value, SIZE, value), fill=(0, 140, 208, 18), width=2)
    for cx, cy in ((CELL, CELL), (CELL * 5, CELL * 3), (CELL * 3, CELL * 6), (CELL * 7, CELL * 7)):
        draw.line((cx - 36, cy - 18, cx - 10, cy - 18), fill=(0, 224, 255, 38), width=2)
        draw.line((cx - 36, cy - 18, cx - 36, cy + 8), fill=(0, 210, 255, 34), width=2)
        draw.rectangle((cx - 4, cy - 4, cx + 4, cy + 4), outline=(0, 235, 255, 42), width=1)
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


