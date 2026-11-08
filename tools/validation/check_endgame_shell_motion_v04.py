"""回读 PDX 蒙皮与动作，检查一圈的实体可见性、星空视线及十六个固定发射点。"""

import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/art"))
from build_endgame_shell_motion_v04 import AX, AY, BONES, COS_CAM, CROSS, EXPORT, FIXED_BONE, FPS, LENGTH, NEAR, OLD, OUT, PARTS, PERIOD, SIN_CAM, VIEW, WAIST
from endgame_shell_profiles import STYLES, load_shells
from io_pdx_mesh import pdx_data
from io_pdx_mesh.pdx_blender.blender_import_export import swap_coord_space


class Surface:
    def __init__(self):
        self.points = []
        self.triangles = []
        self.uvs = []

    def add(self, tri):
        n = len(self.points)
        self.points.extend(tri)
        self.triangles.append((n,n+1,n+2))

    def tree(self, rotation=None):
        points = self.points if rotation is None else [rotation @ p for p in self.points]
        return BVHTree.FromPolygons(points,self.triangles,all_triangles=True)


def read_clip(folder):
    clip = pdx_data.read_meshfile(str(folder/"aef04_shell_orbit.anim"))
    info, samples = clip.find("info"), clip.find("samples")
    assert info.get("fps")==[float(FPS)] and info.get("sa")==[PERIOD+1] and info.get("j")==[3]
    assert info.find(FIXED_BONE).get("sa")==[""]
    names = [b.tag for b in info if b.get("sa")==["q"]]
    assert set(names)==set(BONES.values()) and set(samples.attrib)=={"q"}
    assert all(b.get("t")==[0,0,0] and b.get("s")==[1] for b in info)
    quats = samples.get("q")
    assert len(quats)==4*len(names)*(PERIOD+1)
    phases = []
    previous = {}
    steps = {bank: [] for bank in BONES}
    shapes = load_shells()
    for i in range(PERIOD+1):
        state = {}
        for bank,curve in (("fore",shapes[0]),("aft",shapes[2])):
            j = 4*(i*len(names)+names.index(BONES[bank]))
            x,y,z,w = quats[j:j+4]
            q = Quaternion((w,x,y,z))
            expected = Quaternion((0,1,0), -curve.phase(i*math.tau/PERIOD))
            actual = swap_coord_space(q)
            assert abs(actual.dot(expected))>.99999 and abs(q.magnitude-1)<1e-5
            if bank in previous:
                dot = q.dot(previous[bank])
                assert .998 < dot <= 1.000001
                steps[bank].append(math.degrees(2*math.acos(min(1,dot))))
            previous[bank] = q
            state[bank] = actual.to_matrix()
        phases.append(state)
    assert all(abs(sum(s)-360)<.25 for s in steps.values())
    return phases, {k:round(sum(s),2) for k,s in steps.items()}


