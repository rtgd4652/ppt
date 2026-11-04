"""只读统计外部 PDX 网格；仅保存数量和路径，不复制第三方模型。"""

import argparse
import importlib
import json
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True


def load_reader(addon):
    # 只加载二进制读取模块，避免启动 Blender 或执行插件注册。
    package = types.ModuleType('io_pdx_mesh')
    package.__path__ = [str(addon)]
    sys.modules['io_pdx_mesh'] = package
    return importlib.import_module('io_pdx_mesh.pdx_data').read_meshfile


def inspect(path, reader):
    tree = reader(str(path))
    meshes = []
    for obj in tree.findall('./object/*'):
        for index, mesh in enumerate(obj.findall('mesh')):
            indices = mesh.attrib.get('tri', [])
            positions = mesh.attrib.get('p', [])
            assert len(indices) % 3 == 0, path
            assert len(positions) % 3 == 0, path
            assert not indices or (min(indices) >= 0 and max(indices) < len(positions) // 3), path
            material = mesh.find('material')
            meshes.append({
                'object': obj.tag, 'submesh': index,
                'object_attributes': obj.attrib,
                'triangles': len(indices) // 3,
                'vertices': len(positions) // 3,
                'has_material': material is not None,
                'has_normals': 'n' in mesh.attrib,
                'material': material.attrib if material is not None else None,
            })
    return {
        'path': str(path), 'bytes': path.stat().st_size,
        'render_triangles': sum(m['triangles'] for m in meshes if m['has_material']),
        'non_material_triangles': sum(m['triangles'] for m in meshes if not m['has_material']),
        'submeshes': meshes,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--addon', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    reader = load_reader(args.addon)
    entries = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    records = []
    for path in entries:
        record = inspect(Path(path), reader)
        records.append(record)
        print(f"{record['render_triangles']:>9} render | {record['non_material_triangles']:>7} other | {path}", flush=True)
    args.output.write_text(json.dumps({
        'method': 'PDX tri index count / 3; material-bearing submeshes separated from non-material meshes; file totals are not assembled-ship totals',
        'files': records,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
