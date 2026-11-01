"""后台为v04几何校准材质可读性，只移用上层检修面的现有雾银材质并保留全部挂点。"""

import argparse
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode=True
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_central_court_surface_v02 as base
import build_central_court_surface_v03 as refinement
import integrate_central_court_v04 as integration

ROOT=Path(__file__).resolve().parents[2]
SURFACE=ROOT/'art/models/central_court_surface_candidates_v03'
BOW=ROOT/'art/models/central_court_spinal_emitter_v04'
OUT=ROOT/'art/models/central_court_readability_v05'
EXPORT=OUT/'export'
DEST=ROOT/'mod/gfx/models/central_court_v04'
PARTS=integration.prior.PARTS
ROLES=('armor','plate','silver','warm','glass','vent','cyan','amber')


def paint_service_faces(collection):
    """只移动上朝检修面的UV到既有雾银格；不是全舰换色，也不修改网格坐标。"""
    obj=next(o for o in collection.objects if o.type=='MESH')
    mesh=obj.data
    uv=mesh.uv_layers.active.data
    before=tuple(tuple(v.co) for v in mesh.vertices)
    areas=dict.fromkeys(ROLES,0.0)
    after=dict.fromkeys(ROLES,0.0)
    face_roles={}
    for face in mesh.polygons:
        u=sum(uv[i].uv.x for i in face.loop_indices)/len(face.loop_indices)
        v=sum(uv[i].uv.y for i in face.loop_indices)/len(face.loop_indices)
        face_roles[face.index]=ROLES[min(1,max(0,int((1-v)*2)))*4+min(3,max(0,int(u*4)))]
    vertex_faces=[[] for _ in mesh.vertices]
    for face in mesh.polygons:
        for vertex in face.vertices:
            vertex_faces[vertex].append(face.index)
    unseen=set(range(len(mesh.polygons)))
    selected_faces=set()
    selected_components=0
    while unseen:
        first=unseen.pop()
        stack,component=[first],[first]
        while stack:
            for vertex in mesh.polygons[stack.pop()].vertices:
                for neighbor in vertex_faces[vertex]:
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        component.append(neighbor)
                        stack.append(neighbor)
        points=[mesh.vertices[i].co for f in component for i in mesh.polygons[f].vertices]
        low=[min(p[a] for p in points) for a in range(3)]
        high=[max(p[a] for p in points) for a in range(3)]
        # 按完整独立检修盖选择，避免三角面/斜面阈值在同一板件上留下半块跳色。
        if ({face_roles[f] for f in component}=={'plate'} and low[2]>.7 and
                high[2]-low[2]<.45 and abs((high[0]+low[0])/2)>2.7 and
                min(high[a]-low[a] for a in (0,1))>.6 and
                max(mesh.polygons[f].normal.z for f in component)>.85):
            selected_faces.update(component)
            selected_components+=1
    painted=0
    for face in mesh.polygons:
        role=face_roles[face.index]
        areas[role]+=face.area
        if face.index in selected_faces:
            for i in face.loop_indices:
                uv[i].uv.x+=.25
            painted+=1
            role='silver'
        after[role]+=face.area
    assert before==tuple(tuple(v.co) for v in mesh.vertices)
    total=sum(areas.values())
    obj.data.materials.clear()
    obj.data.materials.append(base.MAT)
    return {'author_collection':collection.name,'reassigned_faces':painted,
            'reassigned_whole_components':selected_components,
            'area_basis':'full 3D surface area, not screen projected percentage',
            'role_fraction_before':{k:round(v/total,4) for k,v in areas.items()},
            'role_fraction_after':{k:round(v/total,4) for k,v in after.items()}}


