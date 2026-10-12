"""导出已生成图标的尺寸样品与审阅板；保留母版，不写入运行Mod。"""

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
exports = root / 'exports'
exports.mkdir(exist_ok=True)
manifest = json.loads((root / 'generation.json').read_text(encoding='utf-8'))
board = Image.new('RGB', (900, 610), '#0c151e')
draw = ImageDraw.Draw(board)
font_path = Path('C:/Windows/Fonts/msyh.ttc')
font = ImageFont.truetype(str(font_path), 20)
small_font = ImageFont.truetype(str(font_path), 15)
labels = ['七日调度中枢 / 建筑', '七日后勤网络 / 科技', '神器共鸣之路 / 公共飞升']
records = []

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

draw.text((24, 16), '中央庭图标代表样品 v0.1 · 上：大图预览 / 下：实际尺寸', font=font, fill='#d6d9d5')
for index, (asset, label) in enumerate(zip(manifest['assets'], labels)):
    source = root / asset['source']
    with Image.open(source) as image:
        original = image.convert('RGBA')
    assert original.getchannel('A').getextrema() == (0, 255), source
    size = asset['target_size'][0]
    name = source.stem
    # 只作等比导出和透明留白，母版不裁切、不过绘，外缘留给游戏界面。
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    subject_size = round(size * 0.82)
    subject = original.resize((subject_size, subject_size), Image.Resampling.LANCZOS)
    offset = (size - subject_size) // 2
    output.alpha_composite(subject, (offset, offset))
    png_path = exports / f'{name}_{size}.png'
    dds_path = exports / f'{name}_{size}.dds'
    output.save(png_path)
    # 现有三项为RGBA未压缩DDS，保持其尺寸与编码类别，保留新母版透明度。
    output.save(dds_path)
    with Image.open(dds_path) as decoded:
        assert decoded.size == output.size
        assert decoded.mode == 'RGBA'
        assert decoded.tobytes() == output.tobytes(), dds_path
        draw_x = 20 + index * 300
        draw.text((draw_x, 61), label, font=font, fill='#d6d9d5')
        # 审阅板只排版显示，不改写任何母版；大图与实际尺寸分别呈现。
        large = original.resize((260, 260), Image.Resampling.LANCZOS)
        board.paste(large, (draw_x, 99), large)
        draw.text((draw_x, 380), f'{size}×{size} · PNG 与 DDS回读一致', font=small_font, fill='#79afc7')
        board.paste(decoded, (draw_x + (260-size)//2, 414), decoded)
    records.append({'source': asset['source'], 'source_size': list(original.size),
                    'source_sha256': sha256(source), 'target_gfx': asset['target_gfx'],
                    'png': str(png_path.relative_to(root)), 'dds': str(dds_path.relative_to(root)),
                    'target_size': [size, size], 'source_alpha_extrema': [0, 255],
                    'format': 'DDS uncompressed RGBA8', 'dds_roundtrip_equal': True,
                    'dds_sha256': sha256(dds_path), 'runtime_installed': False,
                    'review_status': 'draft_pending_human_review'})

draw.text((24, 573), '母版透明度保留 · 本次仅样品导出 · 尚未游戏验证', font=small_font, fill='#9ba8ae')
board.save(root / 'review_board.png')
(root / 'exports_manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'exported': len(records), 'dds_roundtrip_equal': True, 'runtime_installed': False}, ensure_ascii=False))
