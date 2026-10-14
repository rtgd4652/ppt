"""导出v0.2校准样品和新旧对照板；不改母版，不写运行Mod。"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pillow-dir', type=Path)
args = parser.parse_args()
if args.pillow_dir:
    sys.path.insert(0, str(args.pillow_dir.resolve()))
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
previous = root.parent / 'milestone4_v01'
exports = root / 'exports'
exports.mkdir(exist_ok=True)
generation = json.loads((root / 'generation.json').read_text(encoding='utf-8'))
board = Image.new('RGB', (960, 880), '#0c151e')
draw = ImageDraw.Draw(board)
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 19)
small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 15)
draw.text((20, 14), '七都风格校准候选 v0.2 · 新旧版本与实际像素尺寸', font=font, fill='#d6d9d5')
for x, text in [(24, 'v0.1 / 大图'), (264, 'v0.2 / 大图'), (524, '目标实际尺寸'), (744, '64像素辅助观察')]:
    draw.text((x, 47), text, font=small, fill='#79afc7')
labels = ['七日调度中枢 · 建筑', '七日后勤网络 · 科技', '神器共鸣之路 · 公共飞升']
records = []

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for index, (asset, label) in enumerate(zip(generation['assets'], labels)):
    source = root / asset['source']
    old_source = root / asset['edit_target']
    size = asset['target_size'][0]
    with Image.open(source) as image:
        original = image.convert('RGBA')
    with Image.open(old_source) as image:
        old = image.convert('RGBA')
    assert original.getchannel('A').getextrema() == (0, 255), source
    # 保留完整母版，等比缩放到82%输出画布；其余为真正透明留白。
    texture = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    extent = round(size * 0.82)
    subject = original.resize((extent, extent), Image.Resampling.LANCZOS)
    offset = (size - extent) // 2
    texture.alpha_composite(subject, (offset, offset))
    png = exports / f'{source.stem}_{size}.png'
    dds = exports / f'{source.stem}_{size}.dds'
    texture.save(png)
    texture.save(dds)
    with Image.open(dds) as decoded:
        assert decoded.size == texture.size
        assert decoded.mode == 'RGBA'
        assert decoded.tobytes() == texture.tobytes(), dds
    y = 83 + index * 252
    draw.text((24, y), label, font=font, fill='#d6d9d5')
    # 审阅板的版面缩放与正式尺寸分开，避免把放大预览当作实际UI效果。
    for image, x in [(old, 24), (original, 264)]:
        preview = image.resize((212, 212), Image.Resampling.LANCZOS)
        board.paste(preview, (x, y + 28), preview)
    board.paste(texture, (524 + (160-size)//2, y + 61), texture)
    auxiliary = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    small_subject = original.resize((52, 52), Image.Resampling.LANCZOS)
    auxiliary.alpha_composite(small_subject, (6, 6))
    board.paste(auxiliary, (780, y + 74), auxiliary)
    draw.text((524, y + 202), f'{size}×{size} DDS回读一致', font=small, fill='#9ba8ae')
    records.append({'source': asset['source'], 'source_size': list(original.size),
                    'source_sha256': sha256(source), 'edit_target': asset['edit_target'],
                    'edit_target_sha256': sha256(old_source), 'target_gfx': asset['target_gfx'],
                    'png': str(png.relative_to(root)), 'dds': str(dds.relative_to(root)),
                    'target_size': [size, size], 'format': 'DDS uncompressed RGBA8',
                    'source_alpha_extrema': [0, 255], 'dds_roundtrip_equal': True,
                    'dds_sha256': sha256(dds), 'runtime_installed': False,
                    'review_status': 'draft_pending_human_review'})

# 对照旧批次记录核实母版完整保留，仅检查本轮确实涉及的三张来源。
old_manifest = json.loads((previous / 'exports_manifest.json').read_text(encoding='utf-8'))
for old_record in old_manifest:
    assert sha256(previous / old_record['source']) == old_record['source_sha256']
draw.text((20, 850), '仅校准候选 · 原作图未上传生成工具 · 旧母版保留 · 未替换运行资源或验证游戏显示', font=small, fill='#9ba8ae')
board.save(root / 'comparison_board.png')
(root / 'exports_manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('3 RGBA8 DDS roundtrips identical; original v0.1 source hashes unchanged; runtime untouched.')
