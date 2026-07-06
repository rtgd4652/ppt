from __future__ import annotations

from pathlib import Path
from math import cos, sin, pi
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[3]
SIZE = 128
SOURCE_ATLAS = ROOT / "tools" / "build" / "icon_generation" / "source_atlas_realistic.png"
SOURCE_ATLAS_COLUMNS = 12
SOURCE_ATLAS_ROWS = 11


# 图标统一使用高对比剪影和青绿辉光，保证在 Stellaris 小尺寸 UI 中仍能辨认。
PALETTES = {
    "cyan": ("#082024", "#19f2d1", "#b9fff4", "#0c6c70"),
    "violet": ("#1b1028", "#b25cff", "#f0d7ff", "#4e1f75"),
    "gold": ("#2a210d", "#ffd66b", "#fff1b8", "#8a5d13"),
    "red": ("#2a1014", "#ff5e73", "#ffd2d9", "#7b1828"),
    "green": ("#10251c", "#6dff9d", "#d8ffe4", "#1d6b3f"),
    "blue": ("#101d2b", "#64c7ff", "#d9f4ff", "#1c5078"),
}


ICONS: dict[str, tuple[str, str, str]] = {
    # 飞升与传统
    "ascension_perks/ap_artifact_user_resonance_path": ("resonance", "cyan", "ring"),
    "ascension_perks/ap_artifact_user_apotheosis_path": ("apotheosis", "violet", "star"),
    "ascension_perks/ap_artifact_court_destiny": ("tarot", "gold", "tower"),
    "traditions/tr_artifact_court_adopt": ("gate", "cyan", "diamond"),
    "traditions/tr_artifact_court_finish": ("apotheosis", "gold", "star"),
    "traditions/tr_artifact_court_black_gate_watch": ("gate", "violet", "eye"),
    "traditions/tr_artifact_court_seven_guardians": ("army", "cyan", "seven"),
    "traditions/tr_artifact_court_tarot_archive": ("tarot", "gold", "cards"),
    "traditions/tr_artifact_court_city_network": ("city", "green", "grid"),
    "traditions/tr_artifact_court_final_day": ("shield", "red", "seven"),
    "traditions/tradition_icon_artifact_court": ("tower", "cyan", "crest"),

    # 科技
    "technologies/tech_artifact_tarot_calculation": ("tarot", "gold", "cards"),
    "technologies/tech_artifact_black_gate_observation": ("gate", "violet", "eye"),
    "technologies/tech_artifact_relic_fabrication": ("forge", "cyan", "hammer"),
    "technologies/tech_artifact_central_court_protocols": ("tower", "cyan", "grid"),
    "technologies/tech_artifact_tarot_economy": ("tarot", "green", "grid"),
    "technologies/tech_artifact_resonance_manufacturing": ("forge", "gold", "hex"),
    "technologies/tech_artifact_seven_day_logistics": ("city", "cyan", "seven"),
    "technologies/tech_artifact_destiny_economy": ("apotheosis", "gold", "grid"),
    "technologies/tech_artifact_phase_energy": ("reactor", "blue", "bolt"),
    "technologies/tech_artifact_phase_extraction": ("mine", "green", "pick"),
    "technologies/tech_artifact_crossing_trade": ("trade", "gold", "arrows"),
    "technologies/tech_artifact_civic_industry": ("goods", "green", "box"),
    "technologies/tech_artifact_rare_resonance": ("crystal", "violet", "triad"),
    "technologies/tech_artifact_covenant_administration": ("covenant", "gold", "seal"),
    "technologies/tech_artifact_relic_archive_restoration": ("archive", "violet", "book"),
    "technologies/tech_artifact_destiny_city_project": ("city", "gold", "dome"),
    "technologies/tech_artifact_fate_observatory": ("observatory", "violet", "tower"),
    "technologies/tech_artifact_destiny_lord": ("ship", "red", "crown"),
    "technologies/tech_artifact_user_combat_doctrine": ("army", "cyan", "blade"),
    "technologies/tech_artifact_user_resonance_armaments": ("weapon", "cyan", "beam"),
    "technologies/tech_artifact_user_apotheosis_warfare": ("weapon", "violet", "star"),

    # 建筑
    "buildings/building_artifact_sanctum": ("tower", "cyan", "crest"),
    "buildings/building_artifact_black_gate_observatory": ("gate", "violet", "eye"),
    "buildings/building_artifact_relic_workshop": ("forge", "gold", "hammer"),
    "buildings/building_artifact_seven_day_command": ("tower", "cyan", "seven"),
    "buildings/building_artifact_fate_calculus_institute": ("tarot", "violet", "grid"),
    "buildings/building_artifact_destiny_research_spire": ("observatory", "blue", "spire"),
    "buildings/building_artifact_resonance_alloy_forge": ("forge", "red", "hex"),
    "buildings/building_artifact_civic_goods_manufactory": ("goods", "green", "box"),
    "buildings/building_artifact_phase_reactor": ("reactor", "blue", "bolt"),
    "buildings/building_artifact_crossing_trade_tower": ("trade", "gold", "arrows"),
    "buildings/building_artifact_phase_mine": ("mine", "green", "pick"),
    "buildings/building_artifact_rare_resonance_refinery": ("crystal", "violet", "triad"),
    "buildings/building_artifact_memory_palace": ("archive", "cyan", "book"),
    "buildings/building_artifact_covenant_chamber": ("covenant", "gold", "seal"),
    "buildings/building_artifact_relic_archive": ("archive", "violet", "book"),

    # 区划、起源、决议、法令、陆军
    "districts/district_artifact_nexus": ("city", "cyan", "grid"),
    "districts/district_artifact_destiny_commons": ("city", "green", "dome"),
    "districts/district_artifact_destiny_industry": ("forge", "red", "hex"),
    "districts/district_artifact_destiny_foundation": ("mine", "green", "pick"),
    "districts/district_artifact_destiny_research": ("observatory", "blue", "spire"),
    "districts/district_artifact_destiny_fleet": ("ship", "cyan", "crown"),
    "origins/origin_artifact_resonance": ("gate", "cyan", "crest"),
    "decisions/decision_artifact_destiny_city_project": ("city", "gold", "dome"),
    "edicts/edict_summon_aemusa": ("tarot", "gold", "cards"),
    "edicts/edict_contact_aemusa": ("tower", "cyan", "crest"),
    "armies/army_type_artifact_user_guardian": ("army", "cyan", "blade"),
    "armies/army_type_artifact_user_resonance": ("army", "gold", "blade"),
    "armies/army_type_artifact_user_apotheosis": ("army", "violet", "star"),

    # 舰船部件组
    "ship_parts/ship_part_artifact_tarot_ray": ("weapon", "cyan", "beam"),
    "ship_parts/ship_part_artifact_fate_armor": ("armor", "gold", "plate"),
    "ship_parts/ship_part_artifact_seven_day_core": ("core", "cyan", "seven"),
    "ship_parts/ship_part_artifact_tarot_judgement": ("weapon", "violet", "lance"),
    "ship_parts/ship_part_artifact_fate_dominion": ("weapon", "red", "crown"),
    "ship_parts/ship_part_artifact_fate_ray_1": ("weapon", "cyan", "beam"),
    "ship_parts/ship_part_artifact_fate_ray_2": ("weapon", "gold", "beam"),
    "ship_parts/ship_part_artifact_fate_ray_3": ("weapon", "violet", "beam"),
    "ship_parts/ship_part_artifact_black_gate_shield_1": ("shield", "cyan", "diamond"),
    "ship_parts/ship_part_artifact_black_gate_shield_2": ("shield", "gold", "diamond"),
    "ship_parts/ship_part_artifact_black_gate_shield_3": ("shield", "violet", "diamond"),
    "ship_parts/ship_part_artifact_destiny_armor_1": ("armor", "cyan", "plate"),
    "ship_parts/ship_part_artifact_destiny_armor_2": ("armor", "gold", "plate"),
    "ship_parts/ship_part_artifact_destiny_armor_3": ("armor", "violet", "plate"),
    "ship_parts/ship_part_artifact_tactical_core_1": ("core", "cyan", "ring"),
    "ship_parts/ship_part_artifact_tactical_core_2": ("core", "gold", "ring"),
    "ship_parts/ship_part_artifact_tactical_core_3": ("core", "violet", "ring"),
    "ship_parts/ship_part_artifact_combat_computer_1": ("computer", "cyan", "grid"),
    "ship_parts/ship_part_artifact_combat_computer_2": ("computer", "gold", "grid"),
    "ship_parts/ship_part_artifact_combat_computer_3": ("computer", "violet", "grid"),
    "ship_parts/ship_part_artifact_sensor_1": ("sensor", "cyan", "eye"),
    "ship_parts/ship_part_artifact_sensor_2": ("sensor", "gold", "eye"),
    "ship_parts/ship_part_artifact_sensor_3": ("sensor", "violet", "eye"),
    "ship_parts/ship_part_artifact_destiny_lord_reactor": ("reactor", "red", "bolt"),
    "ship_parts/ship_part_artifact_destiny_lord_sensor": ("sensor", "violet", "eye"),
    "ship_parts/ship_part_artifact_destiny_lord_drive": ("drive", "blue", "ring"),
    "ship_parts/ship_part_artifact_destiny_lord_thruster": ("thruster", "cyan", "bolt"),
    "ship_parts/ship_part_artifact_destiny_lord_computer": ("computer", "violet", "grid"),
    "ship_parts/ship_part_artifact_aura_guardian_matrix": ("shield", "green", "ring"),
    "ship_parts/ship_part_artifact_aura_black_gate_suppression": ("gate", "red", "diamond"),
}


