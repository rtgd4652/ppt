#!/usr/bin/env python3
"""把已提交的 mod/ 打成本地候选 ZIP，可选择采用工作区的游戏美术文件。"""

import argparse
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/validation"))
from check_mod import parse


MOD_ID = "aemusa_artifact_user"
MOD_PATH = f"mod/{MOD_ID}"
INSTALL_GUIDE = "docs/project/local_candidate_installation.md"
ART_EXTENSIONS = (".anim", ".dds", ".mesh", ".png")


def git(*args):
    # 从同一份 Git 快照读取所有平台上的原始文件，不受工作区自动换行影响。
    return subprocess.check_output(["git", "-c", "core.autocrlf=false", *args], cwd=ROOT)


def checked_art_path(path):
    # 同时挡住文件链接、目录联接点和通过祖先目录跳出的文件。
    entry = path.lstat()
    if (path.resolve(strict=True) != path or stat.S_ISLNK(entry.st_mode)
            or (stat.S_ISREG(entry.st_mode) and entry.st_nlink > 1)
            or getattr(entry, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
        raise ValueError(f"本地美术路径含链接或重解析点：{path}")
    return entry


def local_art_files():
    gfx = ROOT / "mod/gfx"
    if not stat.S_ISDIR(checked_art_path(gfx).st_mode):
        raise ValueError(f"本地美术根目录无效：{gfx}")
    directories = [gfx]
    files = {}
    while directories:
        for path in sorted(directories.pop().iterdir()):
            entry = checked_art_path(path)
            if stat.S_ISDIR(entry.st_mode):
                directories.append(path)
            elif path.suffix.lower() in ART_EXTENSIONS:
                if not stat.S_ISREG(entry.st_mode):
                    raise ValueError(f"本地美术须为普通文件：{path}")
                relative = path.relative_to(gfx).as_posix()
                if "\\" in relative or ":" in relative:
                    raise ValueError(f"本地美术路径不能用于 Windows 安装包：{path}")
                files[f"{MOD_PATH}/gfx/{relative}"] = path
    return files


def add_local_art(archive, files, date_time):
    for name, path in sorted(files.items()):
        entry = checked_art_path(path)
        info = zipfile.ZipInfo(name, date_time=date_time)
        info.compress_type = zipfile.ZIP_DEFLATED
        with path.open("rb") as source:
            if not os.path.samestat(entry, os.fstat(source.fileno())):
                raise ValueError(f"读取前本地美术已更换，请重新打包：{path}")
            with archive.open(info, "w") as destination:
                shutil.copyfileobj(source, destination)
            final = checked_art_path(path)
            if (not os.path.samestat(entry, final)
                    or (entry.st_size, entry.st_mtime_ns) != (final.st_size, final.st_mtime_ns)):
                raise ValueError(f"打包中本地美术已变动，请重新打包：{path}")


def build(output_dir, local_art=False):
    revision = git("rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    tree = f"{revision}:mod"
    files = git("ls-tree", "-rz", "--name-only", tree).decode("utf-8").split("\0")
    expected = {f"{MOD_PATH}/{name}" for name in files if name}
    output_dir = output_dir.resolve()
    archive_paths = []
    art = {}
    suffix = ""
    if local_art:
        if not output_dir.is_relative_to(ROOT) or output_dir.is_relative_to(ROOT / "mod"):
            raise ValueError("本地美术候选包须输出到仓库的 Git 忽略目录，例如 temp/local_mod_candidates")
        relative_output = output_dir.relative_to(ROOT)
        ignored = subprocess.run(["git", "check-ignore", "-q", "--", relative_output.as_posix() + "/"],
                                 cwd=ROOT)
        if ignored.returncode != 0:
            raise ValueError("本地美术候选包须输出到仓库的 Git 忽略目录")
        art = local_art_files()
        # 工作区提供二进制资源。提交中的美术缺失时中止，防止误发残缺包。
        tracked_art = {name for name in expected if name.startswith(f"{MOD_PATH}/gfx/")
                       and Path(name).suffix.lower() in ART_EXTENSIONS}
        missing = sorted(tracked_art - art.keys())
        if missing or not art:
            raise ValueError("缺少本地美术：" + (missing[0] if missing else "mod/gfx 下没有游戏美术文件"))
        expected -= tracked_art
        archive_paths = ["--", ".", *(f":(exclude,glob,icase)gfx/**/*{ext}" for ext in ART_EXTENSIONS)]
        suffix = "-local-art"
    all_files = expected | art.keys()
    if len({name.casefold() for name in all_files}) != len(all_files):
        raise ValueError("运行文件包含 Windows 无法区分的同名路径")

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{MOD_ID}-candidate-{revision[:12]}{suffix}.zip"
    # 临时文件与成品同盘。检查通过才替换同一版本的成品，中断时可直接重试。
    with tempfile.TemporaryDirectory(prefix=".aemusa-", dir=output_dir) as temporary:
        candidate = Path(temporary) / "candidate.zip"
        commit_time = git("show", "-s", "--format=%cI", revision).decode("ascii").strip()
        git("archive", "--format=zip", f"--mtime={commit_time}", f"--prefix={MOD_PATH}/",
            f"--output={candidate}", tree, *archive_paths)
        with zipfile.ZipFile(candidate, "a") as archive:
            entries = [item for item in archive.infolist() if not item.is_dir()]
            if {item.filename for item in entries} != expected or len(entries) != len(expected):
                raise ValueError("ZIP 中的运行文件与 Git 中的 mod/ 清单不一致")
            if any(stat.S_ISLNK(item.external_attr >> 16) for item in entries):
                raise ValueError("运行目录含符号链接，普通 Windows 解压无法安装其目标")
            inner = archive.getinfo(f"{MOD_PATH}/descriptor.mod")
            descriptor = archive.read(inner).decode("utf-8-sig")
            fields = {entry.key: entry.value for entry in parse(descriptor)}
            if not all(isinstance(fields.get(key), str) and fields[key].strip()
                       for key in ("name", "version", "supported_version")):
                raise ValueError("descriptor.mod 缺少模组名称、版本或适配版本")
            if {"path", "archive", "remote_file_id"} & fields.keys():
                raise ValueError("包内 descriptor.mod 带有本地路径、压缩包路径或工坊绑定")

            # 启动器从游戏用户资料目录解析外层 path，包内描述符保留提交中的原文。
            registration = descriptor.rstrip() + f'\npath="{MOD_PATH}"\n'
            guide = git("show", f"{revision}:{INSTALL_GUIDE}").decode("utf-8-sig").rstrip()
            if local_art:
                add_local_art(archive, art, inner.date_time)
                guide += (f"\n\n本机美术候选包。脚本、资源定义和本说明取自 Git 提交 `{revision}`。"
                          f"本包的 {len(art)} 个模型、动画与贴图文件取自构建时本机的 mod/gfx。\n")
            else:
                guide += f"\n\n本包的游戏文件取自 Git 提交 `{revision}`。\n"
            for name, content in ((f"{MOD_PATH}.mod", registration), ("安装与存档说明.md", guide)):
                info = zipfile.ZipInfo(name, date_time=inner.date_time)
                archive.writestr(info, content.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)

        with zipfile.ZipFile(candidate) as archive:
            broken = archive.testzip()
            if broken is not None:
                raise ValueError(f"ZIP 完整性检查失败：{broken}")
        candidate.replace(destination)

    return destination, len(all_files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "temp/local_mod_candidates",
                        help="候选包输出目录，默认为项目 temp/local_mod_candidates")
    parser.add_argument("--local-art", action="store_true",
                        help="在已提交的脚本与资源定义上使用 mod/gfx 下本机的模型、动画和贴图")
    args = parser.parse_args()
    try:
        archive_path, file_count = build(args.output_dir, args.local_art)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        parser.exit(1, f"打包失败：{error}\n")
    print(f"{archive_path}\n共 {file_count} 个游戏文件，另附启动器注册文件及安装说明。")
