"""按公共配色重新生成精修候选的低对比装甲图集；不修改/采样v02纹理。"""

import argparse
import json
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_central_court_surface_v02 import dds_with_mips, PALETTE as ORIGINAL_PALETTE

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/models/central_court_surface_candidates_v03'
# RGB沿原批准色值，只调整高光/金属/光泽与功能发光；R重着色遮罩仍为0。
SURFACES = {
    'armor': (40, 20, 70, 0), 'plate': (58, 55, 82, 0),
    'silver': (85, 145, 112, 0), 'warm': (26, 10, 45, 0),
    'glass': (105, 12, 155, 0), 'vent': (35, 90, 65, 0),
    'cyan': (62, 35, 85, 42), 'amber': (52, 25, 72, 20),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pillow-dir', type=Path, default=ROOT / 'temp/cc_surface_v02_deps')
    args = parser.parse_args()
    if args.pillow_dir.is_dir():
        sys.path.insert(0, str(args.pillow_dir.resolve()))
    from PIL import Image, ImageDraw, __version__
    output = OUT / 'export'
    output.mkdir(parents=True, exist_ok=True)
    diffuse = Image.new('RGBA', (2048, 1024))
    properties = Image.new('RGBA', diffuse.size)
    normal = Image.new('RGBA', diffuse.size, (128, 128, 0, 128))
    d, p, n = (ImageDraw.Draw(im) for im in (diffuse, properties, normal))
    rng = random.Random(2026110103)
    palette = []
    for i, (role, rgb, old_properties, old_emission) in enumerate(ORIGINAL_PALETTE):
        x, y = i % 4 * 512, i // 4 * 512
        specular, metal, gloss, emission = SURFACES[role]
        d.rectangle((x, y, x + 511, y + 511), fill=(*rgb, 255))
        p.rectangle((x, y, x + 511, y + 511), fill=(0, specular, metal, gloss))
        n.rectangle((x, y, x + 511, y + 511), fill=(128, 128, emission, 128))
        palette.append({'role': role, 'rgb': list(rgb), 'rgb_unchanged': True,
                        'properties': [0, specular, metal, gloss], 'emission': emission,
                        'previous_properties': list(old_properties), 'previous_emission': old_emission})
        if role in ('cyan', 'amber', 'glass'):
            # 功能端保留干净工作面；细分线较弱，不用明亮装甲边铺满发光格。
            for offset in range(54, 490, 73):
                value = tuple(max(0, c - 7) for c in rgb)
                d.line((x + offset, y + 32, x + offset, y + 479), fill=(*value, 255), width=2)
            continue
        columns = 2 if role in ('armor', 'warm') else 3
        rows = 3
        cell_w, cell_h = 480 // columns, 480 // rows
        for row in range(rows):
            for col in range(columns):
                left, top = x + 16 + col * cell_w, y + 16 + row * cell_h
                right, bottom = left + cell_w - 9, top + cell_h - 9
                variation = rng.choice((-3, -1, 0, 1, 3))
                face = tuple(max(0, min(255, c + variation)) for c in rgb)
                edge = tuple(max(0, c - 8) for c in rgb)
                light = tuple(min(255, c + 4) for c in rgb)
                d.rectangle((left, top, right, bottom), fill=(*face, 255), outline=(*edge, 255), width=2)
                d.line((left + 3, top + 3, right - 3, top + 3), fill=(*light, 255), width=1)
                # 小幅加工纹理保留材料面；不把磨损/接缝当成主轮廓。
                for gy in range(top + 8, bottom - 5, 5):
                    grain = tuple(max(0, min(255, c + rng.choice((-1, 0, 1)))) for c in face)
                    d.line((left + 6, gy, right - 6, gy), fill=(*grain, 255), width=1)
                n.line((left, top, right, top), fill=(128, 128, 0, 136), width=2)
                n.line((left, bottom, right, bottom), fill=(128, 128, 0, 120), width=2)
                n.line((left, top, left, bottom), fill=(136, 136, 0, 128), width=2)
                for bx, by in ((left + 8, top + 9), (right - 10, bottom - 11)):
                    d.rectangle((bx, by, bx + 2, by + 2), fill=(*edge, 255))
        if role == 'vent':
            for offset in range(32, 488, 24):
                d.rectangle((x + 24, y + offset, x + 487, y + offset + 7), fill=(8, 14, 18, 255))
    records = []
    for suffix, image in (('diffuse', diffuse), ('properties', properties), ('normal', normal)):
        name = 'cc_surface_v03_' + suffix
        image.save(output / (name + '.png'))
        records.append(dds_with_mips(image, output / (name + '.dds'), Image))
    report = {'date': '2026-11-01', 'source_base': 'dfcc660', 'status': 'draft_pending_human_review',
              'runtime_installed': False, 'pillow_version': __version__, 'textures': records,
              'palette': palette, 'nominal_rgb_preserved': True,
              'method': 'new procedural low contrast panels and directional grain, no image sampling',
              'reference': 'docs/art/calibration/CENTRAL_COURT_MATERIAL_CALIBRATION.md',
              'normal_channels': 'R=G; G=normal X; A=-normal Y; B=functional emission',
              'properties_channels': 'R=zero recolor; G=specular; B=metalness; A=glossiness',
              'game_exposure_verified': False}
    (OUT / 'surface_manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('CC_SURFACE_V03_TEXTURES_OK 3 BC3 DDS, 12 mips each, nominal RGB preserved')


if __name__ == '__main__':
    main()
