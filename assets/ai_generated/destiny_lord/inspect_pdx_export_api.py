import inspect
import sys
from pathlib import Path

roots = [
    Path(r"C:\Users\Admin\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default"),
    Path(r"C:\Users\Admin\AppData\Roaming\Blender Foundation\Blender\5.1\extensions"),
]

for root in roots:
    print("ROOT", root, root.exists())
    if root.exists():
        for path in sorted(root.rglob("blender_import_export.py")):
            print("CANDIDATE", path)
            sys.path.append(str(path.parents[2]))

from io_pdx_mesh.pdx_blender import blender_import_export as bie
from io_pdx_mesh import library

print("PDX_SHADER_CONST", library.PDX_SHADER)
print("PDX_MESHINDEX_CONST", library.PDX_MESHINDEX)


for name in dir(bie):
    if "export" in name.lower() and "mesh" in name.lower():
        obj = getattr(bie, name)
        if callable(obj):
            print("EXPORT_API", name, inspect.signature(obj))
            source = inspect.getsource(obj).splitlines()
            for line in source[:80]:
                print("EXPORT_SRC", line)
