"""独立后台精修终局旗舰；复用灰模坐标和定位器，另存v02供对照。"""

import json
import math
from pathlib import Path
import sys

import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_endgame_flagship_blockout as base

ROOT = base.ROOT
OUT = ROOT / 'art/models/aemusa_endgame_refinement_v02'


def painted_material(name, colors):
    """EEVEE内的分层绘画式明暗样品；不是群星运行材质。"""
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*colors[1],1)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
    diffuse=nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.inputs['Color'].default_value=(.8,.8,.8,1)
    diffuse.inputs['Roughness'].default_value=.65
    light=nodes.new('ShaderNodeShaderToRGB')
    links.new(diffuse.outputs[0],light.inputs[0])
    values=nodes.new('ShaderNodeRGBToBW')
    links.new(light.outputs[0],values.inputs[0])
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation='EASE'
    ramp.color_ramp.elements[0].position=.12
    ramp.color_ramp.elements[0].color=(*colors[0],1)
    ramp.color_ramp.elements[1].position=.8
    ramp.color_ramp.elements[1].color=(*colors[2],1)
    ramp.color_ramp.elements.new(.4).color=(*colors[1],1)
    links.new(values.outputs[0],ramp.inputs[0])
    emission=nodes.new('ShaderNodeEmission')
    links.new(ramp.outputs['Color'],emission.inputs['Color'])
    out=nodes.new('ShaderNodeOutputMaterial')
    links.new(emission.outputs[0],out.inputs['Surface'])
    return mat


