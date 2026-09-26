#!/usr/bin/env python3
"""从仓库原画导出固定尺寸 UI 纹理；不改写源图或游戏原版界面。"""

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pillow-dir", type=Path, help="可选的已有 Pillow 安装目录")
    args = parser.parse_args()
    if args.pillow_dir:
        sys.path.insert(0, str(args.pillow_dir.resolve()))
    from PIL import Image, ImageOps

    preview_dir = ROOT / "temp/awp02-451-20260926/ui-previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    records = []

    def export(source, output, box, canvas_size, subject_size=None):
        source_path, output_path = ROOT / source, ROOT / output
        with Image.open(source_path) as original:
            # 用源图比例记录裁切，避免不同原画尺寸造成位置漂移。
            crop_box = tuple(round(n * original.size[i % 2]) for i, n in enumerate(box))
            cropped = original.convert("RGBA").crop(crop_box)
        if subject_size:
            subject = ImageOps.contain(cropped, subject_size, Image.Resampling.LANCZOS)
            texture = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
            texture.alpha_composite(subject, ((canvas_size[0] - subject.width) // 2,
                                              canvas_size[1] - subject.height))
        else:
            texture = cropped.resize(canvas_size, Image.Resampling.LANCZOS)
        # BC3 保留肖像透明留白；尺寸沿用原版画布，不改变所有物种的全局缩放。
        texture.save(output_path, pixel_format="DXT5")
        with Image.open(output_path) as decoded:
            assert decoded.size == canvas_size, output
            assert decoded.convert("RGBA").getbbox(), output
            decoded.save(preview_dir / (output_path.stem + ".png"))
        records.append({"source": source, "source_sha256": digest(source_path),
                        "crop_box": crop_box, "output": output,
                        "size": canvas_size, "subject_bounds": texture.getbbox(),
                        "output_sha256": digest(output_path)})

    # 排除源图右侧烘焙的菜单字样，仅取接待者与沙发区域。
    export("mod/gfx/event_pictures/aemusa_white_night_pavilion.png",
           "mod/gfx/event_pictures/aemusa_white_night_pavilion_event.dds",
           (40 / 1024, 75 / 512, 850 / 1024, 345 / 512), (450, 150))
    # 575×380 为原版 character 画布；210×350 同时适配内阁和领袖故事左栏。
    # 收窄取景而非压扁原画，保留头部与躯干高度，避免盖住右侧正文。
    export("mod/gfx/models/portraits/aemusa_portrait_upper_dxt1.png",
           "mod/gfx/models/portraits/aemusa_portrait_ui.dds",
           (300 / 700, 0, 540 / 700, 1), (575, 380), (210, 350))
    export("mod/gfx/models/portraits/aemusa_portrait_level_30.png",
           "mod/gfx/models/portraits/aemusa_portrait_level_30_ui.dds",
           (0.345, 0.285, 0.662, 0.615), (575, 380), (210, 350))
    manifest = ROOT / "tools/build/ui_assets_manifest.json"
    manifest.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"exported": len(records), "manifest": str(manifest),
                      "dds_roundtrip_verified": True}, ensure_ascii=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