def compare_geometry(new,old):
    """UV拆分可能改变顶点索引，逐三角形展开坐标/法线核对，不使用例行哈希。"""
    meshes_new=new.findall('./object/*/mesh')
    meshes_old=old.findall('./object/*/mesh')
    assert len(meshes_new)==len(meshes_old)
    for a,b in zip(meshes_new,meshes_old):
        assert len(a.attrib['tri'])==len(b.attrib['tri'])
        for channel in ('p','n'):
            va,vb=a.attrib[channel],b.attrib[channel]
            for ia,ib in zip(a.attrib['tri'],b.attrib['tri']):
                assert all(abs(va[ia*3+k]-vb[ib*3+k])<1e-5 for k in range(3)), channel
    assert {n.tag:n.attrib for n in new.findall('./locator/*')}=={n.tag:n.attrib for n in old.findall('./locator/*')}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdx-addon-root',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('只允许独立后台factory-startup，不操作用户交互场景。')
    sys.path.insert(0,args.pdx_addon_root)
    from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile
    from io_pdx_mesh.pdx_data import read_meshfile
    assert json.loads((OUT/'surface_manifest.json').read_text(encoding='utf-8'))['rgb_diffuse_bytes_unchanged']
    bpy.ops.wm.open_mainfile(filepath=str(SURFACE/'central_court_surface_candidates_v03.blend'))
    wanted={'ccv03_'+p for p in PARTS if p!='bow_spinal'}
    for c in list(bpy.data.collections):
        if c.name not in wanted:
            for obj in list(c.objects):
                bpy.data.objects.remove(obj,do_unlink=True)
            bpy.data.collections.remove(c)
    with bpy.data.libraries.load(str(BOW/'central_court_spinal_emitter_v04.blend'),link=False) as (available,selected):
        selected.collections=['ccv04_bow_field']
    bow=selected.collections[0]
    bpy.context.scene.collection.children.link(bow)
    collections={p:bpy.data.collections['ccv03_'+p] for p in PARTS if p!='bow_spinal'}
    collections['bow_spinal']=bow
    base.EXP=EXPORT
    base.MAT=base.texture_material('cc_surface_v05')
    base.MAT.name='中央庭涂层与检修面可读性v05'
    refinement.shared_specular_proxy(base.MAT)
    painted=[paint_service_faces(collections[p]) for p in PARTS]
    scene=bpy.context.scene
    scene.name='中央庭暗部可读性候选v05'
    previews=OUT/'previews'
    previews.mkdir(parents=True,exist_ok=True)
    images=[]
    for stem,target,offset,scale in (('ship_readability',(0,-1,0),(43,59,49),77),
                                     ('bow_readability',(0,20,0),(18,30,22),32)):
        shown={collections[p].name for p in ('bow_spinal','mid_artillery','stern')}
        for c in bpy.data.collections:
            c.hide_render=c.name not in shown
            c.hide_viewport=False
        refinement.camera_view(scene,scene.camera,target,offset,scale)
        scene.render.filepath=str(previews/(stem+'.png'))
        bpy.ops.render.render(write_still=True)
        images.append((previews/(stem+'.png')).relative_to(ROOT).as_posix())
    refinement.camera_view(scene,scene.camera,(0,-1,0),(43,59,49),77)
    for c in bpy.data.collections:
        c.hide_render=c.hide_viewport=c.name not in shown
    bpy.data.orphans_purge(do_recursive=True)
    # 追加后可能保留来源库记录；先核实所有实际数据均已本地化，才清理空来源记录。
    linked=[block.name for block in bpy.data.user_map() if block.library is not None]
    assert not linked, f'仍有外部链接数据：{linked}'
    for library in list(bpy.data.libraries):
        bpy.data.libraries.remove(library)
    for image in bpy.data.images:
        if image.filepath.lower().endswith('.dds'):
            image.pack()
    bpy.context.preferences.filepaths.save_version=0
    blend=OUT/'central_court_readability_v05.blend'
    collection_names={p:c.name for p,c in collections.items()}
    assert len(bpy.data.libraries)==0
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    assert len(bpy.data.libraries)==0
    assert len([i for i in bpy.data.images if i.filepath.lower().endswith('.dds') and i.packed_file])==3
    collections={p:bpy.data.collections[name] for p,name in collection_names.items()}
    inspected=json.loads((ROOT/'reports/central_court_engine_space_2026-11-01.json').read_text(encoding='utf-8'))
    by_file={Path(row['file']).name:row for row in inspected}
    native={'gun':by_file['mammalian_01_battleship_bow_XL1.mesh']['locators']['xl_gun_01']['q'],
            'engine':by_file['mammalian_01_battleship_stern_L1.mesh']['locators']['engine_medium_01']['q']}
    integration.pipeline.EXPORT, integration.pipeline.ROOT=EXPORT,ROOT
    records=[]
    for part in PARTS:
        row=integration.export_part(part,collections[part],export_meshfile,read_meshfile,native)
        new=read_meshfile(str(ROOT/row['mesh']))
        baseline=ROOT/'art/models/central_court_runtime_v04/export'/(row['part']+'.mesh')
        compare_geometry(new,read_meshfile(str(baseline)))
        row.update(geometry_normals_and_all_locators_unchanged=True,source_generation='v05_materials_v04_geometry')
        records.append(row)
    # 实体名与消费者不变；仅替换网格UV/材质引用，旧v03贴图和v04导出基线保留。
    gfx=integration.prior.graphics(records).replace('中央庭v02','中央庭v05材质校准').replace('central_court_v02/','central_court_v04/').replace('cc_surface_v02_','cc_surface_v05_')
    (EXPORT/'_central_court_v04_meshes.gfx').write_text(gfx,encoding='utf-8')
    for path in EXPORT.iterdir():
        if path.suffix in ('.mesh','.dds','.gfx'):
            shutil.copy2(path,DEST/path.name)
    result={'date':'2026-11-01','source_base':'2125b28','status':'draft_integrated_runtime_pending',
            'formal_asset_approved':False,'meshes':records,'surface_reassignment':painted,
            'source_blend':blend.relative_to(ROOT).as_posix(),'source_reopened':True,'packed_dds':3,
            'geometry_normals_all_locators_unchanged':True,'diffuse_and_emission_bytes_unchanged':True,
            'new_self_illumination_on_armor':False,'previews':images,
            'new_entities_or_gameplay_changes':False,'user_live_blender_scene_modified':False,
            'native_windup_retained':True,'runtime_display_verified':False,
            'preview_lighting':'same v04 offline camera/lights, shader remains Blender proxy',
            'installation':'in-place v04 runtime mesh/material update; old authoring and v04 export baseline preserved'}
    (OUT/'readability_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('CC_READABILITY_V05_OK seven UV/material updates; expanded triangle positions/normals and every locator unchanged',flush=True)


if __name__=='__main__':
    main()