def polygon(cx: float, cy: float, radius: float, points: int, start: float = -pi / 2):
    return [
        (cx + cos(start + i * 2 * pi / points) * radius, cy + sin(start + i * 2 * pi / points) * radius)
        for i in range(points)
    ]


def draw_background(draw: ImageDraw.ImageDraw, bg: str, accent: str, dim: str):
    draw.rounded_rectangle((4, 4, 124, 124), radius=18, fill=bg, outline=dim, width=4)
    for r, alpha in [(56, 50), (42, 70), (28, 90)]:
        col = accent + f"{alpha:02x}"
        draw.ellipse((64 - r, 64 - r, 64 + r, 64 + r), outline=col, width=2)
    draw.line((18, 100, 110, 28), fill=dim, width=3)
    draw.line((22, 104, 114, 32), fill=accent, width=1)


def draw_motif(draw: ImageDraw.ImageDraw, motif: str, accent: str, bright: str, dim: str, variant: str):
    if motif == "tarot":
        for off in [-14, 0, 14]:
            draw.rounded_rectangle((43 + off, 30, 75 + off, 92), radius=5, outline=bright, width=3)
        draw.polygon(polygon(64, 61, 18, 4), outline=accent, fill=None)
        draw.line((52, 61, 76, 61), fill=accent, width=3)
    elif motif == "gate":
        draw.polygon(polygon(64, 64, 43, 4), outline=bright, width=5)
        draw.polygon(polygon(64, 64, 24, 4), outline=accent, width=4)
        draw.ellipse((51, 51, 77, 77), fill=dim, outline=bright, width=3)
    elif motif == "forge":
        draw.polygon((32, 82, 88, 82, 102, 98, 20, 98), fill=dim, outline=bright)
        draw.line((45, 35, 86, 76), fill=bright, width=9)
        draw.line((77, 34, 96, 53), fill=accent, width=9)
        draw.polygon(polygon(64, 62, 18, 6), outline=accent, width=3)
    elif motif == "tower" or motif == "observatory":
        draw.polygon((45, 104, 55, 42, 73, 42, 83, 104), fill=dim, outline=bright)
        draw.rectangle((39, 34, 89, 47), fill=dim, outline=bright, width=3)
        draw.line((64, 24, 64, 104), fill=accent, width=3)
        draw.arc((30, 22, 98, 90), 200, 340, fill=accent, width=3)
    elif motif == "city":
        for x, h in [(28, 42), (45, 58), (63, 50), (81, 66)]:
            draw.rounded_rectangle((x, 100 - h, x + 14, 100), radius=2, fill=dim, outline=bright)
        draw.arc((24, 30, 104, 110), 200, 340, fill=accent, width=5)
    elif motif == "reactor":
        draw.ellipse((32, 32, 96, 96), outline=bright, width=6)
        draw.ellipse((48, 48, 80, 80), fill=accent)
        draw.polygon((64, 18, 74, 58, 58, 58, 70, 110, 48, 68, 64, 68), fill=bright)
    elif motif == "mine":
        draw.polygon((34, 86, 54, 34, 76, 86), fill=dim, outline=bright)
        draw.line((40, 88, 94, 34), fill=bright, width=8)
        draw.line((82, 32, 98, 48), fill=accent, width=8)
    elif motif == "trade":
        draw.arc((28, 32, 98, 82), 205, 25, fill=bright, width=6)
        draw.arc((30, 48, 100, 98), 25, 205, fill=accent, width=6)
        draw.polygon((96, 37, 112, 45, 96, 55), fill=bright)
        draw.polygon((32, 91, 16, 83, 32, 73), fill=accent)
    elif motif == "goods":
        draw.polygon((36, 46, 64, 30, 92, 46, 92, 82, 64, 98, 36, 82), fill=dim, outline=bright)
        draw.line((36, 46, 64, 62, 92, 46), fill=accent, width=3)
        draw.line((64, 62, 64, 98), fill=accent, width=3)
    elif motif == "crystal":
        draw.polygon((64, 22, 84, 62, 64, 108, 44, 62), fill=dim, outline=bright)
        draw.polygon((36, 54, 52, 86, 30, 102, 22, 68), fill=dim, outline=accent)
        draw.polygon((92, 54, 106, 70, 98, 102, 76, 86), fill=dim, outline=accent)
    elif motif == "covenant":
        draw.ellipse((30, 30, 98, 98), outline=bright, width=5)
        draw.polygon(polygon(64, 64, 27, 6), outline=accent, width=4)
        draw.line((44, 64, 84, 64), fill=bright, width=4)
    elif motif == "archive":
        draw.rounded_rectangle((34, 30, 88, 100), radius=5, fill=dim, outline=bright, width=4)
        draw.line((48, 46, 78, 46), fill=accent, width=3)
        draw.line((48, 62, 78, 62), fill=accent, width=3)
        draw.polygon(polygon(64, 79, 12, 4), outline=bright, width=3)
    elif motif == "ship":
        draw.polygon((64, 20, 96, 96, 64, 82, 32, 96), fill=dim, outline=bright)
        draw.line((64, 28, 64, 86), fill=accent, width=4)
        draw.polygon((50, 98, 78, 98, 64, 112), fill=accent)
    elif motif == "army":
        draw.ellipse((52, 26, 76, 50), fill=bright)
        draw.rounded_rectangle((43, 52, 85, 98), radius=10, fill=dim, outline=bright, width=3)
        draw.line((34, 92, 94, 32), fill=accent, width=6)
        draw.line((44, 32, 94, 82), fill=accent, width=4)
    elif motif == "weapon":
        draw.line((26, 90, 88, 28), fill=bright, width=9)
        draw.line((38, 90, 100, 28), fill=accent, width=4)
        draw.polygon((86, 20, 108, 20, 102, 42), fill=bright)
    elif motif == "shield":
        draw.polygon((64, 22, 100, 38, 92, 86, 64, 108, 36, 86, 28, 38), fill=dim, outline=bright)
        draw.polygon((64, 38, 83, 48, 79, 80, 64, 92, 49, 80, 45, 48), outline=accent, width=4)
    elif motif == "armor":
        draw.polygon((38, 32, 90, 32, 98, 62, 82, 102, 46, 102, 30, 62), fill=dim, outline=bright)
        draw.line((44, 50, 84, 50), fill=accent, width=4)
        draw.line((38, 70, 90, 70), fill=accent, width=4)
    elif motif == "core":
        draw.ellipse((30, 30, 98, 98), outline=bright, width=6)
        draw.polygon(polygon(64, 64, 24, 3), outline=accent, width=5)
        draw.ellipse((56, 56, 72, 72), fill=bright)
    elif motif == "computer":
        draw.rounded_rectangle((30, 32, 98, 94), radius=8, fill=dim, outline=bright, width=4)
        for x in [44, 64, 84]:
            draw.line((x, 42, x, 84), fill=accent, width=2)
        for y in [48, 64, 80]:
            draw.line((40, y, 88, y), fill=accent, width=2)
    elif motif == "sensor":
        draw.ellipse((28, 42, 100, 86), outline=bright, width=5)
        draw.ellipse((50, 50, 78, 78), fill=dim, outline=accent, width=4)
        draw.line((64, 24, 64, 104), fill=accent, width=3)
    elif motif == "drive":
        draw.ellipse((28, 28, 100, 100), outline=bright, width=5)
        draw.arc((38, 38, 90, 90), 35, 310, fill=accent, width=5)
        draw.polygon((64, 42, 82, 82, 46, 74), fill=bright)
    elif motif == "thruster":
        draw.polygon((44, 24, 84, 24, 76, 78, 52, 78), fill=dim, outline=bright)
        draw.polygon((52, 78, 76, 78, 64, 112), fill=accent)
    else:
        draw.polygon(polygon(64, 64, 36, 6), fill=dim, outline=bright)

    if variant == "seven":
        for i in range(7):
            angle = -pi / 2 + i * 2 * pi / 7
            x = 64 + cos(angle) * 43
            y = 64 + sin(angle) * 43
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=bright)
    elif variant == "star":
        draw.polygon(polygon(64, 64, 42, 8), outline=bright, width=3)


