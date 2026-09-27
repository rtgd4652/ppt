"""使用临时仓库验证检查器能拦截真实缺陷，不写入正式 Mod。"""

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_mod import check, parse
from snapshot_workspace import snapshot


class ModChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.write("mod/descriptor.mod", 'name = "fixture"')
        self.write("mod/events/story.txt", 'namespace = aemusa_ms\ncountry_event = { id = aemusa_ms.1 title = aemusa_ms.1.title desc = aemusa_ms.1.desc option = { name = aemusa_ms.1.ok } }')
        self.localize()
        path = self.root / "docs/design/aemusa_main_story_state_registry_expanded_v1.0.csv"
        path.parent.mkdir(parents=True)
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["registry_id", "key", "scope", "data_type", "status"])
            writer.writerow(["ASR-1", "aemusa_ms_country_ready", "country", "flag", "formal_awp_02"])
            writer.writerow(["ASR-2", "aemusa_ms_country_pending_index", "country", "variable", "reserved_pending_enum_review"])

    def write(self, name, data, encoding="utf-8"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding=encoding)

    def localize(self, encoding="utf-8-sig"):
        self.write("mod/localisation/simp_chinese/test.yml", 'l_simp_chinese:\n aemusa_ms.1.title:0 "标题"\n aemusa_ms.1.desc:0 "正文 { } # 字符串"\n aemusa_ms.1.ok:0 "继续"\n', encoding)

    def codes(self, game_dir=None):
        return {item["code"] for item in check(self.root, game_dir)["errors"]}

    def test_valid_project_and_read_only(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(check(self.root)["status"], "pass")
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_comments_strings_comparisons_and_color_blocks(self):
        parse('color = hsv { 0.2 0.5 1 } nested = { { 1 2 } } # }\nvalue = "escaped \\" { #" check = { value >= 1 }')
        for value in ('x = {', 'x = }', 'x = "unterminated', 'x = { y = }'):
            with self.assertRaises(ValueError):
                parse(value)

    def test_duplicate_events(self):
        self.write("mod/events/duplicate.txt", 'country_event = { id = aemusa_ms.1 }')
        self.assertIn("duplicate_event", self.codes())

    def test_missing_event_in_on_action(self):
        self.write("mod/common/on_actions/test.txt", 'on_game_start_country = { events = { aemusa_ms.99 } }')
        self.assertIn("missing_event", self.codes())

    def test_global_event_is_resolved_and_duplicate_checked(self):
        # 读档回调引用无作用域 event，仍须检查 ID 引用与跨类型重名。
        self.write("mod/events/global.txt", 'event = { id = aemusa_ms.2 hide_window = yes is_triggered_only = yes }')
        self.write("mod/common/on_actions/test.txt", 'on_single_player_save_game_load = { events = { aemusa_ms.2 } }')
        self.assertEqual(self.codes(), set())
        self.write("mod/events/duplicate_global.txt", 'country_event = { id = aemusa_ms.2 }')
        self.assertIn("duplicate_event", self.codes())

    def test_missing_localization(self):
        self.write("mod/events/story.txt", 'namespace = aemusa_ms country_event = { id = aemusa_ms.1 title = aemusa_ms.missing }')
        self.assertIn("missing_localization", self.codes())

    def test_duplicate_localization(self):
        self.write("mod/localisation/simp_chinese/duplicate.yml", 'l_simp_chinese:\n aemusa_ms.1.title:0 "重复"', "utf-8-sig")
        self.assertIn("duplicate_localization", self.codes())

    def test_bom_rules(self):
        self.localize("utf-8")
        self.write("mod/common/test.txt", 'x = yes', "utf-8-sig")
        self.assertTrue({"localization_bom", "script_bom"}.issubset(self.codes()))

    def test_missing_assets_and_sprites(self):
        self.write("mod/interface/test.gfx", 'spriteTypes = { spriteType = { name = GFX_aemusa_test texturefile = "gfx/aemusa_missing.dds" } }')
        self.assertIn("missing_asset", self.codes())
        self.write("mod/events/story.txt", 'namespace = aemusa_ms country_event = { id = aemusa_ms.1 picture = GFX_aemusa_unknown }')
        self.assertIn("missing_sprite", self.codes())

    def test_external_assets_are_explicitly_unverified(self):
        self.write("mod/interface/test.gfx", 'spriteTypes = { spriteType = { name = GFX_external texturefile = "gfx/vanilla.dds" } }')
        self.assertEqual(check(self.root)["warnings"][0]["code"], "external_assets_unverified")
        self.assertIn("missing_external_asset", self.codes(self.root / "vanilla"))
        self.write("vanilla/gfx/vanilla.dds", "fixture")
        self.assertEqual(self.codes(self.root / "vanilla"), set())

    def test_state_and_interface_contracts(self):
        self.write("mod/events/story.txt", 'namespace = aemusa_ms country_event = { id = aemusa_ms.1 immediate = { aemusa_ms_unknown_effect = yes set_country_flag = aemusa_ms_country_unknown set_variable = { which = aemusa_ms_country_pending_index value = 1 } check_variable = { which = aemusa_ms_country_ready value = 1 } } }')
        self.assertTrue({"missing_interface", "unregistered_state", "reserved_state_write", "state_type"}.issubset(self.codes()))

    def test_reserved_state_can_be_read(self):
        self.write("mod/common/scripted_triggers/test.txt", 'aemusa_ms_test = { check_variable = { which = aemusa_ms_country_pending_index value = 0 } }')
        self.assertEqual(self.codes(), set())

    def test_zero_duration_edict_crash_is_rejected(self):
        # 同时拦截直接数值与本文件常量，错误位置必须指向法令的 length 行。
        for duration in ("0", "0.0", "@instant", "@alias"):
            with self.subTest(duration=duration):
                self.write("mod/common/edicts/test.txt", f"@instant = 0\n@alias = @instant\nfixture = {{\n length = {duration}\n}}")
                errors = check(self.root)["errors"]
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[0]["code"], "zero_duration_edict")
                self.assertEqual(errors[0]["line"], 4)

    def test_edict_duration_guard_stays_within_its_scope(self):
        # 常规时长、永久法令和非时长字段不受影响；不把未解析常量当成零。
        for duration in ("1", "-1", "@perpetual", "@external", "@cycle"):
            with self.subTest(duration=duration):
                self.write("mod/common/edicts/test.txt", f"@perpetual = -1\n@cycle = @cycle\nfixture = {{ length = {duration} modifier = {{ length = 0 }} }}")
                self.write("mod/common/scripted_effects/test.txt", "fixture_effect = { length = 0 }")
                self.assertEqual(self.codes(), set())


