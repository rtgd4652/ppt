"""按实体静态挂接统计外部舰船，保留来源和未解析项，不操作游戏。"""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'validation'))
from check_mod import parse, scalar, walk
from inspect_external_mesh_counts import inspect, load_reader


def index_root(root):
    entities, meshes, errors = {}, {}, []
    for path in sorted((root / 'gfx').rglob('*')):
        if path.suffix not in ('.asset', '.gfx'):
            continue
        try:
            nodes = parse(path.read_text(encoding='utf-8-sig'))
        except (ValueError, UnicodeError) as exc:
            errors.append({'file': str(path), 'error': str(exc)})
            continue
        for node, _ in walk(nodes):
            if node.key not in ('entity', 'pdxmesh') or not isinstance(node.value, list):
                continue
            name = scalar(node.value, 'name')
            if not name:
                continue
            target = entities if node.key == 'entity' else meshes
            target[name] = {'entries': node.value, 'source': str(path), 'line': node.line}
    return entities, meshes, errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    reader = load_reader(Path(config['addon']))
    base = Path(config['game'])
    base_entities, base_meshes, base_errors = index_root(base)
    cache, results = {}, []
    for group in config['mods']:
        root = Path(group['root'])
        own_entities, own_meshes, own_errors = index_root(root)
        entities, meshes = base_entities | own_entities, base_meshes | own_meshes
        for requested in group['entities']:
            instances, warnings, references = Counter(), [], []

            def descend(name, stack=()):
                if name in stack:
                    warnings.append('entity cycle: ' + name)
                    return
                definition = entities.get(name)
                if definition is None:
                    warnings.append('missing entity: ' + name)
                    return
                entries = definition['entries']
                references.append({'entity': name, 'source': definition['source'], 'line': definition['line']})
                clone = scalar(entries, 'clone')
                if clone:
                    # 不猜测引擎覆写／继承语义；明确报告此实例不完整。
                    warnings.append('unexpanded clone: ' + name + ' -> ' + clone)
                meshname = scalar(entries, 'pdxmesh')
                if meshname:
                    md = meshes.get(meshname)
                    if md is None:
                        warnings.append('missing pdxmesh: ' + meshname)
                    else:
                        filename = scalar(md['entries'], 'file')
                        if filename:
                            path = next((r / filename for r in (root, base) if (r / filename).is_file()), None)
                            if path is None:
                                warnings.append('missing mesh file: ' + filename)
                            else:
                                key = str(path)
                                if key not in cache:
                                    cache[key] = inspect(path, reader)
                                instances[key] += 1
                        else:
                            warnings.append('pdxmesh has no file: ' + meshname)
                for item in entries:
                    if item.key == 'attach' and isinstance(item.value, list):
                        for attachment in item.value:
                            if isinstance(attachment.value, str):
                                descend(attachment.value, stack + (name,))

            descend(requested)
            rows = [{'path': key, 'instances': count, 'triangles_each': cache[key]['render_triangles'],
                     'triangles_instanced': count * cache[key]['render_triangles']} for key, count in instances.items()]
            result = {'mod': group['name'], 'entity': requested,
                      'static_attached_triangles': sum(r['triangles_instanced'] for r in rows),
                      'instances': rows, 'references': references, 'unresolved': warnings,
                      'definition_parse_errors': own_errors}
            results.append(result)
            print(json.dumps({k: result[k] for k in ('mod', 'entity', 'static_attached_triangles', 'unresolved')}, ensure_ascii=False), flush=True)
    args.output.write_text(json.dumps({
        'date': '2026-11-04',
        'method': 'Direct entity pdxmesh plus recursive top-level attach multiplicity; material-bearing triangles; no particles, dynamic state spawns, loadout turrets or automatic ship sections. Clone expansion explicitly unresolved.',
        'base_definition_parse_errors': base_errors, 'assemblies': results, 'meshes': list(cache.values()),
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
