"""由开发版 v03 舰模与第二稿截面生成带骨骼的三段 PDX、循环动作和作者源。"""

import argparse
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from endgame_shell_profiles import ROOT, OUT, EXPORT, Spline, clamp, load_shells, uv
import build_endgame_runtime_v03 as baseline

sys.path.insert(0, str(baseline.ADDON))
from io_pdx_mesh import pdx_data
from io_pdx_mesh.pdx_blender.blender_import_export import export_animfile, export_meshfile

OLD = ROOT / "art/models/aemusa_endgame_runtime_v03"
BLEND = OUT / "endgame_shell_motion_v04.blend"
PREVIEWS = OUT / "previews"
PARTS = ("bow", "mid", "stern")
FIXED_BONE = "aef_keel"
BONES = {"fore": "aef_forward_shells", "aft": "aef_aft_shells"}
FPS, SECONDS = 24, 8
PERIOD = FPS * SECONDS
# 第二稿的固定斜视投影。生成的顶点使用原版舰首为 -Y 的 Blender 坐标。
UNIT = .056
AX = 1 / math.sqrt(1 + .281**2)
AY = -.281 * AX
SIN_CAM = .30
COS_CAM = math.sqrt(1 - SIN_CAM**2)
PITCH = math.radians(36)
CROSS = Vector((math.sin(PITCH), 0, -math.cos(PITCH)))
NEAR = Vector((math.cos(PITCH), 0, math.sin(PITCH)))
LENGTH = Vector((0, 1, 0))
VIEW = COS_CAM*NEAR - SIN_CAM*LENGTH
WAIST = Spline([-50,-45,-30,-12.6,-5.3,2,9,33,50],
               [-50,-45,-32,-23,-12,-1,6,33,50])


def select_only(objects, active):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = active


def remove_previous_mantles(mesh):
    # v03 前后段的靛蓝主体与尾灯分属图集 0、6，其他面来自旧壳、内衬及刻线。
    bm = bmesh.new()
    bm.from_mesh(mesh)
    uv_layer = bm.loops.layers.uv.active
    discard = []
    for face in bm.faces:
        u, v = face.loops[0][uv_layer].uv
        tile = min(3, int(u*4)) + 4*(1-min(1, int(v*2)))
        if tile not in (0,6):
            discard.append(face)
    assert discard and len(discard) < len(bm.faces)
    bmesh.ops.delete(bm, geom=discard, context="FACES")
    bm.to_mesh(mesh)
    bm.free()


def fixed_sections():
    sections = {p: bpy.data.objects["aef03_"+p] for p in PARTS}
    for part, obj in sections.items():
        mesh = obj.data
        is_star = set()
        emitters = set()
        if part == "mid":
            for face in mesh.polygons:
                if mesh.materials[face.material_index].name.startswith("aef03_star"):
                    is_star.update(face.vertices)
        else:
            remove_previous_mantles(mesh)
            if part == "stern":
                layer = mesh.uv_layers.active
                for face in mesh.polygons:
                    u, v = layer.data[face.loop_start].uv
                    if u > .5 and v < .5:
                        emitters.update(face.vertices)
        for v in mesh.vertices:
            x, y, z = v.co
            # 近舷切口向前后退开，星空从实体内侧露出。不同部件共用切口函数。
            cross = clamp(x/8.4,-1.12,1.12)
            front = math.exp(-((y-2)/5.0)**2)
            aft = math.exp(-((y+12.6)/5.0)**2)
            new_y = WAIST(y) + (front-aft)*3.0*(-cross+.32*cross*cross)
            if v.index in is_star:
                depth = math.sin(math.pi * clamp((y+12.6)/14.6, 0, 1))**2
                x *= .96 - .12*depth
                x += 1.6*depth
                z *= .93 - .23*depth
            elif part=="mid" and abs(x)<.22:
                x *= 1.7
                z += .055
            if part in ("mid","stern") and y < -29:
                t = clamp((-29-y)/16,0,1)
                taper = t*t*(3-2*t)
                new_y += 1.8*taper*min(1,(abs(x)/4.6)**2)
                if v.index in emitters:
                    new_y += .52
                else:
                    x *= 1-.42*taper
                z *= 1-.32*taper
            v.co = (-x, -new_y, z)
        mesh.update()
    locators = []
    for obj in bpy.context.scene.objects:
        if obj.type == "EMPTY" and obj.get("pdx_locator_name"):
            obj.location.x *= -1
            obj.location.y *= -1
            locators.append(obj)
    bpy.context.view_layer.update()
    return sections, locators


