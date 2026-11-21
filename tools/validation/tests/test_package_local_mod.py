"""隔离仓库验证候选 ZIP 的素材来源，避免把工作区脚本或链接目标带入游戏包。"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "build"))
import package_local_mod as package


class LocalCandidateTest(unittest.TestCase):
    def setUp(self):
        scratch = package.ROOT / "temp"
        scratch.mkdir(exist_ok=True)
        self.repo = Path(self.enterContext(tempfile.TemporaryDirectory(dir=scratch))).resolve()
        self.enterContext(patch.object(package, "ROOT", self.repo))
        self.output = self.repo / "temp/candidates"
        self.gfx = self.repo / "mod/gfx"
        self.gfx.mkdir(parents=True)
        (self.repo / ".gitignore").write_text("temp/\n", encoding="utf-8")
        (self.repo / "mod/descriptor.mod").write_text(
            'name="示例"\nversion="0.1"\nsupported_version="4.4.*"\n', encoding="utf-8")
        guide = self.repo / package.INSTALL_GUIDE
        guide.parent.mkdir(parents=True)
        guide.write_text("安装说明", encoding="utf-8")
        self.art = self.gfx / "sample.dds"
        self.art.write_bytes(b"committed-art")
        self.definition = self.gfx / "sample.gfx"
        self.definition.write_bytes(b"committed-definition")
        for args in (["init", "-q"], ["add", "."], ["-c", "user.name=Test", "-c", "user.email=test@invalid",
                                                     "-c", "commit.gpgsign=false", "commit", "-qm", "fixture"]):
            subprocess.run(["git", *args], cwd=self.repo, check=True)

    def test_uses_selected_assets_with_committed_definitions(self):
        self.art.write_bytes(b"local-art")
        self.definition.write_bytes(b"uncommitted-definition")
        (self.gfx / "new.PNG").write_bytes(b"new-art")
        (self.gfx / "untracked.asset").write_bytes(b"untracked-definition")
        (self.repo / "mod/outside.png").write_bytes(b"out-of-scope")
        snapshot, count = package.build(self.output)
        local, new_count = package.build(self.output, local_art=True)
        self.assertNotEqual(snapshot, local)
        self.assertEqual(new_count, count + 1)
        prefix = package.MOD_PATH + "/"
        with ZipFile(snapshot) as old, ZipFile(local) as current:
            self.assertEqual(old.read(prefix + "gfx/sample.dds"), b"committed-art")
            self.assertEqual(current.read(prefix + "gfx/sample.dds"), b"local-art")
            self.assertEqual(current.read(prefix + "gfx/sample.gfx"), b"committed-definition")
            self.assertEqual(current.read(prefix + "gfx/new.PNG"), b"new-art")
            self.assertNotIn(prefix + "gfx/new.PNG", old.namelist())
            self.assertNotIn(prefix + "gfx/untracked.asset", current.namelist())
            self.assertNotIn(prefix + "outside.png", current.namelist())
            self.assertIn("本机美术候选包", current.read("安装与存档说明.md").decode("utf-8"))
            self.assertIsNone(current.testzip())

    def test_rejects_linked_directory_and_hardlinked_file(self):
        outside = self.repo / "outside"
        outside.mkdir()
        (outside / "private.png").write_bytes(b"private")
        linked = self.gfx / "linked"
        if os.name == "nt":
            subprocess.run(["cmd", "/d", "/c", "mklink", "/J", r"mod\gfx\linked", "outside"],
                           cwd=self.repo, stdout=subprocess.DEVNULL, check=True)
        else:
            linked.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "链接"):
            package.build(self.output, local_art=True)
        if os.name == "nt":
            linked.rmdir()
        else:
            linked.unlink()
        os.link(outside / "private.png", self.gfx / "linked.png")
        with self.assertRaisesRegex(ValueError, "链接"):
            package.build(self.output, local_art=True)
        self.assertFalse(self.output.exists())

    def test_rejects_missing_tracked_art_and_visible_output(self):
        with self.assertRaisesRegex(ValueError, "忽略目录"):
            package.build(self.repo / "share", local_art=True)
        good, _ = package.build(self.output, local_art=True)
        original = good.read_bytes()
        self.art.unlink()
        with self.assertRaisesRegex(ValueError, "缺少本地美术"):
            package.build(self.output, local_art=True)
        self.assertEqual(good.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
