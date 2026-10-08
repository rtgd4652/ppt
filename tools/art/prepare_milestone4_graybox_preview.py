"""汇总已有灰模三视图，不重建模型或改动游戏资源。"""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "art/models/milestone4_graybox"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pillow-dir", type=Path, help="已有Pillow目录")
    args = parser.parse_args()
    if args.pillow_dir:
        sys.path.insert(0, str(args.pillow_dir.resolve()))
    from PIL import Image, ImageDraw, ImageOps

    manifest = json.loads((OUTPUT / "graybox_manifest.json").read_text(encoding="utf-8"))
    expected = [f"{role}_{view}.png" for role in ("flagship", "hub_base", "hub_active")
                for view in ("top", "side", "oblique")]
    available = {Path(p).name: ROOT / p for p in manifest["previews"]}
    if set(expected) != set(available):
        raise ValueError("灰模三视图清单不完整。")

    board = Image.new("RGB", (1280, 950), (25, 31, 39))
    draw = ImageDraw.Draw(board)
    draw.text((25, 18), "M4 fresh graybox v0.1 | source / export draft | not installed in game", fill=(221, 228, 237))
    for index, name in enumerate(expected):
        x, y = 20 + (index % 3) * 420, 55 + (index // 3) * 295
        # 使用最新完整帧等比缩放，不从旧联系表重新裁切。
        with Image.open(available[name]) as source:
            frame = ImageOps.contain(source.convert("RGB"), (400, 263), Image.Resampling.LANCZOS)
        board.paste(frame, (x + (400 - frame.width) // 2, y))
        draw.text((x + 8, y + 268), name.removesuffix(".png"), fill=(207, 220, 228))
    destination = OUTPUT / "previews/graybox_contact_sheet.png"
    board.save(destination)
    print(json.dumps({"preview": destination.relative_to(ROOT).as_posix(), "views": len(expected)}))


if __name__ == "__main__":
    main()
