from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


# 白夜馆 UI 资源生成脚本：生成事件背景与法令图标，避免依赖外部版权素材。
MOD_DIR = Path(__file__).resolve().parents[2]
ASSET_DIR = MOD_DIR / "assets" / "white_night_pavilion"
EVENT_DIR = MOD_DIR / "gfx" / "event_pictures"
EDICT_ICON_DIR = MOD_DIR / "gfx" / "interface" / "icons" / "edicts"
GENERATED_BACKGROUND = ASSET_DIR / "white_night_pavilion_generated_source.png"


def load_font(size, bold=False):
    """优先使用系统中文字体，缺失时退回 Pillow 默认字体。"""
    font_candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for font_path in font_candidates:
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default()


def draw_glow(draw, position, text, font, fill, glow_fill, radius=2):
    """绘制带柔光的文字，用于白夜馆 UI 的发光标题。"""
    x, y = position
    for offset in range(radius, 0, -1):
        for dx in range(-offset, offset + 1):
            for dy in range(-offset, offset + 1):
                if dx * dx + dy * dy <= offset * offset:
                    draw.text((x + dx, y + dy), text, font=font, fill=glow_fill)
    draw.text((x, y), text, font=font, fill=fill)


def rounded_rect(draw, box, radius, fill, outline=None, width=1):
    """兼容旧版 Pillow 的圆角矩形包装。"""
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def create_event_picture():
    """生成白夜馆主菜单事件背景：暗紫会客厅、柔光沙发、书堆与右侧菱形入口。"""
    width, height = 1024, 512

    # 优先使用绘图工具生成的白夜馆背景；裁成 Stellaris 事件图使用的 2:1 宽幅。
    if GENERATED_BACKGROUND.exists():
        source = Image.open(GENERATED_BACKGROUND).convert("RGBA")
        image = ImageOps.fit(
            source,
            (width, height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.58),
        )

        # Stellaris 事件窗口会在下半部叠加正文和选项框；这里预先压暗，避免角色衣摆与文字抢读。
        safe_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        safe_draw = ImageDraw.Draw(safe_overlay, "RGBA")
        for y in range(260, height):
            t = (y - 260) / (height - 260)
            alpha = int(18 + 118 * t)
            safe_draw.line((0, y, width, y), fill=(16, 8, 24, alpha))
        safe_draw.rounded_rectangle(
            (246, 292, 778, 504),
            radius=12,
            fill=(18, 8, 26, 74),
            outline=(122, 84, 138, 42),
            width=1,
        )
        image.alpha_composite(safe_overlay)

        EVENT_DIR.mkdir(parents=True, exist_ok=True)
        png_path = EVENT_DIR / "aemusa_white_night_pavilion.png"
        dds_path = EVENT_DIR / "aemusa_white_night_pavilion.dds"
        image.convert("RGB").save(png_path)
        image.convert("RGBA").save(dds_path)
        return png_path, dds_path

    rng = Random(20260701)
    image = Image.new("RGBA", (width, height), "#211528")
    draw = ImageDraw.Draw(image, "RGBA")

    # 背景使用暗紫室内渐变，贴近白夜馆的梦境会客厅氛围。
    for y in range(height):
        t = y / (height - 1)
        r = int(28 + 8 * t)
        g = int(18 + 6 * t)
        b = int(38 + 18 * t)
        draw.line((0, y, width, y), fill=(r, g, b, 255))

    # 后景窗帘与花纹：使用柔白竖向光带和卷草暗纹，避免直接复刻原图。
    curtain = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    curtain_draw = ImageDraw.Draw(curtain, "RGBA")
    curtain_draw.rectangle((226, 0, 790, 310), fill=(68, 58, 74, 170))
    for x in range(238, 790, 38):
        alpha = 55 + int(35 * (1 - abs(x - width / 2) / (width / 2)))
        curtain_draw.rectangle((x, 0, x + 18, 332), fill=(225, 216, 226, alpha))
    for x in range(260, 766, 74):
        for y in range(16, 304, 60):
            curtain_draw.arc((x, y, x + 58, y + 48), 90, 285, fill=(36, 25, 43, 80), width=2)
            curtain_draw.arc((x + 12, y + 4, x + 68, y + 52), 260, 80, fill=(118, 95, 124, 45), width=1)
    curtain = curtain.filter(ImageFilter.GaussianBlur(1.4))
    image.alpha_composite(curtain)

    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, 0, 128, height), fill=(18, 12, 25, 118))
    draw.rectangle((850, 0, width, height), fill=(25, 14, 31, 135))
    draw.rectangle((0, 0, width, height), outline=(86, 54, 98, 100), width=2)

    # 紫色长沙发主体，使用多层椭圆和高光模拟蓬松靠背。
    sofa = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sofa_draw = ImageDraw.Draw(sofa, "RGBA")
    sofa_draw.ellipse((226, 146, 786, 372), fill=(82, 58, 96, 230), outline=(55, 36, 66, 220), width=5)
    sofa_draw.rounded_rectangle((178, 224, 842, 448), radius=62, fill=(105, 77, 123, 240), outline=(50, 33, 60, 230), width=5)
    sofa_draw.rounded_rectangle((216, 204, 804, 418), radius=46, fill=(184, 160, 199, 220), outline=(96, 70, 111, 210), width=3)
    sofa_draw.rectangle((250, 300, 774, 444), fill=(188, 166, 205, 225))
    for x in range(262, 760, 54):
        sofa_draw.ellipse((x, 224, x + 48, 282), fill=(215, 198, 226, 72), outline=(246, 235, 250, 72), width=1)
        sofa_draw.ellipse((x + 16, 246, x + 26, 256), fill=(118, 83, 133, 150))
    sofa_draw.rounded_rectangle((132, 236, 306, 450), radius=48, fill=(101, 73, 119, 242), outline=(48, 32, 58, 230), width=4)
    sofa_draw.rounded_rectangle((718, 236, 892, 450), radius=48, fill=(101, 73, 119, 242), outline=(48, 32, 58, 230), width=4)
    sofa = sofa.filter(ImageFilter.GaussianBlur(0.6))
    image.alpha_composite(sofa)

    # 中央接待者剪影：只保留原创的抽象人物轮廓，不使用参考图角色素材。
    figure = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fig = ImageDraw.Draw(figure, "RGBA")
    fig.ellipse((468, 74, 550, 154), fill=(238, 231, 239, 236), outline=(106, 82, 118, 160), width=2)
    fig.rounded_rectangle((460, 136, 560, 286), radius=28, fill=(232, 226, 235, 238), outline=(86, 66, 95, 140), width=2)
    fig.polygon([(462, 182), (388, 398), (498, 430), (532, 252)], fill=(238, 232, 238, 226), outline=(70, 55, 78, 120))
    fig.polygon([(558, 184), (640, 404), (528, 430), (502, 252)], fill=(218, 210, 222, 225), outline=(70, 55, 78, 120))
    fig.line((490, 82, 436, 280), fill=(244, 238, 246, 235), width=12)
    fig.line((532, 84, 582, 292), fill=(244, 238, 246, 235), width=12)
    fig.line((430, 232, 612, 228), fill=(198, 169, 116, 230), width=5)
    fig.line((430, 232, 612, 228), fill=(70, 49, 42, 160), width=1)
    fig.ellipse((496, 112, 501, 117), fill=(175, 56, 77, 210))
    fig.ellipse((520, 112, 525, 117), fill=(175, 56, 77, 210))
    fig.line((505, 132, 520, 132), fill=(120, 88, 104, 118), width=1)
    fig.polygon([(548, 88), (584, 70), (570, 110)], fill=(190, 18, 37, 205), outline=(248, 82, 86, 92))
    fig.polygon([(548, 88), (590, 98), (560, 118)], fill=(158, 14, 32, 205), outline=(248, 82, 86, 92))
    fig.ellipse((500, 152, 522, 174), fill=(52, 42, 56, 220), outline=(224, 198, 120, 230), width=2)
    fig.line((511, 174, 511, 218), fill=(224, 198, 120, 180), width=2)
    figure = figure.filter(ImageFilter.GaussianBlur(0.25))
    image.alpha_composite(figure)
    draw = ImageDraw.Draw(image, "RGBA")

    # 左右书堆增强白夜馆室内陈设感。
    for base_x, direction in [(56, 1), (816, -1)]:
        for stack in range(4):
            x = base_x + direction * stack * 38
            y_base = 438 - stack * 20
            for i in range(rng.randint(4, 8)):
                y = y_base - i * 15
                w = rng.randint(56, 96)
                h = rng.randint(10, 15)
                shade = rng.choice([(58, 51, 68), (78, 69, 82), (46, 42, 56), (92, 82, 86)])
                x1 = min(x, x + direction * w)
                x2 = max(x, x + direction * w)
                rounded_rect(draw, (x1, y, x2, y + h), 2, fill=(*shade, 210), outline=(22, 18, 28, 135), width=1)
                draw.line((x1 + 6, y + 3, x2 - 6, y + 3), fill=(186, 174, 165, 80), width=1)

    # 红色蝶形光片是白夜馆风格的重要点缀，这里用几何碎片原创绘制。
    def red_shard(cx, cy, scale):
        points = [
            (cx, cy),
            (cx - 8 * scale, cy - 14 * scale),
            (cx + 1 * scale, cy - 8 * scale),
            (cx + 10 * scale, cy - 18 * scale),
            (cx + 5 * scale, cy),
            (cx + 12 * scale, cy + 12 * scale),
            (cx + 1 * scale, cy + 8 * scale),
            (cx - 9 * scale, cy + 14 * scale),
        ]
        draw.polygon(points, fill=(192, 16, 33, 218), outline=(255, 76, 80, 118))

    for cx, cy, scale in [(178, 276, 1.0), (350, 198, 0.75), (594, 142, 0.72), (662, 292, 0.82), (890, 202, 0.66), (512, 328, 0.62)]:
        red_shard(cx, cy, scale)

    # 右侧竖排菱形入口：呼应参考图的层级，但换成模组自己的菜单语义。
    menu_font = load_font(34, bold=True)
    for i, label in enumerate(["通讯", "名册", "回忆"]):
        cy = 145 + i * 104
        diamond = [(880, cy), (924, cy - 35), (968, cy), (924, cy + 35)]
        draw.polygon(diamond, fill=(72, 47, 82, 84), outline=(176, 129, 184, 125))
        draw.line((890, cy, 958, cy), fill=(232, 184, 174, 70), width=1)
        draw_glow(draw, (902, cy - 22), label, menu_font, (255, 236, 219, 230), (255, 180, 171, 72), radius=1)
        draw.line((976, cy - 22, 976, cy + 22), fill=(244, 204, 202, 112), width=2)

    # 画面边缘加暗角，压住事件窗口底部按钮区域。
    vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    vig = ImageDraw.Draw(vignette, "RGBA")
    vig.rectangle((0, 414, width, height), fill=(10, 6, 14, 108))
    vig.rectangle((0, 0, width, 72), fill=(12, 6, 16, 70))
    image.alpha_composite(vignette)
    draw = ImageDraw.Draw(image, "RGBA")

    # 左上角小型导航符号，保留游戏 UI 的可交互入口感。
    draw.rectangle((62, 0, 178, 34), fill=(14, 10, 20, 150))
    draw.line((118, 8, 104, 18), fill=(111, 238, 229, 220), width=4)
    draw.line((104, 18, 118, 28), fill=(111, 238, 229, 220), width=4)
    draw.rectangle((150, 10, 156, 26), fill=(111, 238, 229, 190))
    draw.rectangle((160, 5, 166, 26), fill=(111, 238, 229, 160))
    draw.rectangle((170, 13, 176, 26), fill=(111, 238, 229, 130))

    EVENT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = EVENT_DIR / "aemusa_white_night_pavilion.png"
    dds_path = EVENT_DIR / "aemusa_white_night_pavilion.dds"
    image.convert("RGB").save(png_path)
    image.convert("RGBA").save(dds_path)
    return png_path, dds_path


