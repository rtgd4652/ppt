"""生成中央庭整舰/造境候选的共享材质图集与完整DDS mip链，不采样概念图。"""

import argparse
import io
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/models/central_court_surface_candidates_v02'
PALETTE = (
    ('armor', (24, 38, 48), (0, 68, 28, 95), 0),
    ('plate', (48, 70, 81), (0, 90, 65, 120), 0),
    ('silver', (155, 168, 174), (0, 130, 155, 155), 0),
    ('warm', (214, 217, 213), (0, 72, 20, 110), 0),
    ('glass', (26, 65, 79), (0, 165, 35, 200), 0),
    ('vent', (18, 27, 32), (0, 70, 125, 90), 0),
    ('cyan', (105, 193, 204), (0, 95, 40, 125), 58),
    ('amber', (211, 154, 85), (0, 85, 30, 110), 30),
)


def dds_with_mips(image, path, Image):
    """逐级BC3编码，填写DDS原生mipmap计数与caps；保存后再次解码主层。"""
    levels, current, header = [], image, None
    while True:
        stream = io.BytesIO()
        current.save(stream, format='DDS', pixel_format='DXT5')
        encoded = stream.getvalue()
        assert encoded[:4] == b'DDS ' and encoded[84:88] == b'DXT5'
        if header is None:
            header = bytearray(encoded[:128])
        expected = max(1, (current.width + 3) // 4) * max(1, (current.height + 3) // 4) * 16
        assert len(encoded) - 128 == expected
        levels.append(encoded[128:])
        if current.size == (1, 1):
            break
        current = current.resize((max(1, current.width // 2), max(1, current.height // 2)), Image.Resampling.BOX)
    struct.pack_into('<I', header, 8, struct.unpack_from('<I', header, 8)[0] | 0x20000)
    struct.pack_into('<I', header, 28, len(levels))
    struct.pack_into('<I', header, 108, struct.unpack_from('<I', header, 108)[0] | 0x8 | 0x400000)
    path.write_bytes(bytes(header) + b''.join(levels))
    with Image.open(path) as check:
        check.load()
        assert check.size == image.size
    assert struct.unpack_from('<I', path.read_bytes(), 28)[0] == len(levels)
    return {'file': path.relative_to(ROOT).as_posix(), 'format': 'DXT5/BC3',
            'size': list(image.size), 'mip_levels': len(levels), 'bytes': path.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pillow-dir', type=Path, default=ROOT / 'temp/cc_surface_v02_deps')
    args = parser.parse_args()
    if args.pillow_dir.is_dir():
        sys.path.insert(0, str(args.pillow_dir.resolve()))
    from PIL import Image, ImageDraw, __version__

    export = OUT / 'export'
    export.mkdir(parents=True, exist_ok=True)
    size, tile = (2048, 1024), 512
    diffuse = Image.new('RGBA', size)
    properties = Image.new('RGBA', size)
    normal = Image.new('RGBA', size, (128, 128, 0, 128))
    d, p, n = (ImageDraw.Draw(im) for im in (diffuse, properties, normal))
    rng = random.Random(20261101)
    for i, (role, rgb, packed, emission) in enumerate(PALETTE):
        x, y = i % 4 * tile, i // 4 * tile
        bounds = (x, y, x + tile - 1, y + tile - 1)
        d.rectangle(bounds, fill=(*rgb, 255))
        p.rectangle(bounds, fill=packed)
        n.rectangle(bounds, fill=(128, 128, emission, 128))
        # 功能端不铺装甲接缝；发光只进入cyan/amber材质格的法线B通道。
        if role in ('cyan', 'amber', 'glass'):
            for k in range(36, 490, 38):
                d.rectangle((x + k, y + 28, x + k + 2, y + 483),
                            fill=(*[max(0, a - 12) for a in rgb], 255))
            continue
        for row in range(8):
            for col in range(4):
                left, top = x + 12 + col * 122, y + 12 + row * 61
                shade = rng.choice((-4, -2, 0, 2, 4))
                body = tuple(max(0, min(255, a + shade)) for a in rgb)
                dark = tuple(max(0, a - 15) for a in rgb)
                light = tuple(min(255, a + 9) for a in rgb)
                d.rectangle((left, top, left + 115, top + 54), fill=(*body, 255), outline=(*dark, 255), width=2)
                d.line((left + 3, top + 3, left + 111, top + 3), fill=(*light, 255), width=1)
                n.line((left, top, left + 115, top), fill=(128, 128, 0, 140), width=2)
                n.line((left, top + 54, left + 115, top + 54), fill=(128, 128, 0, 116), width=2)
                n.line((left, top, left, top + 54), fill=(140, 140, 0, 128), width=2)
                for bx, by in ((left + 7, top + 8), (left + 107, top + 46)):
                    d.rectangle((bx, by, bx + 2, by + 2), fill=(*dark, 255))
        if role == 'vent':
            for k in range(32, 490, 14):
                d.rectangle((x + 24, y + k, x + 487, y + k + 4), fill=(8, 14, 18, 255))

    records = []
    for suffix, image in (('diffuse', diffuse), ('properties', properties), ('normal', normal)):
        image.save(export / ('cc_surface_v02_' + suffix + '.png'))
        records.append(dds_with_mips(image, export / ('cc_surface_v02_' + suffix + '.dds'), Image))
    result = {'date': '2026-11-01', 'status': 'draft_pending_human_review', 'runtime_installed': False,
              'pillow_version': __version__,
              'origin': 'project_generated_procedural_surface_no_legacy_or_concept_image_sampling',
              'palette': [x[0] for x in PALETTE], 'textures': records,
              'normal_channels': 'R=G; G=normal X; A=-normal Y; B=functional emission',
              'properties_channels': 'R=recolor mask zero; G=specular; B=metalness; A=glossiness',
              'reference': 'docs/art/calibration/CENTRAL_COURT_MATERIAL_CALIBRATION.md',
              'uv_method': '8 shared material tiles, per-face axis projection with 5 percent inset',
              'unique_uv_bake': False, 'engine_mips_exposure_verified': False}
    (OUT / 'surface_manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('CC_SURFACE_V02_OK', len(records), 'BC3 textures with complete mip chains')


if __name__ == '__main__':
    main()
