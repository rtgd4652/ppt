"""只读盘点 1.0 美术来源、运行时纹理和占位接口，不改动游戏资源。"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHARACTERS = [
    ("aemusa", "爱缪莎"), ("antoniva", "安托涅瓦"), ("yanhua", "晏华"),
    ("an", "安"), ("seth", "赛斯"), ("yutong", "幽桐"), ("rabi", "拉比"),
    ("greysa", "格蕾莎"), ("wenzi", "雯梓"), ("li", "丽"),
]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".dds"}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def describe(path: Path) -> dict:
    """存在、尺寸和透明通道仅说明文件状态，不授予美术或发布批准。"""
    result = {"path": relative(path), "exists": path.is_file()}
    if not result["exists"]:
        return result
    result["bytes"] = path.stat().st_size
    if path.suffix.lower() in IMAGE_SUFFIXES:
        try:
            from PIL import Image
            with Image.open(path) as im:
                result.update(width=im.width, height=im.height, mode=im.mode)
                if "A" in im.getbands():
                    result["alpha_extrema"] = list(im.getchannel("A").getextrema())
        except (ImportError, OSError, ValueError) as exc:
            result["inspection_error"] = str(exc)
    return result


def inventory() -> dict:
    """按既有角色目录读取本地参考；不下载、不推断许可、不计算哈希。"""
    with (ROOT / "docs/art/reference_library/REFERENCE_MANIFEST.csv").open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        references = list(csv.DictReader(stream))
    reference_root = ROOT / "art/reference_library/original_game"
    portrait_files = list((ROOT / "mod/gfx/portraits").rglob("*.txt"))
    portraits = [{"definition_file": relative(p), "textures": re.findall(
        r'texturefile\s*=\s*"([^"]+)"', p.read_text(encoding="utf-8-sig"))}
        for p in sorted(portrait_files)]
    portrait_textures = {value for row in portraits for value in row["textures"]}
    characters = []
    for key, name in CHARACTERS:
        folders = sorted(reference_root.glob(key + "_*"))
        exact = reference_root / key
        if exact.is_dir():
            folders.append(exact)
        images = sorted({p for folder in folders if folder.is_dir()
                         for p in folder.rglob("*")
                         if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES})
        indexed_refs = [{"reference_id": row["reference_id"],
                         "review_status": row["review_status"],
                         "allowed_usage": row["allowed_usage"],
                         "local_file": describe(ROOT / row["local_path"])}
                        for row in references
                        if row["character_or_faction"] == name and row["local_path"]]
        characters.append({"key": key, "name": name,
                           "runtime_portrait_status": (
                               "character_texture_referenced"
                               if any(Path(value).name.startswith(key + "_")
                                      for value in portrait_textures)
                               else "no_character_texture_reference_found"),
                           "local_reference_images": [describe(p) for p in images],
                           "manifest_references": indexed_refs})

    icons = sorted((ROOT / "mod/gfx/interface/icons").rglob("*.dds"))
    interface_refs = []
    for path in sorted((ROOT / "mod/interface").glob("*.gfx")):
        text = path.read_text(encoding="utf-8-sig")
        # spriteType 的纹理字段是盘点线索；本程序不是完整的脚本验证器。
        for texture in re.findall(r'texturefile\s*=\s*"([^"]+)"', text):
            interface_refs.append({"definition": relative(path), "texture": texture,
                                   "provided_by_mod": (ROOT / "mod" / texture).is_file()})
    model_interfaces = {}
    for filename in ("mod/common/ship_sizes/aemusa_reality_flagship.txt",
                     "mod/common/section_templates/aemusa_reality_flagship_sections.txt",
                     "mod/common/megastructures/aemusa_reality_baseline.txt"):
        text = (ROOT / filename).read_text(encoding="utf-8-sig")
        model_interfaces[filename] = re.findall(
            r'^\s*(entity|construction_entity|portrait)\s*=\s*"([^"]+)"',
            text, flags=re.MULTILINE)
    return {
        # 北京时间固定为 UTC+8，Windows 环境无需另装 tzdata。
        "generated_at_beijing": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "scope": "local_asset_inventory_only_no_runtime_or_rights_approval",
        "characters": characters,
        "portrait_definitions": portraits,
        "runtime_portrait_textures": [describe(ROOT / "mod" / value)
                                      for value in sorted(portrait_textures)],
        "icon_dds_total": len(icons),
        "icon_dds_by_directory": dict(sorted(Counter(p.parent.name for p in icons).items())),
        "interface_texture_references": interface_refs,
        "model_interfaces": model_interfaces,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pillow-dir", type=Path,
                        help="使用已存在的 Pillow 目录；不会安装依赖")
    args = parser.parse_args()
    if args.pillow_dir:
        sys.path.insert(0, str(args.pillow_dir.resolve()))
    result = inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"output": str(args.output),
                      "characters": [{"name": c["name"],
                                      "reference_image_count": len(c["local_reference_images"]),
                                      "portrait_status": c["runtime_portrait_status"]}
                                     for c in result["characters"]],
                      "icon_dds_total": result["icon_dds_total"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
