import sys
from pathlib import Path

import bpy


GAME_MODEL_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\mod\gfx\models\ships\destiny_lord")
PDX_PLUGIN_ROOT = Path(r"C:\Users\Admin\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default")
sys.path.append(str(PDX_PLUGIN_ROOT))

from io_pdx_mesh.pdx_blender.blender_import_export import import_meshfile  # noqa: E402


FILES = [
    GAME_MODEL_DIR / "destiny_lord_bow.mesh",
    GAME_MODEL_DIR / "destiny_lord_mid.mesh",
    GAME_MODEL_DIR / "destiny_lord_stern.mesh",
]


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def main():
    for path in FILES:
        clear_scene()
        import_meshfile(str(path))
        meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        empties = [obj for obj in bpy.context.scene.objects if obj.type == "EMPTY"]
        verts = sum(len(obj.data.vertices) for obj in meshes)
        faces = sum(len(obj.data.polygons) for obj in meshes)
        locators = sorted(obj.name for obj in empties)
        dims = []
        for obj in meshes:
            dims.append(tuple(round(value, 3) for value in obj.dimensions))
        print(f"VALIDATE {path.name} meshes={len(meshes)} verts={verts} faces={faces} locators={len(empties)} dims={dims}")
        print(f"LOCATORS {path.name} {','.join(locators)}")


if __name__ == "__main__":
    main()

