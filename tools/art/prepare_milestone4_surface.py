"""生成中央庭模型样品的确定性贴图，不采样旧舰、旧塔或角色素材。"""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "art/models/milestone4_surface_v02"
# 四列两行；所有颜色与材料职责来自已批准的公共校准板。
PALETTE = (
    ("armor", (24, 38, 48), (0, 68, 28, 95), 0),
    ("plate", (48, 70, 81), (0, 90, 65, 120), 0),
    ("silver", (155, 168, 174), (0, 130, 155, 155), 0),
    ("warm", (214, 217, 213), (0, 72, 20, 110), 0),
    ("glass", (26, 65, 79), (0, 165, 35, 200), 0),
    ("vent", (18, 27, 32), (0, 70, 125, 90), 0),
    ("cyan", (105, 193, 204), (0, 95, 40, 125), 70),
    ("amber", (211, 154, 85), (0, 85, 30, 110), 45),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pillow-dir", type=Path)
    args = parser.parse_args()
    if args.pillow_dir:
        sys.path.insert(0, str(args.pillow_dir.resolve()))
    from PIL import Image, ImageDraw

    output = OUTPUT / "export"
    output.mkdir(parents=True, exist_ok=True)
    diffuse = Image.new("RGBA", (1024, 512), (24, 38, 48, 255))
    properties = Image.new("RGBA", diffuse.size)
    # 本机 standardfuncsgfx.fxh: G=法线X、A=翻转后的Y；R重复G，B为发光。
    normal = Image.new("RGBA", diffuse.size, (128, 128, 0, 128))
    d, p, n = ImageDraw.Draw(diffuse), ImageDraw.Draw(properties), ImageDraw.Draw(normal)
    for index, (name, rgb, packed, emissive) in enumerate(PALETTE):
        x, y = index % 4 * 256, index // 4 * 256
        d.rectangle((x, y, x + 255, y + 255), fill=(*rgb, 255))
        p.rectangle((x, y, x + 255, y + 255), fill=packed)
        n.rectangle((x, y, x + 255, y + 255), fill=(128, 128, emissive, 128))
        # 面板接缝和有限维护痕迹由几何规律生成，不把概念板复制为纹理。
        if name in ("armor", "plate", "silver", "warm", "vent"):
            for row in range(4):
                for col in range(2):
                    left, top = x + 8 + 120 * col, y + 8 + 60 * row
                    dark = tuple(max(0, c - 12) for c in rgb)
                    light = tuple(min(255, c + 10) for c in rgb)
                    d.rectangle((left, top, left + 112, top + 51), outline=(*dark, 255), width=2)
                    d.line((left + 3, top + 3, left + 109, top + 3), fill=(*light, 255))
                    n.line((left, top, left + 112, top), fill=(128, 128, 0, 140))
                    n.line((left, top + 51, left + 112, top + 51), fill=(128, 128, 0, 116))
                    n.line((left, top, left, top + 51), fill=(140, 140, 0, 128))
                    for bx, by in ((left + 5, top + 6), (left + 107, top + 45)):
                        d.rectangle((bx, by, bx + 2, by + 2), fill=(*dark, 255))
            if name == "vent":
                for offset in range(18, 239, 12):
                    d.line((x + 16, y + offset, x + 239, y + offset), fill=(8, 14, 18, 255), width=3)

    records = []
    for name, image in (("reality_surface_diffuse", diffuse),
                        ("reality_surface_properties", properties),
                        ("reality_surface_normal", normal)):
        image.save(output / (name + ".png"))
        path = output / (name + ".dds")
        image.save(path, pixel_format="DXT5")
        with Image.open(path) as decoded:
            assert decoded.size == (1024, 512)
            assert path.read_bytes()[84:88] == b"DXT5"
        records.append({"name": name, "size": [1024, 512], "format": "DXT5",
                        "dds": path.relative_to(ROOT).as_posix(), "dds_readback": "pass"})
    record = {"status": "draft_pending_human_review", "runtime_installed": False,
              "origin": "project_generated_procedural_surface_no_legacy_textures",
              "palette": [item[0] for item in PALETTE], "textures": records,
              "normal_channels": "R=G; G=normal X; A=-normal Y; B=low emission",
              "properties_channels": "R=empire recolor mask zero; G=specular; B=metalness; A=glossiness",
              "reference": "local Stellaris 4.5.2 gfx/FX/standardfuncsgfx.fxh and pdxmesh_ship.fxh"}
    (OUTPUT / "surface_manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("M4_SURFACE_OK=" + json.dumps({"textures": len(records), "size": [1024, 512]}))


if __name__ == "__main__":
    main()