def read_meshes(folder):
    groups = {k: Surface() for k in ("fixed","fore","aft","star")}
    samples = {s: [] for s in STYLES}
    guns, totals = [], {}
    for part in PARTS:
        name = "aef03_"+part+".mesh"
        doc = pdx_data.read_meshfile(str(folder/name))
        baseline = pdx_data.read_meshfile(str(OLD/"export"/name))
        locs = {l.tag:l.attrib for l in doc.findall("./locator/*")}
        assert locs == {l.tag:l.attrib for l in baseline.findall("./locator/*")}
        for tag,l in locs.items():
            if tag.startswith("t_gun_"):
                guns.append((tag,swap_coord_space(Vector(l["p"]))))
        shape = doc.find("./object/*")
        skeleton = shape.find("skeleton")
        ids = {}
        if part=="mid":
            ids = {b.tag:b.get("ix")[0] for b in skeleton}
            assert set(ids)=={FIXED_BONE,*BONES.values()}
            for b in skeleton:
                if b.tag!=FIXED_BONE:
                    assert b.get("pa")==[ids[FIXED_BONE]]
                assert b.get("tx")==[1,0,0,0,1,0,0,0,1,0,0,0], b.get("tx")
        totals[part] = 0
        for mesh in shape.findall("mesh"):
            diffuse = mesh.find("material").get("diff")[0]
            active = diffuse == "aef04_shell_diffuse.dds"
            points = [swap_coord_space(Vector(v)) for v in zip(*[iter(mesh.get("p"))]*3)]
            uv = mesh.get("u0")
            assert len(uv)==2*len(points) and all(0 <= u <= 1 for u in uv)
            assert all(math.isfinite(x) for x in mesh.get("p"))
            if part=="mid":
                skin = mesh.find("skin")
                stride = skin.get("bones")[0]
                indices,weights = skin.get("ix"),skin.get("w")
                assert len(weights)==len(indices)==stride*len(points)
                for i in range(len(points)):
                    k = int(uv[2*i+1]*4) if active else 0
                    want = BONES[STYLES[k].split("_")[0]] if active else FIXED_BONE
                    row = [(indices[j],weights[j]) for j in range(i*stride,(i+1)*stride) if weights[j]]
                    assert row==[(ids[want],1)]
            tri = mesh.get("tri")
            totals[part] += len(tri)//3
            for i,j,k in zip(*[iter(tri)]*3):
                verts = (points[i],points[k],points[j])
                if active:
                    zones = [uv[n*2+1]*4 for n in (i,j,k)]
                    layer = int(zones[0])
                    assert all(int(a)==layer for a in zones)
                    item = STYLES[layer]
                    groups[item.split("_")[0]].add(verts)
                    # 按 UV 色带取银面中心，排除特意画成深靛色的内缘。
                    band_row = ((sum(zones)/3-layer)*128-5.5)/117*8
                    if band_row<2 or band_row>5.5:
                        v0,v1,v2 = verts
                        cross = (v1-v0).cross(v2-v0)
                        area = .5*cross.length
                        if area>1e-8:
                            samples[item].append(((v0+v1+v2)/3,cross.normalized(),area))
                else:
                    groups["fixed"].add(verts)
                    if diffuse=="aef03_star_diffuse.dds":
                        groups["star"].add(verts)
                        groups["star"].uvs.append([Vector((uv[2*n],1-uv[2*n+1],0)) for n in (i,k,j)])
    assert len(guns)==16 and len({tag for tag,_ in guns})==16
    return groups, samples, guns, totals


