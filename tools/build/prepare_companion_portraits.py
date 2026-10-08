#!/usr/bin/env python3
"""导出里程碑4代表肖像；保留原画、人物身份和现有全局UI比例。"""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "art/portraits/milestone4"
PROFILES = (
    ("antoniva", "antoniva_base_cutout_v01.png", (475, 240, 940, 960), (210, 350)),
    ("yanhua", "yanhua_base_cutout.png", None, (210, 350)),
    ("rabi_amit", "rabi_amit_joint_portrait_v03.png", None, (210, 350)),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pillow-dir", type=Path, help="已有Pillow目录")
    args = parser.parse_args()
    if args.pillow_dir:
        sys.path.insert(0, str(args.pillow_dir.resolve()))
    from PIL import Image, ImageDraw, ImageOps

    preview_dir = SOURCES / "previews"
    output_dir = ROOT / "mod/gfx/models/portraits"
    preview_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    # 只截去预览中的公共留白，运行纹理仍为完整575×380画布。
    board = Image.new("RGB", (885, 816), (36, 42, 51))
    draw = ImageDraw.Draw(board)
    records = []
    for column, (role, filename, crop_box, subject_size) in enumerate(PROFILES):
        source = SOURCES / filename
        with Image.open(source) as original:
            cutout = original.convert("RGBA")
        alpha_range = cutout.getchannel("A").getextrema()
        if alpha_range[0] != 0 or alpha_range[1] < 250:
            raise ValueError(f"源图缺少有效透明通道：{source}")
        box = crop_box or (0, 0, cutout.width, cutout.height)
        cropped = cutout.crop(box)
        subject = ImageOps.contain(cropped, subject_size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (575, 380), (0, 0, 0, 0))
        canvas.alpha_composite(subject, ((575 - subject.width) // 2, 380 - subject.height))
        output = output_dir / f"{role}_portrait_ui.dds"
        canvas.save(output, pixel_format="DXT5")
        with Image.open(output) as dds:
            decoded = dds.convert("RGBA")
            if decoded.size != (575, 380) or decoded.getchannel("A").getextrema()[0] != 0:
                raise ValueError(f"DDS尺寸或透明通道异常：{output}")
            decoded.save(preview_dir / f"{role}_transparent.png")
            for row, (label, color) in enumerate((
                ("dark", (16, 27, 38, 255)), ("light", (232, 236, 242, 255))
            )):
                backdrop = Image.new("RGBA", (575, 380), color)
                backdrop.alpha_composite(decoded)
                backdrop.convert("RGB").save(preview_dir / f"{role}_{label}.png")
                board.paste(backdrop.crop((140, 0, 435, 380)).convert("RGB"), (295 * column, 28 + 408 * row))
                draw.text((295 * column + 12, 8 + 408 * row), f"{role} / {label}", fill=(235, 238, 242))
        records.append({
            "role": role, "source": source.relative_to(ROOT).as_posix(),
            "source_size": list(cutout.size), "source_alpha_range": list(alpha_range),
            "crop_box": list(box), "subject_limit": list(subject_size),
            "subject_bounds": list(canvas.getbbox()),
            "output": output.relative_to(ROOT).as_posix(),
            "size": [575, 380], "format": "DXT5", "alpha_roundtrip_verified": True,
            "runtime_status": "not_claimed_by_build", "redistribution": "pending",
        })
    board.save(preview_dir / "three_portraits_contact_sheet.png")
    (SOURCES / "build_manifest.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"exported": len(records), "size": [575, 380], "format": "DXT5",
                      "preview": str(preview_dir / "three_portraits_contact_sheet.png")}, ensure_ascii=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
