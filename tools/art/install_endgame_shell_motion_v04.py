"""将已回读核对的银壳模型装入开发版，沿用旧存档解析的三个实体名。"""

import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
AUTHOR = ROOT / "art/models/aemusa_endgame_runtime_v04"
OLD = ROOT / "art/models/aemusa_endgame_runtime_v03/export"
DEST = ROOT / "mod/gfx/models/aemusa_endgame_v03"
REGISTRY = ROOT / "docs/art/ASSET_REGISTRY.csv"
TEXTURES = [f"aef04_shell_{s}.dds" for s in ("diffuse","normal","properties")]
MESHES = [f"aef03_{s}.mesh" for s in ("bow","mid","stern")]
CLIP = "aef04_shell_orbit.anim"
GFX, ENTITIES = "_aef03_meshes.gfx","_aef03_entities.asset"


def relative(path):
    return path.relative_to(ROOT).as_posix()


def resource_digest(name, content):
    # 同一份 GFX 文本在 Windows / Unix 检出时可使用不同换行。
    if name in (GFX, ENTITIES):
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def registry_payload(changed_names):
    original = REGISTRY.read_bytes()
    text = original.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    fields = reader.fieldnames
    assert fields and len({r["asset_id"] for r in rows})==len(rows)
    records = {r["asset_id"]:r for r in rows}
    source = relative(AUTHOR/"endgame_shell_motion_v04.blend")
    note = "2026-11-07。依据第二稿重做四瓣银壳，前后分组绕轴，固定星空与武器挂点。实际 PDX 已离线核对。"
    lod_note = " 三档原生 LOD 已离线核对，游戏内缩放切换待观察。"
    for part in ("BOW","MID","STERN","ENTITY-PACK"):
        key = "ASSET-AEF03-"+("MESH-"+part if part!="ENTITY-PACK" else part)
        row = records[key]
        filename = f"aef03_{part.lower()}.mesh" if part!="ENTITY-PACK" else ENTITIES
        origin = source if part!="ENTITY-PACK" else relative(AUTHOR/"export"/ENTITIES)
        same_source = row["source_path"]==origin
        row["source_path"] = origin
        row["origin_method"] = "项目原创第二稿控制截面与 v03 舰体，刚性蒙皮及 PDX 导出"
        if not same_source:
            row["authorization_review"] = "user_selected_second_concept_and_requested_motion"
        if filename in changed_names or not same_source:
            if same_source and filename in MESHES and row["game_spec_status"] in (
                "normal_system_view_sampled", "near_observed_lod_switch_pending"
            ):
                # 只有哈希核对过的近景可以继承此前的实机记录。新加的两层仍待观察。
                row["game_spec_status"] = "near_observed_lod_switch_pending"
            else:
                row.update(notes=note, game_spec_status="static_checked_runtime_pending")
            if filename in MESHES and lod_note not in row["notes"]:
                row["notes"] += lod_note
    base = records["ASSET-AEF03-MESH-MID"]
    for filename in [*TEXTURES,CLIP]:
        is_clip = filename==CLIP
        role = filename.removeprefix("aef04_shell_").removesuffix(".dds")
        key = "ASSET-AEF04-ORBIT" if is_clip else "ASSET-AEF04-TEX-SHELL-"+role.upper()
        row = dict(records.get(key,base))
        origin = AUTHOR/"shell_albedo.png" if role=="diffuse" else ROOT/"tools/art/endgame_shell_profiles.py"
        if is_clip:
            method = "项目原创前后两组刚性骨骼，24 fps 采样导出 PDX 循环动作"
        elif role=="diffuse":
            method = "项目原创第二稿银壳表面采色，按各壳截面展开并编码 BC3 mip"
        else:
            method = "按 PdxMeshShip 通道定义生成常量数据贴图并编码 BC3 mip"
        row.update(asset_id=key, title="终局旗舰银壳错相旋转" if is_clip else "终局旗舰银壳 "+role+" 贴图",
                   asset_type="ship_animation" if is_clip else "model_texture",
                   source_path=source if is_clip else relative(origin), mod_path=relative(DEST/filename),
                   origin_method=method)
        if filename in changed_names or key not in records:
            row.update(notes=note, game_spec_status="static_checked_runtime_pending")
        if key in records:
            records[key].update(row)
        else:
            rows.append(row)
    result = io.StringIO(newline="")
    writer = csv.DictWriter(result,fieldnames=fields,lineterminator="\r\n" if b"\r\n" in original else "\n")
    writer.writeheader()
    writer.writerows(rows)
    return result.getvalue().encode("utf-8-sig" if original.startswith(b"\xef\xbb\xbf") else "utf-8")


def install():
    evidence = json.loads((AUTHOR/"verification.json").read_text(encoding="utf-8"))
    assert evidence["T_locators"]==16 and evidence["camera_check"]["minimum_visible_banks"]==2
    assert [entry["level"] for entry in evidence["lod"]]==[0,1,2]
    names = [*TEXTURES,CLIP,*MESHES,GFX,ENTITIES]
    payloads = {}
    for name in names:
        content = (AUTHOR/"export"/name).read_bytes()
        if resource_digest(name, content)!=evidence["resource_sha256"][name]:
            raise ValueError(f"离线核对后文件发生变化，请重新核对：{name}")
        target = DEST/name
        if target.is_file() and target.read_bytes()!=content:
            existing = target.read_bytes()
            baseline = (OLD/name).is_file() and existing==(OLD/name).read_bytes()
            # 使用与工作树相同的检出过滤器，避免把 Git 的 LF 与 Windows 的 CRLF 当成本地编辑。
            tracked = subprocess.run(["git","cat-file","--filters","HEAD:"+relative(target)],cwd=ROOT,capture_output=True)
            if not baseline and (tracked.returncode or existing!=tracked.stdout):
                raise RuntimeError(f"已有不同的开发版文件需要保留：{target}")
        payloads[target] = content
    # 原样重装保留已记录的实机观察，资源有变化时另行核对。
    changed_names = {path.name for path,data in payloads.items() if not path.is_file() or path.read_bytes()!=data}
    payloads[REGISTRY] = registry_payload(changed_names)
    # 先在同盘备齐文件，再依次替换。若中途遇到写锁，按原样恢复前面已经替换的文件。
    (ROOT/"temp").mkdir(exist_ok=True)
    with TemporaryDirectory(dir=ROOT/"temp", prefix="aef04_install_") as scratch:
        stage = Path(scratch)
        changed = []
        requests = []
        for i,(target,data) in enumerate(payloads.items()):
            old = target.read_bytes() if target.exists() else None
            if old == data:
                continue
            new_file = stage/f"{i}.new"
            new_file.write_bytes(data)
            backup = stage/f"{i}.old" if old is not None else None
            if backup is not None:
                backup.write_bytes(old)
            requests.append((target,new_file,backup))
        try:
            for target,new_file,backup in requests:
                os.replace(new_file,target)
                changed.append((target,backup))
        except OSError:
            for target,backup in reversed(changed):
                if backup is None:
                    target.unlink()
                else:
                    os.replace(backup,target)
            raise
    print("AEF04_INSTALLED",len(names),"game resources")


if __name__=="__main__":
    install()