def galaxy_landmark(star, trees, folder):
    # 由实际 UV 贴图在当前镜头下找最亮的一片星系。这样不会误把金线下的固定点当成星核。
    path = folder/"aef03_star_diffuse.dds"
    image = bpy.data.images.load(str(path if path.exists() else OLD/"export"/path.name), check_existing=True)
    pixels = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(pixels)
    width,height = image.size
    luma = pixels.reshape(height,width,4)[:,:,:3] @ np.array((.2126,.7152,.0722),dtype=np.float32)
    u = LENGTH*COS_CAM + NEAR*SIN_CAM
    right, up = u*AX-CROSS*AY, -u*AY-CROSS*AX
    center = Vector((0,-WAIST(-4.8),0))
    h,w,step = 65,109,.24
    values = np.zeros((h,w),dtype=float)
    hits = {}
    for j in range(h):
        for i in range(w):
            origin = center + (i-w//2)*step*right + (j-h//2)*step*up + 90*VIEW
            point, _, idx, _ = trees["star"].ray_cast(origin,-VIEW,150)
            if point is None or trees["fixed"].ray_cast(point+.015*VIEW,VIEW,130)[0] is not None:
                continue
            a,b,c = (star.points[k] for k in star.triangles[idx])
            tex = barycentric_transform(point,a,b,c,*star.uvs[idx])
            x,y = int(tex.x*(width-1)),int(tex.y*(height-1))
            values[j,i] = luma[y,x]
            hits[j,i] = point
    # 局部均值抑制单个亮星，选取连续旋臂的亮心。
    padded = np.pad(values,2)
    blurred = sum(padded[j:j+h,i:i+w] for i in range(5) for j in range(5))
    j,i = max(hits,key=lambda k:blurred[k])
    patch = [hits[j+dy,i+dx] for dy in (-3,0,3) for dx in (-3,0,3) if (j+dy,i+dx) in hits]
    return hits[j,i], patch


def check_views(groups, samples, guns, phases, folder):
    trees = {k: surf.tree() for k,surf in groups.items()}
    nucleus, star_points = galaxy_landmark(groups["star"],trees,folder)
    baseline = {}
    min_ratio = {"fore":1.0,"aft":1.0,"total":1.0}
    worst_frame = 0
    count_min, bank_min, stars_min, star_center = 4,2,9,0
    collisions, ray_hits = [], set()
    for frame, rotation in enumerate(phases[:-1]):
        inverse = {k:m.transposed() for k,m in rotation.items()}
        rays = {k:m @ VIEW for k,m in inverse.items()}

        def clear(point):
            origin = point + VIEW*.012
            if trees["fixed"].ray_cast(origin,VIEW,130)[0] is not None:
                return False
            return all(trees[k].ray_cast(inverse[k] @ origin,rays[k],130)[0] is None for k in BONES)

        visible = {}
        for name,points in samples.items():
            rot = rotation[name.split("_")[0]]
            area = 0
            for center,normal,weight in points:
                incidence = (rot @ normal).dot(VIEW)
                if incidence > .04 and clear(rot @ center):
                    area += weight*incidence
            visible[name] = area
        if frame==0:
            baseline = visible.copy()
            assert all(v>0 for v in baseline.values())
        clear_parts = {n for n in STYLES if visible[n] > .12*baseline[n]}
        count_min = min(count_min,len(clear_parts))
        bank_min = min(bank_min,len({n.split("_")[0] for n in clear_parts}))
        for k in min_ratio:
            keys = [n for n in STYLES if k=="total" or n.startswith(k)]
            ratio = sum(visible[n] for n in keys)/sum(baseline[n] for n in keys)
            if ratio < min_ratio[k]:
                min_ratio[k]=ratio
                if k=="total":
                    worst_frame=frame+1
        sight = [clear(p) for p in star_points]
        star_center += clear(nucleus)
        stars_min = min(stars_min,sum(sight))
        for tag,v in guns:
            direction = Vector((0,-1,0))
            if any(trees[k].ray_cast(inverse[k] @ (v+direction*.05),inverse[k] @ direction,130)[0] is not None for k in BONES):
                ray_hits.add(tag)
        if frame%6==0:
            moving = {k: groups[k].tree(rotation[k]) for k in BONES}
            pairs = (("fore","aft",moving["fore"],moving["aft"]),
                     ("fixed","fore",trees["fixed"],moving["fore"]),("fixed","aft",trees["fixed"],moving["aft"]))
            for a,b,left,right in pairs:
                if left.overlap(right):
                    collisions.append([frame+1,a,b])
    return {"camera":"第二稿固定斜视", "poses":PERIOD, "visible_surface_measure":"按正面投影面积累计、由实际导出三角形中心向相机检测遮挡",
            "visible_threshold_per_shell":.12, "minimum_substantial_shells":count_min,"minimum_visible_banks":bank_min,
            "minimum_projected_fraction_vs_rest":{k:round(v,4) for k,v in min_ratio.items()},"weakest_frame":worst_frame,
            "star_patch_minimum_samples_visible":stars_min,"star_patch_samples":len(star_points),
            "star_center_visible_poses":star_center,"star_landmark_native_xyz":[round(v,3) for v in nucleus],
            "beam_hits":sorted(ray_hits), "collision_sample_poses":PERIOD//6,
            "triangle_overlaps":collisions}


def run():
    installed = "--installed" in sys.argv
    folder = ROOT/"mod/gfx/models/aemusa_endgame_v03" if installed else EXPORT
    if installed:
        assert all((folder/f.name).read_bytes()==f.read_bytes() for f in EXPORT.iterdir() if f.is_file())
    phases, revolutions = read_clip(folder)
    groups,samples,guns,tris = read_meshes(folder)
    evidence = check_views(groups,samples,guns,phases,folder)
    result = {"input":folder.relative_to(ROOT).as_posix(),"triangles":tris,"total_triangles":sum(tris.values()),
              "fixed_locators_identical_to_v03":True,"T_locators":len(guns),"sample_rate":FPS,"loop_seconds":PERIOD/FPS,
              "bone_travel_degrees":revolutions,"camera_check":evidence,"engine_observation":"not_measured_by_this_check"}
    print("AEF04_CHECK",json.dumps(result,ensure_ascii=False),flush=True)
    assert evidence["minimum_visible_banks"]==2 and evidence["minimum_substantial_shells"]>=2
    assert evidence["star_patch_minimum_samples_visible"]>=1
    assert not evidence["beam_hits"] and not evidence["triangle_overlaps"]
    (OUT/"verification.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    run()