class Clearance:
    """用真实舰身外缘与固定发射点限定银壳整圈扫过的半径。"""

    step = .25

    def __init__(self, sections, locators):
        self.radius = {}
        self.emitters = [obj.location.copy() for obj in locators if obj["pdx_locator_name"].startswith("t_gun_")]
        assert len(self.emitters) == 16
        for obj in sections.values():
            mesh = obj.data
            for edge in mesh.edges:
                a, b = (mesh.vertices[i].co for i in edge.vertices)
                if a.y > b.y:
                    a, b = b, a
                lo, hi = math.floor(a.y/self.step), math.ceil(b.y/self.step)
                for j in range(lo, hi+1):
                    t = clamp((j*self.step-a.y)/(b.y-a.y), 0, 1) if b.y > a.y else 0
                    v = a.lerp(b, t)
                    r = math.hypot(v.x,v.z)
                    if b.y == a.y:
                        r = max(r, math.hypot(b.x,b.z))
                    self.radius[j] = max(self.radius.get(j,0),r)

    def bounds(self, y):
        j = math.floor(y/self.step)
        inside = max(self.radius.get(i,0) for i in range(j-1,j+3)) + .62
        outside = 19.0
        for v in self.emitters:
            # 炮口后方渐渐放宽半径，壳脊跨过这段纵坐标时保持连续。
            safe = math.hypot(v.x,v.z)-.38
            t = clamp((y-v.y-.5)/12.0,0,1)
            outside = min(outside, safe+(19-safe)*t*t*(3-2*t))
        return inside, outside

    def fit(self, section):
        # 整个截面共用半径映射，使近侧与背侧在运动中具有真实厚度。
        original_r = [math.hypot(b,c) for _, b, c in section]
        r0, r1 = min(original_r), max(original_r)
        fitted = list(section)
        for _ in range(3):
            ys = [-50 + (u-SIN_CAM*c)/COS_CAM for u, b, c in fitted]
            bounds = [self.bounds(y) for y in ys]
            lo = max(x[0] for x in bounds)
            hi = min(x[1] for x in bounds)
            if hi <= lo:
                raise ValueError(f"银壳和发射点之间空间不足，Y={ys[0]:.2f}")
            scale = min(1, (hi-lo)/max(r1-r0,1e-8))
            offset = clamp(0, lo-r0*scale, hi-r1*scale)
            fitted = [(u, b*(scale+offset/max(r,1e-8)), c*(scale+offset/max(r,1e-8)))
                      for (u,b,c), r in zip(section, original_r)]
        return [Vector((0,-50+(u-SIN_CAM*c)/COS_CAM,0)) + CROSS*b + NEAR*c for u,b,c in fitted]


def shell_ring(shell, s, fit):
    x, heights, center = shell.slice(s)
    thickness = (0, .13, .21, .13, 0, -.17, -.254, -.145)
    width = heights[4]-heights[0]
    midpoint = .5*(heights[0]+heights[4])
    # 在实际舰体上，近侧前壳的后尖原会扫过旋臂亮心。只把这一端向舰艏收回。
    t = clamp((s-.55)/.45,0,1)
    shorten = 6.2*t*t*(3-2*t) if shell.name=="fore_near" else 0
    coordinates = []
    for y, relief in zip(heights, thickness):
        u = (x-37)*AX + (y-693)*AY
        b = -(x-37)*AY + (y-693)*AX
        c = center + width*relief*shell.motion["relief_scale"] + shell.motion["transverse_slope"]*AX*(y-midpoint)
        coordinates.append((u*UNIT - COS_CAM*shorten, b*UNIT, c*UNIT))
    return fit.fit(coordinates)


