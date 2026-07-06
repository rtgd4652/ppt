from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


# 白夜馆 UI 资源生成脚本：生成事件背景与法令图标，避免依赖外部版权素材。
MOD_DIR = Path(__file__).resolve().parents[2]
ASSET_DIR = MOD_DIR / "assets" / "white_night_pavilion"
EVENT_DIR = MOD_DIR / "gfx" / "event_pictures"
EDICT_ICON_DIR = MOD_DIR / "gfx" / "interface" / "icons" / "edicts"
GENERATED_BACKGROUND = ASSET_DIR / "white_night_pavilion_generated_source.png"
ICON_DIR = ASSET_DIR / "faction_icons"
ICON_CACHE = {}

FACTION_PAGES = {
    "central_church": {
        "title": "中央庭 / 圣星教会",
        "key": "GFX_evt_aemusa_white_night_faction_central_church",
        "file": "aemusa_white_night_faction_central_church_clean",
        "accent": (142, 238, 214),
        "glyph": "court",
        "members": [("爱缪莎", "中央庭七人众", "命运"), ("赛斯", "圣星神官", "已接入"), ("空位", "资料待整理", "待定")],
    },
    "memory_palace": {
        "title": "主线剧情 / 记忆殿堂",
        "key": "GFX_evt_aemusa_white_night_faction_memory_palace",
        "file": "aemusa_white_night_faction_memory_palace_clean",
        "accent": (190, 148, 244),
        "glyph": "memory",
        "members": [("幽桐", "神弓・甘狄拔", "待整理"), ("拉比", "怪兽・阿米特", "待整理"), ("空位", "资料待整理", "待定")],
    },
    "white_night_gap": {
        "title": "白夜馆 / 记忆隙间",
        "key": "GFX_evt_aemusa_white_night_faction_white_night_gap",
        "file": "aemusa_white_night_faction_white_night_gap_clean",
        "accent": (235, 196, 238),
        "glyph": "white_night",
        "members": [("格蕾莎", "神符・安卡", "待整理"), ("空位", "记忆隙间", "待定"), ("空位", "白夜馆档案", "待定")],
    },
    "collaboration": {
        "title": "联动来客",
        "key": "GFX_evt_aemusa_white_night_faction_collaboration",
        "file": "aemusa_white_night_faction_collaboration_clean",
        "accent": (244, 122, 92),
        "glyph": "linkage",
        "members": [("冈部伦太郎", "世界线观测", "待整理"), ("空位", "联动档案", "待定"), ("空位", "联动档案", "待定")],
    },
}


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


