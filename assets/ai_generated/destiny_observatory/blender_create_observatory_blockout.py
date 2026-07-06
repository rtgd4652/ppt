import math
from pathlib import Path

import bpy


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\ai_generated\destiny_observatory")
OUTPUT = ASSET_DIR / "destiny_observatory_blockout.blend"
PREVIEW_QUARTER = ASSET_DIR / "destiny_observatory_blockout_quarter.png"
PREVIEW_FRONT = ASSET_DIR / "destiny_observatory_blockout_front.png"
PREVIEW_SIDE = ASSET_DIR / "destiny_observatory_blockout_side.png"
PREVIEW_TOP = ASSET_DIR / "destiny_observatory_blockout_top.png"


def make_mat(name, color, metallic=0.0, roughness=0.55, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if emission:
            bsdf.inputs["Emission Color"].default_value = emission
            bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def collection(name):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def move_to_collection(obj, target):
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    target.objects.link(obj)


def cube(name, loc, scale, mat, rot=(0.0, 0.0, 0.0), bevel=0.0, target=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("DO_Blockout_Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 1
    if target:
        move_to_collection(obj, target)
    return obj


def cone(name, loc, radius1, radius2, depth, mat, vertices=8, rot=(0.0, 0.0, 0.0), target=None):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=loc,
        rotation=rot,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    if target:
        move_to_collection(obj, target)
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=12, rot=(0.0, 0.0, 0.0), target=None):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=loc,
        rotation=rot,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    if target:
        move_to_collection(obj, target)
    return obj


def torus(name, loc, major, minor, mat, major_segments=64, minor_segments=6, rot=(0.0, 0.0, 0.0), target=None):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=major_segments,
        minor_segments=minor_segments,
        major_radius=major,
        minor_radius=minor,
        location=loc,
        rotation=rot,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    if target:
        move_to_collection(obj, target)
    return obj


def add_locator(coll, name, loc):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "ARROWS"
    obj.empty_display_size = 0.45
    obj.location = loc
    coll.objects.link(obj)
    return obj


def build_blockout():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    lod0 = collection("DO_LOD0")
    locators = collection("DO_Locators")
    collection("DO_LOD1")
    collection("DO_LOD2")
    collection("DO_LOD3")
    collection("DO_Animation_Rigs")

    navy = make_mat("MAT_DO_Navy_Panel", (0.035, 0.085, 0.16, 1.0), metallic=0.25, roughness=0.5)
    silver = make_mat("MAT_DO_Silver_Edge", (0.72, 0.78, 0.84, 1.0), metallic=0.75, roughness=0.28)
    ice = make_mat(
        "MAT_DO_Ice_Crystal",
        (0.35, 0.82, 1.0, 0.62),
        metallic=0.0,
        roughness=0.18,
        emission=(0.12, 0.65, 1.0, 1.0),
        strength=0.7,
    )
    blue = make_mat(
        "MAT_DO_Blue_Emission",
        (0.08, 0.42, 0.85, 1.0),
        emission=(0.04, 0.55, 1.0, 1.0),
        strength=1.2,
    )
    gold = make_mat(
        "MAT_DO_Gold_Solar",
        (0.95, 0.58, 0.14, 1.0),
        metallic=0.65,
        roughness=0.22,
        emission=(1.0, 0.42, 0.08, 1.0),
        strength=0.35,
    )
    black = make_mat("MAT_DO_Black_Seam", (0.006, 0.010, 0.018, 1.0), metallic=0.1, roughness=0.7)

    # Central tower silhouette.
    cone("DO_Bottom_Anchor", (0, 0, -2.55), 1.25, 0.18, 2.6, navy, vertices=8, target=lod0)
    cone("DO_Bottom_Anchor_Ice_Point", (0, 0, -3.95), 0.36, 0.05, 0.9, ice, vertices=8, target=lod0)
    cube("DO_Main_Spire_Base", (0, 0, -0.82), (1.55, 1.55, 0.34), navy, bevel=0.04, target=lod0)
    cube("DO_Main_Spire_Lower", (0, 0, 0.25), (0.92, 0.92, 1.3), navy, bevel=0.05, target=lod0)
    cube("DO_Main_Spire_Upper", (0, 0, 1.9), (0.52, 0.52, 1.15), silver, bevel=0.035, target=lod0)
    cone("DO_Main_Spire_Needle", (0, 0, 3.3), 0.38, 0.05, 1.25, navy, vertices=8, target=lod0)

    # Crystal core.
    cone("DO_Crystal_Core_Upper", (0, 0, 1.15), 0.48, 0.08, 1.55, ice, vertices=8, target=lod0)
    cone("DO_Crystal_Core_Lower", (0, 0, 0.2), 0.08, 0.38, 0.95, ice, vertices=8, target=lod0)

    # Three fate rings, deliberately separated to avoid intersection reads.
    torus("DO_Ring_Inner", (0, 0, 0.85), 1.9, 0.055, blue, major_segments=48, minor_segments=6, target=lod0)
    torus("DO_Ring_Middle", (0, 0, 1.0), 3.0, 0.07, silver, major_segments=64, minor_segments=6, rot=(math.radians(7), 0, 0), target=lod0)
    torus("DO_Ring_Outer", (0, 0, 1.18), 4.35, 0.085, navy, major_segments=72, minor_segments=6, rot=(math.radians(-5), 0, math.radians(12)), target=lod0)
    torus("DO_Ring_Outer_Blue_Trace", (0, 0, 1.21), 4.52, 0.025, blue, major_segments=72, minor_segments=4, rot=(math.radians(-5), 0, math.radians(12)), target=lod0)

    # Top solar crown.
    torus("DO_Solar_Crown", (0, 0, 4.02), 0.82, 0.055, gold, major_segments=40, minor_segments=5, target=lod0)
    torus("DO_Solar_Crown_Inner_Ice", (0, 0, 4.03), 0.53, 0.032, blue, major_segments=36, minor_segments=4, target=lod0)
    for i in range(12):
        angle = math.tau * i / 12
        r = 1.02
        cube(
            f"DO_Solar_Crown_Ray_{i:02d}",
            (math.cos(angle) * r, math.sin(angle) * r, 4.02),
            (0.035, 0.21, 0.035),
            gold,
            rot=(0, 0, angle),
            bevel=0.008,
            target=lod0,
        )

    # Radial arms and lens modules.
    for i in range(8):
        angle = math.tau * i / 8
        arm_len = 3.35 if i % 2 == 0 else 2.65
        x = math.cos(angle) * (arm_len / 2 + 1.1)
        y = math.sin(angle) * (arm_len / 2 + 1.1)
        cube(
            f"DO_Radial_Arm_{i:02d}",
            (x, y, 0.62),
            (arm_len, 0.105, 0.105),
            silver if i % 2 == 0 else navy,
            rot=(0, 0, angle),
            bevel=0.018,
            target=lod0,
        )
        if i % 2 == 0:
            lx = math.cos(angle) * 4.85
            ly = math.sin(angle) * 4.85
            cylinder(
                f"DO_Lens_Module_{i:02d}",
                (lx, ly, 0.72),
                0.23,
                0.32,
                ice,
                vertices=12,
                rot=(math.radians(90), 0, angle),
                target=lod0,
            )
            torus(
                f"DO_Lens_Frame_{i:02d}",
                (lx, ly, 0.72),
                0.30,
                0.025,
                silver,
                major_segments=24,
                minor_segments=4,
                rot=(math.radians(90), 0, angle),
                target=lod0,
            )

    # Small docking / construction platforms around the outer orbit plane.
    for i, angle in enumerate((math.radians(30), math.radians(150), math.radians(250), math.radians(330))):
        px = math.cos(angle) * 5.8
        py = math.sin(angle) * 5.8
        cube(
            f"DO_Dock_Platform_{i:02d}",
            (px, py, -0.18),
            (0.78, 0.32, 0.10),
            navy,
            rot=(0, 0, angle),
            bevel=0.025,
            target=lod0,
        )
        cube(
            f"DO_Dock_Platform_Edge_{i:02d}",
            (px, py, -0.02),
            (0.70, 0.035, 0.035),
            blue,
            rot=(0, 0, angle),
            bevel=0.006,
            target=lod0,
        )

    for name, loc in {
        "locator_center": (0, 0, 0),
        "locator_ring_inner": (0, 0, 0.85),
        "locator_ring_middle": (0, 0, 1.0),
        "locator_ring_outer": (0, 0, 1.18),
        "locator_core_glow": (0, 0, 1.1),
        "locator_top_crown": (0, 0, 4.0),
    }.items():
        add_locator(locators, name, loc)

    return lod0


def setup_render(camera_name, loc, rot, lens=58):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 32
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 75
    scene.world.color = (0.006, 0.009, 0.014)
    camera_data = bpy.data.cameras.new(camera_name)
    camera = bpy.data.objects.new(camera_name, camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = loc
    camera.rotation_euler = rot
    camera.data.lens = lens
    scene.camera = camera
    return camera


def add_lights():
    key_data = bpy.data.lights.new("DO_Blockout_Key_Light", "AREA")
    key = bpy.data.objects.new("DO_Blockout_Key_Light", key_data)
    bpy.context.scene.collection.objects.link(key)
    key.location = (3.0, -5.0, 6.0)
    key.data.energy = 450
    key.data.size = 5

    fill_data = bpy.data.lights.new("DO_Blockout_Ice_Fill", "POINT")
    fill = bpy.data.objects.new("DO_Blockout_Ice_Fill", fill_data)
    bpy.context.scene.collection.objects.link(fill)
    fill.location = (-4.0, 4.0, 2.0)
    fill.data.color = (0.35, 0.75, 1.0)
    fill.data.energy = 130


def count_tris(coll):
    verts = 0
    tris = 0
    for obj in coll.objects:
        if obj.type != "MESH":
            continue
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        mesh.calc_loop_triangles()
        verts += len(mesh.vertices)
        tris += len(mesh.loop_triangles)
        eval_obj.to_mesh_clear()
    return verts, tris


def render_view(path, camera_name, loc, rot, lens=58):
    setup_render(camera_name, loc, rot, lens)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    lod0 = build_blockout()
    add_lights()
    verts, tris = count_tris(lod0)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    render_view(PREVIEW_QUARTER, "DO_Camera_Quarter", (7.2, -8.2, 5.6), (math.radians(60), 0, math.radians(42)), 54)
    render_view(PREVIEW_FRONT, "DO_Camera_Front", (0, -10.5, 1.4), (math.radians(83), 0, 0), 64)
    render_view(PREVIEW_SIDE, "DO_Camera_Side", (10.5, 0, 1.4), (math.radians(83), 0, math.radians(90)), 64)
    render_view(PREVIEW_TOP, "DO_Camera_Top", (0, 0, 12.0), (0, 0, 0), 70)

    print(f"DESTINY_OBSERVATORY_BLOCKOUT {OUTPUT}")
    print(f"LOD0_STATS verts={verts} tris={tris}")
    print(f"PREVIEWS {PREVIEW_QUARTER} {PREVIEW_FRONT} {PREVIEW_SIDE} {PREVIEW_TOP}")


if __name__ == "__main__":
    main()

