#!/usr/bin/env python3
"""把当前 Git 提交的 mod/ 打成可直接放入本地播放集的候选 ZIP。"""

import argparse
from pathlib import Path
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


def git(*args):
    # 从同一份 Git 快照读取所有平台上的原始文件，不受工作区自动换行影响。
    return subprocess.check_output(["git", "-c", "core.autocrlf=false", *args], cwd=ROOT)


def build(output_dir):
    revision = git("rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    tree = f"{revision}:mod"
    files = git("ls-tree", "-rz", "--name-only", tree).decode("utf-8").split("\0")
    expected = {f"{MOD_PATH}/{name}" for name in files if name}
    if len({name.casefold() for name in expected}) != len(expected):
        raise ValueError("运行文件包含 Windows 无法区分的同名路径")

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{MOD_ID}-candidate-{revision[:12]}.zip"
    # 临时文件与成品同盘。检查通过才替换同一版本的成品，中断时可直接重试。
    with tempfile.TemporaryDirectory(prefix=".aemusa-", dir=output_dir) as temporary:
        candidate = Path(temporary) / "candidate.zip"
        commit_time = git("show", "-s", "--format=%cI", revision).decode("ascii").strip()
        git("archive", "--format=zip", f"--mtime={commit_time}", f"--prefix={MOD_PATH}/",
            f"--output={candidate}", tree)
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
            guide += f"\n\n本包的游戏文件取自 Git 提交 `{revision}`。\n"
            for name, content in ((f"{MOD_PATH}.mod", registration), ("安装与存档说明.md", guide)):
                info = zipfile.ZipInfo(name, date_time=inner.date_time)
                archive.writestr(info, content.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)

        with zipfile.ZipFile(candidate) as archive:
            broken = archive.testzip()
            if broken is not None:
                raise ValueError(f"ZIP 完整性检查失败：{broken}")
        candidate.replace(destination)

    return destination, len(expected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "temp/local_mod_candidates",
                        help="候选包输出目录，默认为项目 temp/local_mod_candidates")
    args = parser.parse_args()
    try:
        archive_path, file_count = build(args.output_dir)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        parser.exit(1, f"打包失败：{error}\n")
    print(f"{archive_path}\n共 {file_count} 个游戏文件，另附启动器注册文件及安装说明。")