def load_faction_icon(glyph, size=86):
    """读取绘图工具生成的势力图标；缺失时返回空值，由旧几何图形兜底。"""
    cache_key = (glyph, size)
    if cache_key in ICON_CACHE:
        return ICON_CACHE[cache_key]

    icon_path = ICON_DIR / f"{glyph}.png"
    if not icon_path.exists():
        ICON_CACHE[cache_key] = None
        return None

    icon = Image.open(icon_path).convert("RGBA")
    icon.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(icon, ((size - icon.width) // 2, (size - icon.height) // 2))
    ICON_CACHE[cache_key] = canvas
    return canvas


def draw_faction_badge(image, center, label, accent, glyph, icon_size=82, show_label=True):
    """绘制原创势力徽记：借鉴阵营环绕版式，但保持白夜馆暗紫灯箱风格。"""
    cx, cy = center
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    font = load_font(15, bold=True)
    small_font = load_font(11, bold=True)
    diamond = [(cx, cy - 31), (cx + 43, cy), (cx, cy + 31), (cx - 43, cy)]
    soft = (*accent, 54)
    bright = (*accent, 145)

    draw.polygon(diamond, fill=(25, 16, 34, 112), outline=bright)
    draw.line((cx - 31, cy, cx + 31, cy), fill=soft, width=1)
    draw.line((cx, cy - 23, cx, cy + 23), fill=soft, width=1)
    draw.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), outline=(*accent, 96), width=2)

    # 优先贴入绘图工具生成的势力图标，避免程序几何图形显得过于抽象。
    icon = load_faction_icon(glyph, size=icon_size)
    if icon is not None:
        layer.alpha_composite(icon, (cx - icon.width // 2, cy - icon.height // 2))
        if show_label:
            text_w = draw.textlength(label, font=small_font)
            draw.text((cx - text_w / 2, cy + 33), label, font=small_font, fill=(246, 226, 234, 190))
        image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.15)))
        return

    if glyph == "court":
        draw.line((cx, cy - 16, cx, cy + 14), fill=bright, width=3)
        draw.line((cx - 15, cy - 4, cx + 15, cy - 4), fill=bright, width=3)
        draw.polygon([(cx, cy - 22), (cx + 7, cy - 8), (cx - 7, cy - 8)], fill=bright)
    elif glyph == "church":
        draw.ellipse((cx - 12, cy - 18, cx + 12, cy + 18), outline=bright, width=3)
        draw.line((cx, cy - 20, cx, cy + 20), fill=bright, width=2)
        draw.line((cx - 13, cy, cx + 13, cy), fill=bright, width=2)
    elif glyph == "school":
        draw.polygon([(cx - 19, cy - 2), (cx, cy - 18), (cx + 19, cy - 2), (cx, cy + 14)], outline=bright, fill=None)
        draw.line((cx - 12, cy + 3, cx + 12, cy + 3), fill=bright, width=2)
        draw.line((cx, cy - 18, cx, cy + 14), fill=bright, width=2)
    elif glyph == "old_street":
        draw.arc((cx - 20, cy - 20, cx + 20, cy + 20), 200, 340, fill=bright, width=3)
        draw.line((cx - 16, cy - 4, cx + 16, cy - 4), fill=bright, width=3)
        draw.line((cx - 10, cy - 4, cx - 10, cy + 16), fill=bright, width=2)
        draw.line((cx + 10, cy - 4, cx + 10, cy + 16), fill=bright, width=2)
    elif glyph == "harbor":
        draw.arc((cx - 20, cy - 9, cx + 20, cy + 23), 180, 360, fill=bright, width=3)
        draw.line((cx, cy - 20, cx, cy + 17), fill=bright, width=3)
        draw.line((cx - 12, cy - 8, cx + 12, cy - 8), fill=bright, width=3)
        draw.line((cx - 18, cy + 10, cx + 18, cy + 10), fill=soft, width=2)
    elif glyph == "white_night":
        draw.text((cx - 12, cy - 18), "白", font=font, fill=bright)
        draw.polygon([(cx + 13, cy - 14), (cx + 23, cy - 6), (cx + 15, cy - 2)], fill=(198, 24, 42, 160))
        draw.polygon([(cx - 22, cy + 15), (cx - 10, cy + 8), (cx - 13, cy + 22)], fill=(198, 24, 42, 150))
    elif glyph == "memory":
        draw.rectangle((cx - 14, cy - 16, cx + 14, cy + 18), outline=bright, width=3)
        draw.line((cx - 8, cy - 7, cx + 8, cy - 7), fill=bright, width=2)
        draw.line((cx - 8, cy + 2, cx + 8, cy + 2), fill=bright, width=2)
        draw.line((cx - 8, cy + 11, cx + 5, cy + 11), fill=bright, width=2)
    elif glyph == "linkage":
        draw.ellipse((cx - 20, cy - 12, cx + 2, cy + 10), outline=bright, width=3)
        draw.ellipse((cx - 2, cy - 10, cx + 20, cy + 12), outline=bright, width=3)
        draw.line((cx - 8, cy + 8, cx + 8, cy - 8), fill=bright, width=2)

    text_w = draw.textlength(label, font=small_font)
    draw.text((cx - text_w / 2, cy + 33), label, font=small_font, fill=(246, 226, 234, 190))
    image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.15)))


def draw_faction_ring(image):
    """将游戏势力分类徽记围绕接待者分布在左右上下。"""
    factions = [
        ((422, 76), "中央庭", (142, 238, 214), "court"),
        ((606, 76), "圣星", (210, 188, 96), "church"),
        ((336, 154), "高校", (120, 196, 255), "school"),
        ((688, 154), "古街", (230, 106, 122), "old_street"),
        ((344, 246), "海湾", (104, 218, 176), "harbor"),
        ((680, 246), "白夜", (235, 196, 238), "white_night"),
        ((512, 252), "记忆", (190, 148, 244), "memory"),
        ((512, 52), "联动", (244, 122, 92), "linkage"),
    ]
    for center, label, accent, glyph in factions:
        draw_faction_badge(image, center, label, accent, glyph)