class WorkspaceSnapshot(unittest.TestCase):
    def test_binary_modified_new_and_deleted_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "repo"
            root.mkdir()
            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True).stdout
            git("init")
            (root / "binary.bin").write_bytes(b"\x00old")
            (root / "deleted.txt").write_text("old", encoding="utf-8")
            git("add", ".")
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture")
            (root / "binary.bin").write_bytes(b"\x00new\xff")
            (root / "deleted.txt").unlink()
            (root / "中文 file.txt").write_text("新文件", encoding="utf-8")
            before = git("status", "--porcelain", "-z")
            target = Path(folder) / "snapshot.zip"
            result = snapshot(root, target)
            self.assertEqual(before, git("status", "--porcelain", "-z"))
            self.assertEqual(result["deleted_paths"], ["deleted.txt"])
            with zipfile.ZipFile(target) as archive:
                manifest = json.loads(archive.read("manifest.json"))
                for entry in manifest["files"]:
                    self.assertEqual(hashlib.sha256(archive.read("files/" + entry["path"])).hexdigest(), entry["sha256"])
                self.assertIn(b"GIT binary patch", archive.read("tracked.patch"))
            with self.assertRaises(FileExistsError):
                snapshot(root, target)


if __name__ == "__main__":
    unittest.main()