def make_icon(motif: str, palette: str, variant: str) -> Image.Image:
    bg, accent, bright, dim = PALETTES[palette]
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((14, 14, 114, 114), fill=accent + "38")
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    base.alpha_composite(glow)
    draw = ImageDraw.Draw(base)
    draw_background(draw, bg, accent, dim)
    draw_motif(draw, motif, accent, bright, dim, variant)
    base = base.filter(ImageFilter.UnsharpMask(radius=1.0, percent=120, threshold=3))
    return base


def output_icon(rel: str, image: Image.Image) -> Image.Image:
    # 这些 UI 位置会按纹理原始尺寸绘制，必须按用途输出小图标。
    if rel.startswith("traditions/tr_artifact_court_"):
        return image.resize((48, 48), Image.Resampling.LANCZOS)
    if rel == "traditions/tradition_icon_artifact_court":
        return image.resize((64, 64), Image.Resampling.LANCZOS)
    if rel.startswith("ascension_perks/"):
        return image.resize((64, 64), Image.Resampling.LANCZOS)
    if rel.startswith("edicts/"):
        return image.resize((32, 32), Image.Resampling.LANCZOS)
    if rel.startswith("districts/"):
        canvas = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        inner = image.resize((22, 22), Image.Resampling.LANCZOS)
        canvas.alpha_composite(inner, (5, 5))
        return canvas
    if rel.startswith("ship_parts/"):
        if (
            "seven_day_core" in rel
            or "tactical_core" in rel
            or "shield" in rel
            or "armor" in rel
        ):
            canvas = Image.new("RGBA", (58, 58), (0, 0, 0, 0))
            inner = image.resize((44, 44), Image.Resampling.LANCZOS)
            canvas.alpha_composite(inner, (7, 7))
            return canvas
        return image.resize((58, 58), Image.Resampling.LANCZOS)
    return image