def load_white_night_base(width=1024, height=512):
    """读取绘图工具生成的白夜馆背景，并裁成 Stellaris 事件图比例。"""
    if GENERATED_BACKGROUND.exists():
        source = Image.open(GENERATED_BACKGROUND).convert("RGBA")
        return ImageOps.fit(
            source,
            (width, height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.58),
        )
    return Image.new("RGBA", (width, height), "#211528")


def apply_event_safe_overlay(image):
    """压暗事件窗口文字区，保证 Stellaris 事件正文可读。"""
    width, height = image.size
    safe_overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
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


def draw_character_card(draw, box, name, subtitle, status, accent):
    """绘制势力详情页中的角色卡。"""
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=6, fill=(18, 12, 28, 142), outline=(*accent, 155), width=2)
    draw.rounded_rectangle((x1 + 7, y1 + 7, x2 - 7, y2 - 34), radius=5, fill=(54, 38, 66, 108), outline=(255, 236, 246, 58), width=1)
    avatar_cx = (x1 + x2) // 2
    avatar_cy = y1 + 48
    draw.ellipse((avatar_cx - 24, avatar_cy - 24, avatar_cx + 24, avatar_cy + 24), fill=(236, 226, 240, 158), outline=(*accent, 140), width=2)
    draw.line((avatar_cx - 17, avatar_cy + 1, avatar_cx + 17, avatar_cy + 1), fill=(*accent, 124), width=2)
    draw.line((avatar_cx, avatar_cy - 17, avatar_cx, avatar_cy + 17), fill=(*accent, 94), width=2)
    font = load_font(17, bold=True)
    small = load_font(11, bold=False)
    status_font = load_font(10, bold=True)
    name_w = draw.textlength(name, font=font)
    draw.text((avatar_cx - name_w / 2, y2 - 31), name, font=font, fill=(255, 244, 236, 232))
    subtitle_w = draw.textlength(subtitle, font=small)
    draw.text((avatar_cx - subtitle_w / 2, y2 - 12), subtitle, font=small, fill=(193, 238, 224, 200))
    draw.rounded_rectangle((x2 - 48, y1 + 8, x2 - 8, y1 + 23), radius=3, fill=(6, 5, 12, 135), outline=(*accent, 84), width=1)
    draw.text((x2 - 44, y1 + 8), status, font=status_font, fill=(*accent, 210))


