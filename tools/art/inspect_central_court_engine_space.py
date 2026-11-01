"""在独立Blender后台只读比较原生与候选PDX坐标、定位器和尺寸。"""

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import bpy

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('F:/steam/steamapps/common/Stellaris')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdx-addon-root', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('仅独立后台factory-startup，不操作用户场景。')
    sys.path.insert(0, args.pdx_addon_root)
    from io_pdx_mesh.pdx_data import read_meshfile
    paths = [GAME / ('gfx/models/ships/mammalian_01/mammalian_01_battleship_' + part + '.mesh')
             for part in ('frame', 'bow_L2', 'bow_XL1', 'mid_L3', 'mid_S4LHB', 'stern_L1')]
    paths += [ROOT / ('art/models/central_court_surface_candidates_v02/export/' + part + '.mesh')
              for part in ('ccv02_bow_spinal', 'ccv02_stern')]
    result = []
    for path in paths:
        pdx = read_meshfile(str(path))
        meshes = []
        for node in pdx.findall('./object/*/mesh'):
            positions = node.attrib.get('p', [])
            if positions:
                meshes.append({'keys': list(node.attrib),
                               'min': [min(positions[i::3]) for i in range(3)],
                               'max': [max(positions[i::3]) for i in range(3)]})
        result.append({'file': str(path), 'meshes': meshes,
                       'locators': {n.tag: n.attrib for n in pdx.findall('./locator/*')}})
    output = ROOT / 'reports/central_court_engine_space_2026-11-01.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    print('CC_ENGINE_SPACE_INSPECT_OK', len(paths), flush=True)


if __name__ == '__main__':
    main()