def save_icon(rel: str, image: Image.Image):
    png_path = ROOT / "mod" / "gfx" / "interface" / "icons" / f"{rel}.png"
    dds_path = ROOT / "mod" / "gfx" / "interface" / "icons" / f"{rel}.dds"
    png_path.parent.mkdir(parents=True, exist_ok=True)
    out = output_icon(rel, image)
    out.save(png_path)
    out.save(dds_path)


def crop_source_atlas() -> list[tuple[str, Image.Image]] | None:
    """从写实图集裁切图标；图集缺失时返回 None，交给程序化备选方案。"""
    if not SOURCE_ATLAS.exists():
        return None
    atlas = Image.open(SOURCE_ATLAS).convert("RGBA")
    width, height = atlas.size
    cell_w = width / SOURCE_ATLAS_COLUMNS
    cell_h = height / SOURCE_ATLAS_ROWS
    generated: list[tuple[str, Image.Image]] = []
    for index, rel in enumerate(ICONS):
        col = index % SOURCE_ATLAS_COLUMNS
        row = index // SOURCE_ATLAS_COLUMNS
        if row >= SOURCE_ATLAS_ROWS:
            raise ValueError(f"source atlas does not have enough cells for {rel}")
        left = round(col * cell_w)
        top = round(row * cell_h)
        right = round((col + 1) * cell_w)
        bottom = round((row + 1) * cell_h)
        cell = atlas.crop((left, top, right, bottom))
        side = min(cell.size)
        ox = (cell.width - side) // 2
        oy = (cell.height - side) // 2
        icon = cell.crop((ox, oy, ox + side, oy + side)).resize((SIZE, SIZE), Image.Resampling.LANCZOS)
        save_icon(rel, icon)
        generated.append((rel, output_icon(rel, icon)))
    return generated


