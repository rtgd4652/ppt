"""在独立后台对整体候选作公共配色研究，不制作/安装正式游戏贴图。"""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'art/models/central_court_full_candidates_v01'
OUT=BASE/'material_study_v01'
PALETTE={'navy':'182630','graphite':'304651','white':'D6D9D5','silver':'9BA8AE','cyan':'69C1CC','amber':'D39A55'}


def linear(hex_value):
    values=[int(hex_value[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in values)


def make_material(key):
    mat=bpy.data.materials.new('公共配色研究_'+key);mat.use_nodes=True
    node=mat.node_tree.nodes.get('Principled BSDF');color=linear(PALETTE[key])
    node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Metallic'].default_value=.7 if key=='silver' else .25
    node.inputs['Roughness'].default_value=.42 if key=='silver' else .58
    if key in ('cyan','amber'):
        node.inputs['Emission Color'].default_value=(*color,1)
        node.inputs['Emission Strength'].default_value=.9 if key=='cyan' else .45
    return mat


def role(obj,face):
    x,y,z=face.center;n=face.normal
    if 'cruiser' in obj.name:
        if y<-22.5 and n.y<-.65 and abs(z)<1.05:return 'cyan'
        if abs(x)<1.5 and -5.1<y<-2.7 and z>2.25:return 'white'
        if n.z>.65 and face.area<2.2 and z>.55:return 'white'
        if n.z>.6:return 'graphite'
        if 0.15<abs(n.z)<.65 and face.area<2:return 'silver'
        if -5<y<-1 and abs(x)>6.4 and n.z>.1 and face.area<.12:return 'amber'
    else:
        if 'active' in obj.name:
            if abs(abs(x)-9)<1.3 and abs(y-1)<1.3 and abs(z-6.3)<.65:return 'cyan'
            if abs(x)<7.6 and abs(y-1)<2.5 and z>8.8 and n.x*x<-.25:return 'cyan'
        if n.z>.65 and .7<z<2.6 and face.area<2:return 'white'
        if z>2.6 and abs(n.z)<.55:return 'silver'
        if -10<y<-6 and 5<abs(x)<8 and 1<z<2.7 and face.area<.15:return 'amber'
        if n.z>.6:return 'graphite'
    return 'navy'


def main():
    if not bpy.app.background or bpy.data.filepath:raise RuntimeError('只能在独立后台factory-startup执行。')
    bpy.context.preferences.filepaths.save_version=0
    source=BASE/'central_court_full_candidates_v01.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source))
    OUT.mkdir(parents=True,exist_ok=True)
    keys=list(PALETTE);materials=[make_material(k) for k in keys]
    counts={};triangles={}
    groups=[c for c in bpy.data.collections if c.name.startswith('cc_candidate_')]
    assert len(groups)==5
    for c in groups:
        obj=next(o for o in c.objects if o.type=='MESH');obj.data.materials.clear()
        for mat in materials:obj.data.materials.append(mat)
        area={k:0 for k in keys}
        for face in obj.data.polygons:
            key=role(obj,face);face.material_index=keys.index(key);area[key]+=face.area
        counts[c.name]=area;triangles[c.name]=len(obj.data.polygons)
    planet=bpy.data.collections['仅预览天体参照_不导出']
    scene=bpy.context.scene;camera=scene.camera
    scene.cycles.samples=16
    images=[]
    for label,target,offset,scale in [('ship',(0,0,0),(40,-60,54),63),('worldformer',(0,-1,3),(34,-42,34),43)]:
        for c in groups:
            show=('cruiser' in c.name) if label=='ship' else c.name.endswith('worldformer_active')
            c.hide_render=not show;c.hide_viewport=False
        planet.hide_render=label=='ship';planet.hide_viewport=False
        camera.location=Vector(target)+Vector(offset);camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
        image=OUT/(label+'_material_study.png');scene.render.filepath=str(image);bpy.ops.render.render(write_still=True);images.append(image.relative_to(ROOT).as_posix())
    for c in groups:c.hide_render='cruiser' not in c.name;c.hide_viewport='cruiser' not in c.name
    planet.hide_render=True;planet.hide_viewport=True
    camera.location=(40,-60,54);camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=63
    bpy.data.orphans_purge(do_recursive=True);assert len(bpy.data.libraries)==0
    blend=OUT/'central_court_material_study_v01.blend'
    assert blend.resolve()!=source.resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    assert len(bpy.data.libraries)==0
    # open_mainfile后不复用旧RNA对象；按保存名称核对实际几何数。
    for name,number in triangles.items():
        obj=next(o for o in bpy.data.collections[name].objects if o.type=='MESH');assert len(obj.data.polygons)==number
    result=dict(date='2026-10-31',status='draft_pending_human_review',runtime_installed=False,geometry_changed=False,
        source_gray=str(source.relative_to(ROOT)),source_blend=str(blend.relative_to(ROOT)),previews=images,
        palette=PALETTE,palette_reference='docs/art/calibration/CENTRAL_COURT_MATERIAL_CALIBRATION.md',
        material_method='离线逐面分区与Blender节点材质，未烘焙正式DDS/UV图集',area_by_role=counts,
        mesh_triangles=triangles,saved_reopen='pass',game_exposure_and_performance='not_run',formal_asset_approved=False)
    (OUT/'material_study_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('MATERIAL_STUDY_OK two previews; saved file reopened; geometry retained.')


if __name__=='__main__':main()
