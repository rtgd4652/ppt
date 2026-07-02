import shutil
import sys
from pathlib import Path

import bpy


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\destiny_lord")
MOD_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict")
GAME_MODEL_DIR = MOD_DIR / "gfx" / "models" / "ships" / "destiny_lord"
INPUT_BLEND = ASSET_DIR / "destiny_lord_stage9_refined_A.blend"
BACKUP_DIR = ASSET_DIR / "runtime_backups"
PDX_PLUGIN_ROOT = Path(r"C:\Users\Admin\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default")


sys.path.append(str(PDX_PLUGIN_ROOT))
from io_pdx_mesh.pdx_blender.blender_import_export import export_meshfile  # noqa: E402


SECTIONS = {
    "bow": {
        "collection": "DL_PDX_Bow",
        "mesh_name": "destiny_lord_bow",
        "target": GAME_MODEL_DIR / "destiny_lord_bow.mesh",
    },
    "mid": {
        "collection": "DL_PDX_Mid",
        "mesh_name": "destiny_lord_mid",
        "target": GAME_MODEL_DIR / "destiny_lord_mid.mesh",
    },
    "stern": {
        "collection": "DL_PDX_Stern",
        "mesh_name": "destiny_lord_stern",
        "target": GAME_MODEL_DIR / "destiny_lord_stern.mesh",
    },
}


def backup_existing_meshes():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for data in SECTIONS.values():
        target = data["target"]
        if target.exists():
            backup = BACKUP_DIR / f"{target.stem}.pre_stage9A.mesh"
            if not backup.exists():
                shutil.copy2(target, backup)
                print(f"BACKUP {target.name} -> {backup}")


def load_image(path):
    try:
        return bpy.data.images.load(str(path), check_existing=True)
    except Exception:
        return bpy.data.images.load(str(GAME_MODEL_DIR / "destiny_lord_basecolor_preview.png"), check_existing=True)


def create_pdx_material():
    mat = bpy.data.materials.new("destiny_lord_pdx_ship")
    mat["shader"] = "PdxMeshShip"
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    diffuse = nodes.new("ShaderNodeTexImage")
    diffuse.image = load_image(GAME_MODEL_DIR / "destiny_lord_basecolor.dds")
    specular = nodes.new("ShaderNodeTexImage")
    specular.image = load_image(GAME_MODEL_DIR / "destiny_lord_specular.dds")
    normal_tex = nodes.new("ShaderNodeTexImage")
    normal_tex.image = load_image(GAME_MODEL_DIR / "destiny_lord_normal.dds")
    normal_map = nodes.new("ShaderNodeNormalMap")
    links.new(diffuse.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(specular.outputs["Color"], bsdf.inputs["Roughness"])
    links.new(normal_tex.outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def ensure_uv(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.015)
    bpy.ops.object.mode_set(mode="OBJECT")


def apply_modifiers(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception as exc:
            print(f"WARN modifier apply failed on {obj.name}:{mod.name}: {exc}")


def prepare_section(section_name, data, pdx_mat):
    coll = bpy.data.collections[data["collection"]]
    meshes = [obj for obj in coll.objects if obj.type == "MESH"]
    locators = [obj for obj in coll.objects if obj.type == "EMPTY"]
    if not meshes:
        raise RuntimeError(f"No meshes in {data['collection']}")

    bpy.ops.object.select_all(action="DESELECT")
    prepared = []
    for obj in meshes:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        apply_modifiers(obj)
        ensure_uv(obj)
        obj.data.materials.clear()
        obj.data.materials.append(pdx_mat)
        for poly in obj.data.polygons:
            poly.material_index = 0
        prepared.append(obj)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in prepared:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = prepared[0]
    bpy.ops.object.join()
    joined = bpy.context.object
    joined.name = data["mesh_name"]
    joined.data.name = data["mesh_name"]
    joined.data["meshindex"] = 0
    joined.data.materials.clear()
    joined.data.materials.append(pdx_mat)
    tri = joined.modifiers.new("DL10_Triangulate_For_PDX", "TRIANGULATE")
    tri.keep_custom_normals = True
    apply_modifiers(joined)
    ensure_uv(joined)

    bpy.ops.object.select_all(action="DESELECT")
    joined.select_set(True)
    for locator in locators:
        locator.select_set(True)
    bpy.context.view_layer.objects.active = joined
    export_meshfile(str(data["target"]), exp_mesh=True, exp_skel=False, exp_locs=True, exp_selected=True)
    print(f"EXPORTED {section_name} -> {data['target']}")


def main():
    bpy.ops.wm.open_mainfile(filepath=str(INPUT_BLEND))
    backup_existing_meshes()
    pdx_mat = create_pdx_material()
    for section_name, data in SECTIONS.items():
        prepare_section(section_name, data, pdx_mat)


if __name__ == "__main__":
    main()