def samples(rows, steps=7):
    """中心路径用插值连贯过渡，截面仍保留明确的转折面。"""
    result=[]
    for i in range(len(rows)-1):
        a=rows[max(0,i-1)];b=rows[i];c=rows[i+1];d=rows[min(len(rows)-1,i+2)]
        for j in range(steps):
            t=j/steps
            row=[]
            for k in range(5):
                value=.5*((2*b[k])+(-a[k]+c[k])*t+(2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+(-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t)
                # 长度与截面边界受相邻设计站位约束，避免插值无意夸大轮廓。
                if k in (0,3,4):value=max(min(b[k],c[k]),min(max(b[k],c[k]),value))
                row.append(value)
            result.append(row)
    result.append(list(rows[-1]))
    return result


def replace_shell(obj, rows, mat, signx=1, signz=1, core=False, end_curve=None):
    """将椭圆泡状截面改为带折面的实体壳，保留原对象身份。"""
    if core:
        profile=[(1,0),(.94,.36),(.62,.82),(.18,1),(-.18,1),(-.62,.82),
                 (-.94,.36),(-1,0),(-.82,-.62),(-.25,-.86),(.25,-.86),(.82,-.62)]
    else:
        profile=[(1,-.22),(.94,.40),(.55,.95),(-.35,.65),(-.9,.15),
                 (-1,-.35),(-.65,-.72),(.65,-.72)]
    stations=samples(rows)
    vertices=[]
    count=len(profile)
    for i,(y,x,z,w,h) in enumerate(stations):
        edge=(end_curve or {}).get('first',0) if i==0 else ((end_curve or {}).get('last',0) if i==len(stations)-1 else 0)
        for u,v in profile:
            vertices.append((signx*(x+u*w),y+edge*abs(u)**2,signz*(z+v*h)))
    faces=[]
    for i in range(len(stations)-1):
        for j in range(count):
            faces.append((i*count+j,i*count+(j+1)%count,(i+1)*count+(j+1)%count,(i+1)*count+j))
    faces.extend([tuple(reversed(range(count))),tuple(range(len(vertices)-count,len(vertices)))])
    mesh=bpy.data.meshes.new(obj.name+'_折面精修')
    mesh.from_pydata(vertices,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    obj.modifiers.clear()
    obj.data=mesh
    mesh.materials.append(mat)
    # 沿折面用平面着色，避免重新磨成圆管；纵向密集站位保持轮廓连贯。
    for polygon in mesh.polygons:polygon.use_smooth=False
    return obj


def richer_starfield():
    """基于三维坐标的星点、云层与局部旋臂，移除首稿的线圈占位。"""
    mat=bpy.data.materials.new('星空空间带_v02程序化演示')
    mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
    def mathnode(op,a,b=None):
        n=nodes.new('ShaderNodeMath');n.operation=op
        for index,value in enumerate((a,b)):
            if value is None:continue
            if isinstance(value,(int,float)):n.inputs[index].default_value=value
            else:links.new(value,n.inputs[index])
        return n.outputs[0]
    coordinates=nodes.new('ShaderNodeTexCoord')
    xyz=nodes.new('ShaderNodeSeparateXYZ');links.new(coordinates.outputs['Generated'],xyz.inputs[0])
    x=mathnode('SUBTRACT',xyz.outputs['X'],.62)
    y=mathnode('MULTIPLY',mathnode('SUBTRACT',xyz.outputs['Y'],.54),1.35)
    radius=mathnode('SQRT',mathnode('ADD',mathnode('MULTIPLY',x,x),mathnode('MULTIPLY',y,y)))
    angle=mathnode('ARCTAN2',y,x)
    arm=mathnode('ADD',mathnode('MULTIPLY',angle,2),mathnode('MULTIPLY',radius,38))
    arm=mathnode('POWER',mathnode('MAXIMUM',mathnode('COSINE',arm),0),2)
    envelope=mathnode('EXPONENT',mathnode('MULTIPLY',radius,-17))
    density=mathnode('MULTIPLY',envelope,mathnode('ADD',.22,mathnode('MULTIPLY',arm,.78)))
    core=mathnode('EXPONENT',mathnode('MULTIPLY',radius,-90))
    cloud=nodes.new('ShaderNodeTexNoise');cloud.inputs['Scale'].default_value=4.7;cloud.inputs['Detail'].default_value=4
    links.new(coordinates.outputs['Generated'],cloud.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(.001,.002,.008,1)
    ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(.035,.018,.09,1)
    links.new(cloud.outputs['Fac'],ramp.inputs['Fac'])
    stars=nodes.new('ShaderNodeTexVoronoi');stars.inputs['Scale'].default_value=64
    links.new(coordinates.outputs['Generated'],stars.inputs['Vector'])
    points=mathnode('LESS_THAN',stars.outputs['Distance'],.052)
    # 节点颜色相加只是Blender观察效果；引擎迁移需另做材质方案。
    colors=ramp.outputs['Color']
    for strength,color in [(density,(.26,.21,.52,1)),(core,(.75,.8,1,1)),(points,(.8,.86,1,1))]:
        scale=nodes.new('ShaderNodeMixRGB');scale.blend_type='MULTIPLY';scale.inputs[0].default_value=1
        scale.inputs[1].default_value=color;links.new(strength,scale.inputs[2])
        add=nodes.new('ShaderNodeMixRGB');add.blend_type='ADD';add.inputs[0].default_value=1
        links.new(colors,add.inputs[1]);links.new(scale.outputs[0],add.inputs[2]);colors=add.outputs[0]
    emission=nodes.new('ShaderNodeEmission');emission.inputs['Strength'].default_value=1.05
    links.new(colors,emission.inputs['Color']);out=nodes.new('ShaderNodeOutputMaterial');links.new(emission.outputs[0],out.inputs['Surface'])
    return mat


def main():
    base.OUT=OUT;base.PREVIEW=OUT/'previews';base.BLEND=OUT/'endgame_refinement_v02.blend'
    base.build()
    scene=bpy.data.scenes['终局旗舰_结构样稿'];bpy.context.window.scene=scene
    navy=painted_material('靛蓝绘画明暗_v02',[(.012,.019,.043),(.03,.047,.092),(.09,.12,.20)])
    silver=painted_material('银白绘画明暗_v02',[(.14,.19,.29),(.36,.44,.58),(.68,.76,.88)])
    inset=painted_material('深色内壳_v02',[(.007,.012,.025),(.016,.027,.052),(.04,.065,.12)])
    gold=bpy.data.materials['主轴暖金_占位']
    hull=bpy.data.collections['实体舰体'];fx=bpy.data.collections['中央星空_视觉占位']
    fore=[(50,0,0,.08,.06),(44,0,0,2.2,.7),(33,0,0,5.8,1.9),(21,0,0,8.6,3.1),(9,0,0,9.3,3.5),(2,0,0,8.2,3.5)]
    aft=[(-12.6,0,0,8.2,3.5),(-19,0,0,8.8,3.6),(-30,0,0,7.6,3.0),(-41,0,0,5.3,2.3),(-45,0,0,4.6,1.9)]
    replace_shell(bpy.data.objects['主舰体_前'],fore,navy,core=True,end_curve={'last':2})
    replace_shell(bpy.data.objects['主舰体_后'],aft,navy,core=True,end_curve={'first':-2})
    front=[(46,3.4,2.6,.08,.06),(36,6.4,4,1.9,.6),(24,9.2,4.8,3,1.05),
           (12,10.3,5.2,3.8,1.25),(4,10.1,4.9,3.4,1),(0,9,4.4,.08,.05)]
    rear=[(-11.5,9,4.3,.08,.05),(-20,10.8,4.8,3.3,1.05),(-30,10,4.3,3,1),
          (-42,7,3,2,.7),(-47,4,2.5,.08,.05)]
    for bank,sx,sz in [('A',-1,1),('B',1,1),('C',-1,-1),('D',1,-1)]:
        for label,rows in [('前',front),('后',rear)]:
            replace_shell(bpy.data.objects[f'悬隔外壳_{bank}_{label}'],rows,silver,sx,sz)
            # 内侧深色壳与外壳有独立厚度和退让间隙；不填回中央超常断口。
            inner=[(y,x-.25,z-1.12*h-.18,w*.86,h*.30) for y,x,z,w,h in rows]
            obj=bpy.data.objects.new(f'悬隔内衬_{bank}_{label}',bpy.data.meshes.new('临时内衬'))
            hull.objects.link(obj);replace_shell(obj,inner,inset,sx,sz)
            # 只在内缘设置少量结构导边，不沿所有面平均描金。
            edge=[(sx*(x-.72*w),y,sz*(z+.14*h)) for y,x,z,w,h in samples(rows,4)][2:-2]
            base.tube(f'内缘刻度_{bank}_{label}',edge,.018,fx,gold)
    for obj in list(fx.objects):
        if obj.name.startswith('星空旋臂_'):bpy.data.objects.remove(obj,do_unlink=True)
    # 主轴线跟随真实屋脊高度，避免被新增折面间歇遮住。
    bpy.data.objects.remove(bpy.data.objects['主轴细金线'],do_unlink=True)
    axis=[(0,y,h+.06) for y,x,z,w,h in samples(fore,7)]
    axis += [(0,-1,3.71),(0,-5.4,3.76),(0,-9.6,3.71)]
    axis += [(0,y,h+.06) for y,x,z,w,h in samples(aft,7)]
    base.tube('主轴细金线',axis,.035,fx,gold)
    space=bpy.data.objects['星空缺口_空间带占位'];space.data.materials.clear();space.data.materials.append(richer_starfield())
    # 增加实体发射接口的内层，维持16个既有标识与前向朝向。
    manifest=json.loads((OUT/'blockout_manifest.json').read_text(encoding='utf-8'))
    old_positions={r['id']:list(r['position']) for r in manifest['locators']}
    bpy.context.view_layer.update()
    physical=[o for o in hull.objects if o.type=='MESH']
    bvh=base.world_bvh(physical)
    adjustments=[]
    for row in manifest['locators']:
        obj=bpy.data.objects[row['id']];start=obj.location.copy();sx=-1 if start.x<0 else 1
        step=0
        while bvh.ray_cast(obj.location+Vector((0,.15,0)),Vector((0,1,0)),120)[0] is not None:
            step+=.15;obj.location.x+=sx*.15
            if step>2:raise RuntimeError('精修后发射点需重新设计：'+row['id'])
        delta=obj.location-start
        if delta.length:
            housing=bpy.data.objects['发射接口_'+row['id']]
            housing.location+=delta
            bpy.data.objects['接口指示_'+row['id']].location+=delta
            adjustments.append({'id':row['id'],'delta':list(delta)})
        row['position']=list(obj.location)
    bpy.context.view_layer.update();bvh=base.world_bvh([o for o in hull.objects if o.type=='MESH'])
    for row in manifest['locators']:
        assert bvh.ray_cast(Vector(row['position'])+Vector((0,.15,0)),Vector((0,1,0)),120)[0] is None,row['id']
    manifest.update({'status':'sculpted_refinement_pending_visual_review','blend':base.BLEND.relative_to(ROOT).as_posix(),
                     'parent_source':'art/models/aemusa_endgame_blockout_v01/endgame_blockout_v01.blend',
                     'locator_adjustments':adjustments,'starfield':'procedural cloud/star/spiral demonstration, not game-ready material',
                     'shading':'EEVEE painted-value material prototype; final game shader not implemented'})
    # 便于检查星空与边界，在原三图外只补一张近景，不扩测游戏。
    details=base.camera(scene,'中央星空近景',(-28,14,27),(0,-5.4,0),29,22,(1400,1060))
    scene.camera=bpy.data.objects['概念角度']
    if hasattr(bpy.data,'orphans_purge'):bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(base.BLEND))
    (OUT/'blockout_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    base.verify()
    base.render(['oblique','three_view','geometry'])
    bpy.context.window.scene=bpy.data.scenes['终局旗舰_结构样稿']
    scene=bpy.context.scene;scene.camera=bpy.data.objects['中央星空近景']
    scene.render.resolution_x,scene.render.resolution_y=1400,1060
    scene.render.filepath=str(OUT/'previews/core_detail.png')
    bpy.ops.render.render(write_still=True,scene=scene.name)
    print('REFINEMENT_COMPLETE '+json.dumps({'locator_adjustments':adjustments,'source':str(base.BLEND)},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