def create_edict_icon():
    """生成白夜馆法令图标：法令列表按原始尺寸绘制，因此使用透明底 32px 小图标。"""
    size = 32
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")

    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    glow_draw.ellipse((4, 5, 28, 29), fill=(219, 195, 232, 92))
    glow = glow.filter(ImageFilter.GaussianBlur(2))
    image.alpha_composite(glow)
    draw = ImageDraw.Draw(image, "RGBA")

    draw.polygon([(16, 3), (29, 16), (16, 29), (3, 16)], fill=(70, 44, 84, 118), outline=(183, 132, 184, 210))
    font = load_font(20, bold=True)
    draw_glow(draw, (6, 5), "白", font, (255, 244, 235, 255), (255, 218, 208, 125), radius=1)
    draw.polygon([(25, 5), (21, 13), (29, 11)], fill=(199, 20, 39, 230))
    draw.polygon([(6, 24), (12, 20), (10, 30)], fill=(199, 20, 39, 220))
    draw.line((8, 28, 24, 28), fill=(243, 218, 198, 170), width=1)

    EDICT_ICON_DIR.mkdir(parents=True, exist_ok=True)
    png_path = EDICT_ICON_DIR / "edict_white_night_pavilion.png"
    dds_path = EDICT_ICON_DIR / "edict_white_night_pavilion.dds"
    image.convert("RGBA").save(png_path)
    image.convert("RGBA").save(dds_path)
    return png_path, dds_path


if __name__ == "__main__":
    event_png, event_dds = create_event_picture()
    icon_png, icon_dds = create_edict_icon()
    print(f"event_png={event_png}")
    print(f"event_dds={event_dds}")
    print(f"icon_png={icon_png}")
    print(f"icon_dds={icon_dds}")
