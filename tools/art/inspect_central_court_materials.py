"""独立后台只读核对PDX法线、材质角色面积与原生着色器依据，不复制原版媒体。"""

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('F:/steam/steamapps/common/Stellaris')
ROLES = ('armor', 'plate', 'silver', 'warm', 'glass', 'vent', 'cyan', 'amber')


def inspect(path, read_meshfile, own=False):
    result = {'file': str(path.relative_to(ROOT)) if own else str(path), 'meshes': []}
    pdx = read_meshfile(str(path))
    for node in pdx.findall('./object/*/mesh'):
        a = node.attrib
        if 'n' not in a:
            # 原版另含无材质/无法线的碰撞网格，不拿它作渲染法线对照。
            assert not own
            result['meshes'].append({'keys': list(a), 'skipped': 'non-render collision mesh without normals'})
            continue
        positions = [Vector(a['p'][i:i+3]) for i in range(0, len(a['p']), 3)]
        normals = [Vector(a['n'][i:i+3]) for i in range(0, len(a['n']), 3)]
        indices = a['tri']
        alignment, up_normals, roles, area_sum = [], [], dict.fromkeys(ROLES, 0.0), 0.0
        uv = a.get('u0', a.get('uv0'))
        for i in range(0, len(indices), 3):
            ids = indices[i:i+3]
            p, q, r = [positions[j] for j in ids]
            cross = (q-p).cross(r-p)
            if cross.length < 1e-9:
                continue
            normal = sum((normals[j] for j in ids), Vector()).normalized()
            alignment.append(cross.normalized().dot(normal))
            if normal.y > .9:
                up_normals.append(normal.y)
            area = cross.length / 2
            area_sum += area
            if own and uv:
                u = sum(uv[j*2] for j in ids) / 3
                v = sum(uv[j*2+1] for j in ids) / 3
                # PDX导出UV原点为图像顶部，与作者UV的上下方向相反。
                tile = min(1, max(0, int(v*2))) * 4 + min(3, max(0, int(u*4)))
                roles[ROLES[tile]] += area
        result['meshes'].append({'keys': list(a), 'triangles': len(indices)//3,
             'surface_area_model_units': area_sum,
             'mean_winding_normal_alignment': sum(alignment)/len(alignment),
             'normal_positive_y_triangles': len(up_normals),
             'role_surface_fraction': {k:round(v/area_sum,4) for k,v in roles.items()} if own and uv else None})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdx-addon-root', required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('只允许独立后台factory-startup只读诊断。')
    sys.path.insert(0,args.pdx_addon_root)
    from io_pdx_mesh.pdx_data import read_meshfile
    paths=[ROOT/('mod/gfx/models/central_court_v04/ccv04_runtime_'+part+'.mesh')
           for part in ('bow_spinal','mid_artillery','stern')]
    own=[inspect(path, read_meshfile, True) for path in paths]
    native=inspect(GAME/'gfx/models/ships/mammalian_01/mammalian_01_battleship_bow_XL1.mesh',read_meshfile)
    result={'date':'2026-11-01','source_base':'2125b28','status':'read_only_diagnostic',
            'own':own,'native':native,
            'shader_references':['gfx/FX/pdxmesh_ship.fxh','gfx/FX/standardfuncsgfx.fxh'],
            'shader_equations':{'dielectric_F0':'G*G*0.4','metalness':'1-(1-B)*(1-B)',
                                'normal':'x=G*2-1, y=-(A*2-1), z=sqrt(saturate(1-x*x-y*y))','emissive':'normal.B'},
            'native_media_copied':False,'runtime_lighting_not_measured':True}
    output=ROOT/'reports/central_court_material_diagnostic_2026-11-01.json'
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('CC_MATERIAL_DIAGNOSTIC_OK '+json.dumps(own,ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
