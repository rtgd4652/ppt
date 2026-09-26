"""执行真实 AWP-02 脚本中的账本子集，回归旧窗口重复选择与强制跳章。

这不是 Stellaris 模拟器；不验证 UI、引擎调度、真实 on_action 或读档。
只识别本工作包使用的条件和写入，未知语法立即失败，避免静默跳过保护。
"""

from copy import deepcopy
from itertools import product
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_mod import Entry, parse, scalar


ROOT = Path(__file__).resolve().parents[3]
PREFIX = "aemusa_ms_country_"


def read_script(relative):
    text = (ROOT / relative).read_text(encoding="utf-8")
    # 通用静态解析器不保留运算符；此测试显式保留唯一使用的比较形式。
    text = re.sub(r"\bvalue\s*>\s*0\b", "value_greater_than = 0", text)
    if re.search(r"[<>!]", re.sub(r"#[^\n]*", "", text)):
        raise AssertionError("账本测试遇到未支持的比较运算符")
    return parse(text)


EVENTS = {
    scalar(entry.value, "id"): entry.value
    for entry in read_script("mod/events/aemusa_main_story_awp_02_events.txt")
    if entry.key == "country_event"
}
TRIGGERS = {entry.key: entry.value for entry in read_script(
    "mod/common/scripted_triggers/aemusa_ms_story_entry_triggers.txt")}
EFFECTS = {entry.key: entry.value for entry in read_script(
    "mod/common/scripted_effects/aemusa_ms_story_lifecycle_effects.txt")}


def child(entries, key):
    return next((entry.value for entry in entries if entry.key == key), [])


def expand(entries, arguments):
    """按脚本传入的显式参数替换，不生成或推断任何正式状态名。"""
    def value(item):
        if isinstance(item, list):
            return expand(item, arguments)
        return re.sub(r"\$(\w+)\$", lambda match: arguments[match[1]], item)
    return [Entry(entry.key, value(entry.value), entry.line) for entry in entries]


class Ledger:
    def __init__(self):
        # 仅提供已初始化玩家国家及有效爱缪莎的测试前置，不调用生命周期探针。
        self.flags = {PREFIX + "route_initialized"}
        self.variables = {
            PREFIX + "route_version_index": 1,
            PREFIX + "chapter_index": 0,
            PREFIX + "act_index": 0,
        }
        self.queue = []
        self.logs = []

    def snapshot(self):
        return deepcopy((self.flags, self.variables, self.queue, self.logs))

    def condition(self, entries):
        return all(self.term(entry) for entry in entries)

    def term(self, entry):
        key, value = entry.key, entry.value
        if key in TRIGGERS:
            arguments = {item.key: item.value for item in value} if isinstance(value, list) else {}
            result = self.condition(expand(TRIGGERS[key], arguments))
            return not result if value == "no" else result
        if key == "AND":
            return self.condition(value)
        if key == "OR":
            return any(self.term(item) for item in value)
        if key in {"NOT", "NOR"}:
            if key == "NOT" and len(value) != 1:
                raise AssertionError("NOT 必须只包含一个条件")
            return not any(self.term(item) for item in value)
        if key == "has_country_flag":
            return value in self.flags
        if key == "is_variable_set":
            return value in self.variables
        if key == "check_variable":
            current = self.variables.get(scalar(value, "which"), 0)
            greater = scalar(value, "value_greater_than")
            return current > float(greater) if greater is not None else current == float(scalar(value, "value"))
        if key == "is_ai":
            return value == "no"
        if key == "exists" and value == "event_target:aemusa_leader":
            return True
        raise AssertionError(f"未支持的条件：{key}")

    def execute(self, entries):
        branch_taken = False
        for entry in entries:
            key, value = entry.key, entry.value
            if key == "if":
                branch_taken = self.condition(child(value, "limit"))
                if branch_taken:
                    self.execute([item for item in value if item.key != "limit"])
            elif key in {"else_if", "else"}:
                if not branch_taken and (key == "else" or self.condition(child(value, "limit"))):
                    self.execute([item for item in value if item.key != "limit"])
                    branch_taken = True
            elif key in EFFECTS:
                arguments = {item.key: item.value for item in value} if isinstance(value, list) else {}
                self.execute(expand(EFFECTS[key], arguments))
            elif key == "set_country_flag":
                self.flags.add(value)
            elif key == "remove_country_flag":
                self.flags.discard(value)
            elif key == "set_variable":
                self.variables[scalar(value, "which")] = float(scalar(value, "value"))
            elif key == "country_event":
                self.queue.append((scalar(value, "id"), int(scalar(value, "days") or 0)))
            elif key == "log":
                self.logs.append(value)
            else:
                raise AssertionError(f"未支持的效果：{key}")

    def open(self, event, forced=False):
        body = EVENTS[event]
        if forced or self.condition(child(body, "trigger")):
            self.execute(child(body, "immediate"))
            return True
        return False

    def choose(self, event, suffix):
        name = event + "." + suffix
        option = next(entry.value for entry in EVENTS[event]
                      if entry.key == "option" and scalar(entry.value, "name") == name)
        self.execute([entry for entry in option if entry.key != "name"])

    def step(self, event, suffix):
        if not self.open(event):
            raise AssertionError(f"正常流程被阻断：{event}")
        self.choose(event, suffix)


