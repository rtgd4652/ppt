"""汇总材质样品的离线预览，不修改原始帧或游戏资源。"""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "art/models/milestone4_surface_v02/previews"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pillow-dir", type=Path)
    args = parser.parse_args()
    if args.pillow_dir:
        sys.path.insert(0, str(args.pillow_dir.resolve()))
    from PIL import Image, ImageDraw, ImageOps

    board = Image.new("RGB", (1280, 350), (28, 35, 43))
    draw = ImageDraw.Draw(board)
    draw.text((20, 15), "M4 surface v0.2 | Blender preview | draft / not installed in game", fill=(225, 232, 238))
    for index, (role, label) in enumerate((
        ("flagship", "Reality flagship / 3 sections"),
        ("hub_base", "Baseline hub / foundation"),
        ("hub_active", "Baseline hub / operational"),
    )):
        # 使用完整原始帧，保留舰艉与四臂，不能从其他预览反复裁切。
        with Image.open(OUTPUT / (role + "_surface.png")) as source:
            frame = ImageOps.contain(source.convert("RGB"), (400, 260), Image.Resampling.LANCZOS)
        x = 20 + index * 420
        board.paste(frame, (x, 45))
        draw.text((x + 5, 316), label, fill=(205, 219, 228))
    path = OUTPUT / "surface_contact_sheet.png"
    board.save(path)
    print(path.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