def create_faction_picture(page):
    """生成进入势力后的二级页面背景：左侧势力大卡，右侧人物卡网格。"""
    width, height = 1024, 512
    data = FACTION_PAGES[page]
    accent = data["accent"]
    image = load_white_night_base(width, height)
    dim = Image.new("RGBA", image.size, (8, 4, 16, 118))
    image.alpha_composite(dim)
    draw = ImageDraw.Draw(image, "RGBA")

    # 外框和左侧势力大卡，借鉴参考页面结构但使用白夜馆灯箱样式。
    draw.rounded_rectangle((44, 38, 980, 476), radius=14, fill=(9, 7, 20, 122), outline=(242, 226, 185, 116), width=2)
    draw.rounded_rectangle((60, 78, 308, 346), radius=10, fill=(18, 10, 28, 156), outline=(*accent, 190), width=3)
    draw.rounded_rectangle((74, 92, 294, 282), radius=8, fill=(42, 24, 54, 110), outline=(255, 240, 255, 56), width=1)
    draw_faction_badge(image, (184, 172), data["title"].split(" / ")[0], accent, data["glyph"])
    title_font = load_font(27, bold=True)
    small_font = load_font(14, bold=True)
    title_w = draw.textlength(data["title"], font=title_font)
    draw_glow(draw, (184 - title_w / 2, 292), data["title"], title_font, (255, 242, 226, 232), (*accent, 80), radius=1)
    draw.text((84, 324), "WHITE NIGHT PAVILION ARCHIVE", font=small_font, fill=(210, 190, 210, 170))

    # 中部势力切换纵列，用小徽记提示其它分类。
    side_factions = [
        ("中央", (142, 238, 214), "court"),
        ("圣星", (210, 188, 96), "church"),
        ("学园", (120, 196, 255), "school"),
        ("白夜", (235, 196, 238), "white_night"),
        ("记忆", (190, 148, 244), "memory"),
        ("联动", (244, 122, 92), "linkage"),
    ]
    for idx, (label, side_accent, glyph) in enumerate(side_factions):
        cy = 76 + idx * 52
        draw_faction_badge(image, (356, cy), label, side_accent, glyph, icon_size=48, show_label=False)

    # 右侧角色卡网格，当前已规划角色会显示为小卡；待整理角色作为占位。
    card_positions = [
        (430, 82, 560, 190),
        (590, 82, 720, 190),
        (750, 82, 880, 190),
        (430, 224, 560, 332),
        (590, 224, 720, 332),
        (750, 224, 880, 332),
    ]
    for index, box in enumerate(card_positions):
        if index < len(data["members"]):
            name, subtitle, status = data["members"][index]
        else:
            name, subtitle, status = "空位", "资料待整理", "待定"
        draw_character_card(draw, box, name, subtitle, status, accent)

    # 游戏事件窗口会叠加标题、正文和按钮；右侧档案卡在实机中容易形成双层 UI，这里压暗为留白背景。
    # 真正的联络、返回和招募操作全部交给下方事件选项承载。
    ui_clear = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ui_clear_draw = ImageDraw.Draw(ui_clear, "RGBA")
    ui_clear_draw.rounded_rectangle(
        (402, 64, 918, 336),
        radius=10,
        fill=(8, 5, 18, 255),
        outline=(*accent, 36),
        width=1,
    )
    image.alpha_composite(ui_clear)
    draw = ImageDraw.Draw(image, "RGBA")

    # 底部分页与说明条，主要作为视觉提示，不承载真实点击。
    draw.rounded_rectangle((430, 356, 880, 392), radius=6, fill=(17, 10, 26, 136), outline=(*accent, 88), width=1)
    draw.text((448, 364), "按下方事件选项切换、联络或返回。角色接入后会在这里点亮对应档案卡。", font=load_font(15), fill=(176, 255, 226, 210))
    for i in range(1, 5):
        fill = (*accent, 220) if (page, i) in [("central_church", 1), ("memory_palace", 2), ("white_night_gap", 3), ("collaboration", 4)] else (92, 74, 105, 170)
        draw.polygon([(612 + i * 34, 420), (626 + i * 34, 407), (640 + i * 34, 420), (626 + i * 34, 433)], fill=fill, outline=(255, 232, 242, 90))
        draw.text((621 + i * 34, 411), str(i), font=load_font(14, bold=True), fill=(18, 12, 26, 220))

    apply_event_safe_overlay(image)

    # Stellaris 会把事件正文与按钮绘制在图片下半区；这里把势力页自带的说明条和分页装饰压掉，避免进游戏后文字互相覆盖。
    event_text_clear = Image.new("RGBA", image.size, (0, 0, 0, 0))
    event_text_clear = Image.new("RGBA", image.size, (0, 0, 0, 0))
    clear_draw = ImageDraw.Draw(event_text_clear, "RGBA")
    for y in range(236, height):
        t = (y - 236) / (height - 236)
        clear_draw.line((0, y, width, y), fill=(10, 5, 18, int(110 + 145 * t)))
    clear_draw.rectangle((0, 284, width, height), fill=(8, 4, 16, 255))
    clear_draw.rounded_rectangle(
        (246, 292, 778, 504),
        radius=12,
        fill=(12, 6, 20, 255),
        outline=(122, 84, 138, 46),
        width=1,
    )
    image.alpha_composite(event_text_clear)
    png_path = EVENT_DIR / f"{data['file']}.png"
    dds_path = EVENT_DIR / f"{data['file']}.dds"
    image.convert("RGB").save(png_path)
    image.convert("RGBA").save(dds_path)
    return png_path, dds_path


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

        # 右上三枚菱形框作为白夜馆主菜单入口提示；事件选项仍由 Stellaris 按钮承载。
        menu_draw = ImageDraw.Draw(image, "RGBA")
        menu_font = load_font(25, bold=True)
        for i, label in enumerate(["通讯", "名册", "回忆"]):
            cy = 140 + i * 98
            diamond = [(884, cy), (920, cy - 28), (956, cy), (920, cy + 28)]
            menu_draw.polygon(diamond, fill=(34, 24, 48, 42), outline=(218, 178, 214, 80))
            menu_draw.line((894, cy, 946, cy), fill=(252, 215, 205, 48), width=1)
            draw_glow(menu_draw, (900, cy - 17), label, menu_font, (255, 242, 224, 190), (255, 177, 168, 58), radius=1)
            menu_draw.line((966, cy - 19, 966, cy + 19), fill=(248, 210, 205, 78), width=2)

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