class Awp02StateTests(unittest.TestCase):
    def chapter_three(self):
        ledger = Ledger()
        ledger.variables[PREFIX + "chapter_index"] = 3
        ledger.flags.add(PREFIX + "chapter_02_completed")
        ledger.step("aemusa_ms.500", "continue")
        ledger.step("aemusa_ms.510", "continue")
        ledger.open("aemusa_ms.520")
        ledger.queue.clear()
        return ledger

    def test_stale_intervention_choice_cannot_take_another_branch(self):
        ledger = self.chapter_three()
        ledger.choose("aemusa_ms.520", "adopt")
        before = ledger.snapshot()
        ledger.choose("aemusa_ms.520", "reject")
        self.assertEqual(ledger.snapshot(), before)

    def test_stale_execution_cannot_restart_finished_wait(self):
        ledger = self.chapter_three()
        ledger.choose("aemusa_ms.520", "adopt")
        ledger.step("aemusa_ms.530", "execute")
        self.assertEqual(ledger.queue.count(("aemusa_ms.540", 30)), 1)
        ledger.open("aemusa_ms.540")  # 单独验证回调已执行以后的旧窗口。
        before = ledger.snapshot()
        ledger.choose("aemusa_ms.530", "execute")
        self.assertEqual(ledger.snapshot(), before)

    def test_forced_chapter_end_before_prologue_writes_nothing(self):
        ledger = Ledger()
        before = ledger.snapshot()
        ledger.open("aemusa_ms.590", forced=True)
        ledger.choose("aemusa_ms.590", "finish")
        self.assertEqual(ledger.snapshot(), before)

    def test_force_each_cluster_without_its_predecessor_writes_nothing(self):
        for event in EVENTS:
            number = int(event.rsplit(".", 1)[1])
            if number <= 200 or number in {300, 400, 500, 535}:
                continue
            with self.subTest(event=event):
                ledger = Ledger()
                # 保持章节本身合法，只移除同章事件簇前置，防止测试仅靠章节不符通过。
                chapter = 0 if number < 300 else number // 100 - 2
                ledger.variables[PREFIX + "chapter_index"] = chapter
                if chapter:
                    ledger.flags.add(PREFIX + f"chapter_{chapter - 1:02d}_completed")
                ledger.flags.add(PREFIX + "galactic_participation_recorded")
                ledger.variables[PREFIX + "civilization_responsibility_radius_index"] = 1
                before = ledger.snapshot()
                ledger.open(event, forced=True)
                for option in [entry.value for entry in EVENTS[event] if entry.key == "option"]:
                    ledger.choose(event, scalar(option, "name").rsplit(".", 1)[1])
                self.assertEqual(ledger.snapshot(), before)

    def test_conflict_after_window_opens_blocks_all_choice_effects(self):
        ledger = self.chapter_three()
        ledger.flags.add(PREFIX + "consistency_conflict_active")
        before = ledger.snapshot()
        ledger.choose("aemusa_ms.520", "adopt")
        self.assertEqual(ledger.snapshot(), before)

    def test_all_choice_paths_and_repeated_options(self):
        # 192 组正常账本路径；每次选择后重放所有旧选项，结果和队列必须不变。
        for choices in product(range(2), range(2), range(2), range(2), range(3), range(2), range(2)):
            with self.subTest(choices=choices):
                ledger = Ledger()
                policy, tempo, radius, responsibility, intervention, cost, attribution = choices
                selections = {
                    "aemusa_ms.230": ("confidential", "disclosure")[policy],
                    "aemusa_ms.310": ("cautious", "limited")[tempo],
                    "aemusa_ms.320": ("internal", "expanded")[radius],
                    "aemusa_ms.420": ("optimum", "external")[responsibility],
                    "aemusa_ms.520": ("adopt", "narrow", "reject")[intervention],
                    "aemusa_ms.540": ("disclose", "minimize")[cost],
                    "aemusa_ms.550": ("correct", "oracle")[attribution],
                }
                ledger.queue.append(("aemusa_ms.200", 0))
                for _ in range(30):
                    event, days = ledger.queue.pop(0)
                    if days:
                        self.assertEqual((event, days), ("aemusa_ms.540", 30))
                        before = ledger.snapshot()
                        for _ in range(3):
                            ledger.open("aemusa_ms.100")
                            self.assertEqual(ledger.queue.pop(), ("aemusa_ms.535", 0))
                        self.assertEqual(ledger.snapshot(), before)
                    self.assertTrue(ledger.open(event), event)
                    options = [scalar(entry.value, "name").rsplit(".", 1)[1]
                               for entry in EVENTS[event] if entry.key == "option"]
                    ledger.choose(event, selections.get(event, options[0]))
                    before = ledger.snapshot()
                    for option in options:
                        ledger.choose(event, option)
                        self.assertEqual(ledger.snapshot(), before, (event, option))
                    if not ledger.queue:
                        chapter = ledger.variables[PREFIX + "chapter_index"]
                        if chapter == 4:
                            break
                        if chapter == 1:
                            ledger.open("aemusa_ms.100")
                            self.assertEqual(ledger.queue.pop(), ("aemusa_ms.101", 0))
                            # 真实调查/殖民由游戏另测；账本测试只提供外部事实前置。
                            ledger.flags.add(PREFIX + "galactic_participation_recorded")
                        ledger.open("aemusa_ms.100")
                else:
                    self.fail("账本流程未在预期事件数内结束")
                ledger.execute(EFFECTS["aemusa_ms_log_awp_02_audit"])
                self.assertEqual(sum("|PASS|" in line for line in ledger.logs), 5)
                self.assertFalse(any("|FAIL|" in line for line in ledger.logs))


if __name__ == "__main__":
    unittest.main()
