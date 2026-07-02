from pathlib import Path

import bpy


ASSET_DIR = Path(r"C:\Users\Admin\Desktop\ppt\simple_leader_edict\assets\destiny_lord")
INPUT = ASSET_DIR / "destiny_lord_stage9_refined_A.blend"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(INPUT))
    for obj in sorted((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: max(o.dimensions), reverse=True):
        dims = tuple(round(v, 3) for v in obj.dimensions)
        loc = tuple(round(v, 3) for v in obj.location)
        if max(obj.dimensions) >= 12 or "Rim" in obj.name or "Rail" in obj.name or "Blade" in obj.name:
            print(f"LONG_OBJECT name={obj.name} loc={loc} dims={dims}")


if __name__ == "__main__":
    main()