def create_faction_picture(page):
    """生成势力页事件图：只保留势力徽章与索引，避免和 Stellaris 原生事件 UI 叠成双层窗口。"""
    width, height = 1024, 512
    data = FACTION_PAGES[page]
    accent = data["accent"]
    image = load_white_night_base(width, height)

    # 整体压暗，保留白夜馆背景氛围，但不给右侧再画独立窗口。
    dim = Image.new("RGBA", image.size, (8, 4, 16, 138))
    image.alpha_composite(dim)
    draw = ImageDraw.Draw(image, "RGBA")

    # 下半区只做阅读底色，正文与按钮完全交给游戏自己的事件 UI。
    lower = Image.new("RGBA", image.size, (0, 0, 0, 0))
    lower_draw = ImageDraw.Draw(lower, "RGBA")
    for y in range(252, height):
        t = (y - 252) / (height - 252)
        lower_draw.line((0, y, width, y), fill=(8, 4, 16, int(92 + 98 * t)))
    image.alpha_composite(lower)

    # 势力页不使用主入口的中部通讯灯箱；用柔和暗幕压掉背景源图里的横向框线。
    frame_clean = Image.new("RGBA", image.size, (0, 0, 0, 0))
    frame_draw = ImageDraw.Draw(frame_clean, "RGBA")
    frame_draw.rounded_rectangle((232, 146, 790, 356), radius=28, fill=(8, 4, 16, 146))
    frame_clean = frame_clean.filter(ImageFilter.GaussianBlur(14))
    image.alpha_composite(frame_clean)
    draw = ImageDraw.Draw(image, "RGBA")

    # 左侧势力档案牌保留为视觉锚点，尺寸收小以避开游戏标题与正文层。
    draw.rounded_rectangle(
        (64, 84, 306, 284),
        radius=10,
        fill=(18, 10, 28, 120),
        outline=(*accent, 160),
        width=3,
    )
    draw.rounded_rectangle(
        (82, 104, 288, 238),
        radius=7,
        fill=(42, 24, 54, 70),
        outline=(255, 240, 255, 42),
        width=1,
    )
    draw_faction_badge(image, (185, 172), data["title"].split(" / ")[0], accent, data["glyph"], icon_size=76, show_label=True)

    # 中间纵列作为名册分类索引，只显示小徽章，不再画文字标签，避免覆盖游戏标题。
    side_factions = [
        ("中央", (142, 238, 214), "court"),
        ("圣星", (210, 188, 96), "church"),
        ("学园", (120, 196, 255), "school"),
        ("白夜", (235, 196, 238), "white_night"),
        ("记忆", (190, 148, 244), "memory"),
        ("联动", (244, 122, 92), "linkage"),
    ]
    draw.line((340, 42, 340, 334), fill=(*accent, 58), width=1)
    for idx, (label, side_accent, glyph) in enumerate(side_factions):
        cy = 62 + idx * 46
        draw_faction_badge(image, (340, cy), label, side_accent, glyph, icon_size=40, show_label=False)

    # 顶部和右侧只加极轻边线，让背景承托窗口而不自成一套 UI。
    draw.line((52, 58, 972, 58), fill=(242, 226, 185, 52), width=1)
    draw.line((52, 58, 52, 354), fill=(*accent, 58), width=1)
    draw.line((972, 58, 972, 354), fill=(*accent, 34), width=1)

    png_path = EVENT_DIR / f"{data['file']}.png"
    dds_path = EVENT_DIR / f"{data['file']}.dds"
    image.convert("RGB").save(png_path)
    image.convert("RGBA").save(dds_path)
    return png_path, dds_path


if __name__ == "__main__":
    event_png, event_dds = create_event_picture()
    faction_outputs = [create_faction_picture(page) for page in FACTION_PAGES]
    icon_png, icon_dds = create_edict_icon()
    print(f"event_png={event_png}")
    print(f"event_dds={event_dds}")
    for faction_png, faction_dds in faction_outputs:
        print(f"faction_png={faction_png}")
        print(f"faction_dds={faction_dds}")
    print(f"icon_png={icon_png}")
    print(f"icon_dds={icon_dds}")