def make_preview(generated: list[tuple[str, Image.Image]]):
    cols = 8
    cell = 152
    rows = (len(generated) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rows * cell), "#0b1116")
    for idx, (_, image) in enumerate(generated):
        x = (idx % cols) * cell + 12 + (SIZE - image.width) // 2
        y = (idx // cols) * cell + 12 + (SIZE - image.height) // 2
        sheet.alpha_composite(image, (x, y))
    out = ROOT / "tools" / "build" / "icon_generation" / "artifact_icon_preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def gfx_name(rel: str) -> str:
    stem = Path(rel).name
    if rel.startswith("ship_parts/"):
        return f"GFX_{stem}"
    return f"GFX_{stem}"


def write_generated_gfx():

    skip_prefixes = ("traditions/", "ascension_perks/")
    lines = [
        "spriteTypes = {",
        "\t# \u7531 tools/build/icon_generation/generate_artifact_icons.py \u751f\u6210\u7684\u795e\u5668\u4f7f\u4e13\u5c5e\u56fe\u6807\u6ce8\u518c\u3002",
    ]
    for rel in sorted(ICONS):
        if rel.startswith(skip_prefixes):
            continue
        lines.extend(
            [
                "\tspriteType = {",
                f'\t\tname = "{gfx_name(rel)}"',
                f'\t\ttexturefile = "gfx/interface/icons/{rel}.dds"',
                "\t\talwaystransparent = yes",
                "\t}",
            ]
        )
    lines.append("}")
    out = ROOT / "mod" / "interface" / "aemusa_generated_icons.gfx"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    generated = crop_source_atlas()
    if generated is None:
        generated = []
        for rel, (motif, palette, variant) in ICONS.items():
            image = make_icon(motif, palette, variant)
            save_icon(rel, image)
            generated.append((rel, output_icon(rel, image)))
    make_preview(generated)
    write_generated_gfx()
    print(f"generated {len(generated)} icons")


if __name__ == "__main__":
    main()


