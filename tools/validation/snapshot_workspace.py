#!/usr/bin/env python3
"""保存相对 HEAD 的工作区快照；不修改 Git 索引、分支或项目文件。"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import zipfile


def git(root, *args):
    """只调用只读 Git 命令，保留含空格和中文的路径。"""
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True
    ).stdout


def snapshot(root, destination):
    root = Path(root).resolve()
    destination = Path(destination).resolve()
    base = git(root, "rev-parse", "HEAD").decode().strip()
    changed = git(root, "diff", "--no-renames", "--name-only", "-z", "HEAD")
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    names = sorted({p.decode("utf-8") for p in (changed + untracked).split(b"\0") if p})
    if destination.is_relative_to(root) and destination.relative_to(root).as_posix() in names:
        raise ValueError("快照输出不能覆盖已有项目文件")
    patch = git(root, "diff", "--binary", "--no-ext-diff", "HEAD")
    manifest = {
        "format": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "base_commit": base,
        "branch": git(root, "branch", "--show-current").decode().strip(),
        "files": [],
        "deleted_paths": [],
        "limitations": "恢复需要 base_commit；不含忽略的数据库、缓存及素材，不保存原索引的分期状态。",
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    # x 模式保证不会覆盖已有快照。
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            path = root / name
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError(f"不支持仓库外链接：{name}")
            if not path.exists():
                manifest["deleted_paths"].append(name)
                continue
            data = path.read_bytes()
            archive.writestr("files/" + name, data)
            manifest["files"].append({
                "path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()
            })
        archive.writestr("tracked.patch", patch)
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    # 写入后立即校验压缩包完整性和文件哈希。
    with zipfile.ZipFile(destination) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"快照 CRC 校验失败：{bad}")
        for entry in manifest["files"]:
            digest = hashlib.sha256(archive.read("files/" + entry["path"])).hexdigest()
            if digest != entry["sha256"]:
                raise ValueError(f"快照哈希校验失败：{entry['path']}")
    return manifest


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = snapshot(args.root, args.output)
    print(json.dumps({"snapshot": str(args.output.resolve()), "base_commit": manifest["base_commit"],
                      "saved_files": len(manifest["files"]),
                      "deleted_paths": len(manifest["deleted_paths"]), "verified": True},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
