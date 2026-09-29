"""检查天灾入口和实际写入；不模拟游戏引擎、天灾生成或真实存读档。"""

import unittest

from test_awp02_state import EVENTS, Ledger, PREFIX, child, read_script, scalar


CRISIS_EVENTS = {}
for path in (
    "mod/events/aemusa_main_story_awp_04_entry_events.txt",
    "mod/events/aemusa_main_story_awp_04_story_events.txt",
    "mod/events/aemusa_main_story_chapter_07_events.txt",
):
    CRISIS_EVENTS.update({scalar(entry.value, "id"): entry.value
                         for entry in read_script(path) if entry.key == "country_event"})
ROUTES = (
    ("prethoryn", "prethoryn_invasion", 1),
    ("unbidden", "extradimensional_invasion", 2),
    ("contingency", "ai_invasion", 3),
    ("cetana", "synth_queen", 4),
)


class CrisisLedger(Ledger):
    def __init__(self):
        super().__init__(events={**EVENTS, **CRISIS_EVENTS})
        self.global_flags = set()
        self.resources = {"energy": 1000, "minerals": 1000}
        self.timers = {}

    def snapshot(self):
        return super().snapshot(), dict(self.resources), dict(self.timers)

    def term(self, entry):
        if entry.key == "has_global_flag":
            return entry.value in self.global_flags
        if entry.key == "custom_tooltip":
            return self.condition([item for item in entry.value if item.key != "fail_text"])
        if entry.key == "resource_stockpile_compare":
            return self.resources[scalar(entry.value, "resource")] >= float(scalar(entry.value, "value_greater_equal"))
        return super().term(entry)

    def execute_extra(self, entry):
        if entry.key == "add_resource":
            for resource in entry.value:
                self.resources[resource.key] += float(resource.value)
        elif entry.key == "set_timed_country_flag":
            name = scalar(entry.value, "flag")
            self.flags.add(name)
            self.timers[name] = int(scalar(entry.value, "days"))
        else:
            super().execute_extra(entry)

    def elapse(self, days):
        # 只核对源代码的计时条件；实际引擎延迟与存档另作一次运行检查。
        for name in tuple(self.timers):
            self.timers[name] -= days
            if self.timers[name] <= 0:
                del self.timers[name]
                self.flags.discard(name)

    def option(self, event, suffix):
        return next(entry.value for entry in self.events[event]
                    if entry.key == "option" and scalar(entry.value, "name") == event + "." + suffix)

    def choose(self, event, suffix):
        # 刻意绕过 UI allow，确认即使旧选项被执行也有实际写入保护。
        self.execute(child(self.option(event, suffix), "hidden_effect"))

    def available(self, suffix):
        return self.condition(child(self.option("aemusa_ms.1010", suffix), "allow"))


def after_second_act():
    ledger = CrisisLedger()
    ledger.variables[PREFIX + "chapter_index"] = 7
    ledger.variables[PREFIX + "act_index"] = 2
    ledger.flags.update(PREFIX + suffix for suffix in (
        "chapter_06_completed", "settlement_chapter_06_done",
        "act_02_completed", "fe_war_recovery_period_active",
    ))
    return ledger


class Awp04EntryTests(unittest.TestCase):
    def test_recovery_can_wait_then_route_returns_to_preparation(self):
        ledger = after_second_act()
        ledger.open("aemusa_ms.100")
        self.assertEqual(ledger.queue.pop(), ("aemusa_ms.1000", 0))
        before = ledger.snapshot()
        ledger.step("aemusa_ms.1000", "rest")
        self.assertEqual(ledger.snapshot(), before)
        ledger.step("aemusa_ms.1000", "prepare")
        self.assertEqual(ledger.queue.pop(), ("aemusa_ms.1010", 0))
        self.assertTrue(ledger.open("aemusa_ms.1010"))
        before = ledger.snapshot()
        ledger.choose("aemusa_ms.1010", "wait")
        self.assertEqual(ledger.snapshot(), before)
        self.assertFalse(any(ledger.available(route) for route, _, _ in ROUTES))
        ledger.open("aemusa_ms.100")
        self.assertEqual(ledger.queue.pop(), ("aemusa_ms.1010", 0))

    def test_available_route_locks_once_and_resumes_without_awarding_completion(self):
        # 四项共用写接口，仅核对参数映射；不穷举剧情或引擎排列。
        for route, flag, index in ROUTES:
            with self.subTest(route=route):
                ledger = after_second_act()
                ledger.flags.add(PREFIX + "fe_war_recovery_reviewed")
                ledger.global_flags.add(flag + "_happened")
                self.assertTrue(ledger.available(route))
                ledger.step("aemusa_ms.1010", route)
                self.assertEqual(ledger.queue.pop(), ("aemusa_ms.1015", 0))
                self.assertEqual(ledger.variables[PREFIX + "vanilla_crisis_route_index"], index)
                self.assertIn(PREFIX + "history_vanilla_crisis_locked", ledger.flags)
                self.assertIn(PREFIX + "cluster_aed_c_00_settled", ledger.flags)
                self.assertNotIn(PREFIX + "history_vanilla_crisis_completed", ledger.flags)
                self.assertNotIn(PREFIX + "chapter_07_completed", ledger.flags)
                self.assertEqual(ledger.variables[PREFIX + "chapter_index"], 7)
                before = ledger.snapshot()
                ledger.global_flags.update(other + "_happened" for _, other, _ in ROUTES)
                ledger.choose("aemusa_ms.1010", "unbidden" if index != 2 else "prethoryn")
                self.assertEqual(ledger.snapshot(), before)
                # 从已有持久账本恢复入口；这不是 Stellaris 存读档证明。
                restored = CrisisLedger()
                restored.flags = set(ledger.flags)
                restored.variables = dict(ledger.variables)
                restored.open("aemusa_ms.100")
                self.assertEqual(restored.queue.pop(), ("aemusa_ms.1100", 0))

    def test_forced_entry_without_second_act_cannot_lock_a_route(self):
        ledger = CrisisLedger()
        ledger.global_flags.add("prethoryn_invasion_happened")
        before = ledger.snapshot()
        ledger.open("aemusa_ms.1000", forced=True)
        ledger.choose("aemusa_ms.1000", "prepare")
        ledger.open("aemusa_ms.1010", forced=True)
        ledger.choose("aemusa_ms.1010", "prethoryn")
        self.assertEqual(ledger.snapshot(), before)

    def test_already_ended_crisis_keeps_postwar_route_available(self):
        ledger = after_second_act()
        ledger.flags.add(PREFIX + "fe_war_recovery_reviewed")
        ledger.global_flags.add("prethoryn_invasion_happened")
        self.assertTrue(ledger.open("aemusa_ms.1010"))
        ledger.global_flags.add("prethoryn_invasion_defeated")
        self.assertTrue(ledger.available("prethoryn"))
        ledger.choose("aemusa_ms.1010", "prethoryn")
        self.assertEqual(ledger.variables[PREFIX + "vanilla_crisis_route_index"], 1)
        self.assertNotIn(PREFIX + "history_vanilla_crisis_completed", ledger.flags)
        self.assertNotIn(PREFIX + "history_vanilla_crisis_settled", ledger.flags)


if __name__ == "__main__":
    unittest.main()