def build_shell(shell, index, material, group, fit):
    stations = []
    for a,b in zip(shell.x, shell.x[1:]):
        steps = math.ceil((b-a)/10)
        stations.extend(a + k*(b-a)/steps for k in range(steps))
    stations.append(shell.x[-1])
    fractions = [(x-shell.x[0])/(shell.x[-1]-shell.x[0]) for x in stations]
    vertices, rings, faces, uvs = [], [], [], []
    for i,s in enumerate(fractions):
        points = shell_ring(shell, s, fit)
        if i in (0,len(fractions)-1):
            rings.append([len(vertices)]*8)
            vertices.append(points[0])
        else:
            rings.append(list(range(len(vertices),len(vertices)+8)))
            vertices.extend(points)
    for i in range(len(rings)-1):
        for row in range(8):
            next_row = (row+1)%8
            corners = [(rings[i][row], fractions[i], row),
                       (rings[i][next_row], fractions[i], row+1),
                       (rings[i+1][next_row], fractions[i+1], row+1),
                       (rings[i+1][row], fractions[i+1], row)]
            for tri in ((0,1,2),(0,2,3)):
                points = [corners[n] for n in tri]
                if len({p[0] for p in points}) == 3:
                    faces.append([p[0] for p in points])
                    uvs.append([uv(index,p[1],p[2]) for p in points])
    mesh = bpy.data.meshes.new("aef04_"+shell.name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    layer = mesh.uv_layers.new(name="UVMap")
    for face, coords in zip(mesh.polygons,uvs):
        face.use_smooth = True
        for loop, coord in zip(face.loop_indices, coords):
            layer.data[loop].uv = coord
    # 沿纵向插值表面法线，在大折面分界处保留利落的壳脊。
    creases = {tuple(sorted((a[row],b[row]))) for a,b in zip(rings, rings[1:]) for row in (0,2,4,6)}
    for edge in mesh.edges:
        edge.use_edge_sharp = tuple(sorted(edge.vertices)) in creases
    mesh.update()
    obj = bpy.data.objects.new(mesh.name, mesh)
    group.objects.link(obj)
    return obj


def bind(obj, armature, bone):
    group = obj.vertex_groups.new(name=bone)
    group.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    mod = obj.modifiers.new("舰体刚性蒙皮", "ARMATURE")
    mod.object = armature


def create_rig(scene, pieces, profiles, middle):
    bones = bpy.data.armatures.new("aef04_shell_rig")
    rig = bpy.data.objects.new(bones.name, bones)
    scene.collection.objects.link(rig)
    select_only([rig], rig)
    bpy.ops.object.mode_set(mode="EDIT")
    fixed = bones.edit_bones.new(FIXED_BONE)
    fixed.head, fixed.tail = (0,0,0), (0,3,0)
    for index,name in enumerate(BONES.values()):
        bone = bones.edit_bones.new(name)
        bone.head, bone.tail = (0,0,0), (0,2-index*.6,0)
        bone.parent = fixed
    bpy.ops.object.mode_set(mode="OBJECT")
    bind(middle, rig, FIXED_BONE)
    for profile, obj in zip(profiles,pieces):
        bind(obj, rig, BONES[profile.name.split("_")[0]])
    prefs = bpy.context.preferences.edit
    interpolation = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, PERIOD
    try:
        for name,profile in zip(BONES.values(), (profiles[0],profiles[2])):
            bone = rig.pose.bones[name]
            bone.rotation_mode = "XYZ"
            for i in range(PERIOD+1):
                bone.rotation_euler.y = -profile.phase(math.tau*i/PERIOD)
                bone.keyframe_insert("rotation_euler", index=1, frame=i+1, group=name)
    finally:
        prefs.keyframe_new_interpolation_type = interpolation
    rig.animation_data.action.name = "aef04_shell_orbit_8s"
    scene.frame_set(1)
    return rig


def camera_scene(scene):
    cam = scene.camera
    u = LENGTH*COS_CAM + NEAR*SIN_CAM
    right, up = u*AX-CROSS*AY, -u*AY-CROSS*AX
    target = Vector((0,-50,0)) + UNIT*((836-37)*right - (470.5-693)*up)
    cam.location = target + 150*VIEW
    cam.rotation_euler = Matrix((right,up,VIEW)).transposed().to_euler()
    cam.name = "第二稿_固定斜视"
    cam.data.ortho_scale, cam.data.clip_end = 1672*UNIT*1.055, 400
    scene.render.resolution_x, scene.render.resolution_y = 960,540
    scene.render.resolution_percentage = 100
    scene.eevee.taa_render_samples = 32
    # 柔和的主光照亮上壳，低位轮廓光使旋到腹侧的厚边可见。
    from build_endgame_flagship_blockout import area
    for obj in list(scene.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    area(scene,"上侧主光",(16,-46,72),39000,60)
    area(scene,"冷色轮廓光",(-42,29,35),33500,50)
    low = area(scene,"腹侧补光",(38,22,-38),21500,50)
    low.data.color = (.72,.80,1.0)
    for obj in scene.objects:
        if obj.type == "LIGHT":
            obj.data.use_shadow = False
    scene.world.use_nodes = True
    background = next(n for n in scene.world.node_tree.nodes if n.type=="BACKGROUND")
    background.inputs["Color"].default_value = (.068,.088,.146,1)
    background.inputs["Strength"].default_value = .66
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    return cam


def export_parts(sections, pieces, rig, locators):
    mid = sections["mid"]
    select_only([mid, *pieces], mid)
    bpy.ops.object.join()
    for part, obj in sections.items():
        group = bpy.data.collections["aef03_"+part]
        markers = [x for x in locators if x.name in group.objects]
        names = [(x, x.name) for x in markers]
        try:
            for x,_ in names:
                x.name = x["pdx_locator_name"]
            select_only([obj,*markers], obj)
            path = EXPORT / (obj.data.name+".mesh")
            export_meshfile(str(path), exp_mesh=True, exp_skel=(part=="mid"), exp_locs=True, exp_selected=True)
        finally:
            for x,name in names:
                x.name = name
    select_only([rig], rig)
    clip = EXPORT / "aef04_shell_orbit.anim"
    export_animfile(str(clip), frame_start=1, frame_end=PERIOD+1)
    normalize_clip(clip)
    # 银壳是中段的第三个材质子网格。用整圈扫过的径向外缘填写可见性包围盒。
    path = EXPORT / "aef03_mid.mesh"
    tree = pdx_data.read_meshfile(str(path))
    moving = [m for m in tree.findall("./object/*/mesh")
              if m.find("material").get("diff")==["aef04_shell_diffuse.dds"]]
    assert len(moving)==1
    mesh = moving[0]
    coords = list(zip(*[iter(mesh.attrib["p"])]*3))
    radius = max(math.hypot(x,y) for x,y,z in coords)
    low, high = min(v[2] for v in coords), max(v[2] for v in coords)
    mid_z = (low+high)*.5
    mesh.find("aabb").set("min", [-radius,-radius,low])
    mesh.find("aabb").set("max", [radius,radius,high])
    mesh.set("boundingsphere",[0.0,0.0,mid_z,max(math.sqrt(x*x+y*y+(z-mid_z)**2) for x,y,z in coords)])
    pdx_data.write_meshfile(str(path), tree)


def normalize_clip(path):
    # 导出器对每帧矩阵独立分解。等价四元数统一到相邻半球，删除浮点误差引起的缩放通道。
    tree = pdx_data.read_meshfile(str(path))
    info, samples = tree.find("info"), tree.find("samples")
    joints = list(info)
    rotating = [b for b in joints if "q" in b.get("sa")[0]]
    assert {b.tag for b in rotating} == set(BONES.values())
    quats = samples.get("q")
    for j in range(len(rotating)):
        prev = None
        for frame in range(PERIOD+1):
            offset = 4*(frame*len(rotating)+j)
            q = quats[offset:offset+4]
            if prev and sum(a*b for a,b in zip(q,prev)) < 0:
                q = [-v for v in q]
            quats[offset:offset+4] = q
            prev = q
    for channel,expected in (("s",1),("t",0)):
        stream = samples.get(channel,[])
        assert all(abs(v-expected)<1e-5 for v in stream)
        if stream:
            del samples.attrib[channel]
    for b in joints:
        b.set("sa",["q" if b in rotating else ""])
    pdx_data.write_animfile(str(path),tree)


def definitions():
    gfx = ["# 终局旗舰，三段沿用原实体接口。", "objectTypes = {"]
    for part in PARTS:
        name = "aef03_"+part
        tree = pdx_data.read_meshfile(str(EXPORT/(name+".mesh")))
        gfx += ["    pdxmesh = {", f'        name = "{name}_mesh"',
                f'        file = "gfx/models/aemusa_endgame_v03/{name}.mesh"', "        scale = 1.0"]
        if part=="mid":
            gfx.append('        animation = { id = "idle" type = "aef04_shell_orbit_animation" }')
        for shape in tree.findall("./object/*"):
            for i,sub in enumerate(shape.findall("mesh")):
                mat = sub.find("material").attrib
                gfx += ["        meshsettings = {", f'            name = "{shape.tag}"', f"            index = {i}",
                        f'            texture_diffuse = "{mat["diff"][0]}"', f'            texture_normal = "{mat["n"][0]}"',
                        f'            texture_specular = "{mat["spec"][0]}"', '            shader = "PdxMeshShip"', "        }"]
        gfx.append("    }")
    (EXPORT/"_aef03_meshes.gfx").write_text("\n".join(gfx+["}",""]),encoding="utf-8")
    old = (OLD/"export/_aef03_entities.asset").read_text(encoding="utf-8")
    start = old.index('    name = "aef03_mid_entity"')
    end = old.index('\n}',start)
    middle = old[start:end]
    for state in ("idle","moving"):
        needle = f'name = "{state}" state_time = 5'
        assert middle.count(needle)==1
        middle = middle.replace(needle,f'name = "{state}" animation = "idle" looping = yes animation_blend_time = 0.25')
    text = old[:start]+middle+old[end:]
    text = text.replace(text.splitlines()[0],"# 终局旗舰的固定舰身、武器挂点与前后两组旋转银壳。",1)
    text += '\nanimation = {\n    name = "aef04_shell_orbit_animation"\n    file = "aef04_shell_orbit.anim"\n}\n'
    (EXPORT/"_aef03_entities.asset").write_text(text,encoding="utf-8")


def build():
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError("请在独立 --background --factory-startup 进程中构建。")
    EXPORT.mkdir(parents=True, exist_ok=True)
    PREVIEWS.mkdir(exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(OLD/"endgame_runtime_v03.blend"))
    scene = bpy.context.scene
    sections, locators = fixed_sections()
    fit = Clearance(sections,locators)
    profiles = load_shells()
    material = baseline.runtime_material("aef04_shell", EXPORT)
    collection = bpy.data.collections["aef03_mid"]
    pieces = [build_shell(sh,i,material,collection,fit) for i,sh in enumerate(profiles)]
    rig = create_rig(scene,pieces,profiles,sections["mid"])
    camera_scene(scene)
    select_only([rig],rig)
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    export_parts(sections,pieces,rig,locators)
    definitions()
    render("still")
    print("AEF04_EXPORT", str(BLEND), flush=True)


def render(mode):
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    scene = bpy.context.scene
    if mode=="still":
        scene.frame_set(1)
        scene.render.filepath = str(PREVIEWS/"model_oblique.png")
        bpy.ops.render.render(write_still=True)
    else:
        folder = ROOT/"temp/flagship_model_motion_20261107/mesh_frames"
        folder.mkdir(parents=True,exist_ok=True)
        scene.eevee.taa_render_samples = 16
        scene.frame_step = 1
        scene.render.filepath = str(folder/"frame_")
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build","still","frames"))
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    build() if args.mode=="build" else render(args.mode)
