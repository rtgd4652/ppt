"""第二批图标的尺寸导出、DDS回读及审阅板；不修改母版或运行资源。"""

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
repo = root.parents[2]
exports = root / 'exports'
exports.mkdir(exist_ok=True)
data = json.loads((root / 'generation.json').read_text(encoding='utf-8'))
board = Image.new('RGB', (1020, 850), '#101c29')
draw = ImageDraw.Draw(board)
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 20)
small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 16)
draw.text((24, 16), '第二批公共文明图标 · 沿用v0.2绘画方向', font=font, fill='#e1ded2')
draw.text((24, 52), '上排：已获方向反馈的前三张候选；下排：本次新作。均未安装运行纹理。', font=small, fill='#9daebd')
old_sources = ['building_seven_day_command_v02', 'tech_seven_day_logistics_v02', 'ap_resonance_path_v02']
old_labels = ['七日调度中枢', '七日后勤网络', '神器共鸣之路']
records = []

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for index, asset in enumerate(data['assets']):
    source = root / asset['source']
    size = asset['target_size'][0]
    runtime = repo / asset['runtime_texture']
    runtime_hash = sha256(runtime)
    with Image.open(source) as image:
        original = image.convert('RGBA')
    assert original.getchannel('A').getextrema() == (0, 255), source
    # 只作等比缩小与透明画布合成，不重绘图案。
    extent = round(size * 0.82)
    subject = original.copy()
    subject.thumbnail((extent, extent), Image.Resampling.LANCZOS)
    texture = Image.new('RGBA', (size, size))
    texture.alpha_composite(subject, ((size-subject.width)//2, (size-subject.height)//2))
    png = exports / f'{source.stem}_{size}.png'
    dds = exports / f'{source.stem}_{size}.dds'
    texture.save(png)
    texture.save(dds)
    with Image.open(dds) as decoded:
        assert decoded.size == (size, size) and decoded.mode == 'RGBA'
        assert decoded.tobytes() == texture.tobytes(), dds
    assert sha256(runtime) == runtime_hash
    x = 24 + 332 * index
    with Image.open(root.parent / 'milestone4_v02' / 'sources' / f'{old_sources[index]}.png') as old:
        old = old.convert('RGBA')
        old.thumbnail((190, 190), Image.Resampling.LANCZOS)
        board.paste(old, (x+50, 88), old)
    draw.text((x, 286), old_labels[index]+' · 既有候选', font=small, fill='#7f9bb1')
    draw.text((x, 334), asset['label'], font=font, fill='#e1ded2')
    preview = original.copy()
    preview.thumbnail((300, 300), Image.Resampling.LANCZOS)
    board.paste(preview, (x, 370), preview)
    # 实际尺寸单列，禁止把放大的审阅图当成游戏效果。
    board.paste(texture, (x+(300-size)//2, 682), texture)
    draw.text((x+58, 812), f'{size}×{size} 实际尺寸', font=small, fill='#9daebd')
    records.append({'source': asset['source'], 'source_size': list(original.size),
                    'source_sha256': sha256(source), 'source_alpha_extrema': [0,255],
                    'target_gfx': asset['target_gfx'], 'target_size': [size,size],
                    'png': str(png.relative_to(root)), 'dds': str(dds.relative_to(root)),
                    'dds_sha256': sha256(dds), 'format': 'DDS uncompressed RGBA8',
                    'dds_roundtrip_equal': True, 'runtime_texture': asset['runtime_texture'],
                    'runtime_sha256_unchanged_during_export': runtime_hash,
                    'runtime_installed': False, 'review_status': 'draft_pending_human_review'})

board.save(root / 'review_board.png')
(root / 'exports_manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('3 transparent masters; 128/128/64 RGBA8 DDS roundtrips identical; runtime textures unchanged during export.')
