"""执行真实脚本的主路径与关键保护，不穷举全部章节选择。"""

import unittest

from test_awp04_entry_state import after_second_act, PREFIX


def route(ledger):
    ledger.queue.clear()
    ledger.open("aemusa_ms.1100")
    return ledger.queue.pop()[0]


def prepared(ended=False, refuses=False):
    ledger = after_second_act()
    ledger.flags.add(PREFIX + "fe_war_recovery_reviewed")
    ledger.global_flags.add("prethoryn_invasion_happened")
    if ended:
        ledger.global_flags.add("prethoryn_invasion_defeated")
    if refuses:
        ledger.flags.add(PREFIX + "first_intervention_oracle_narrative_recorded")
    ledger.step("aemusa_ms.1010", "prethoryn")
    assert route(ledger) == "aemusa_ms.1110"
    ledger.step("aemusa_ms.1110", "continue")
    assert route(ledger) == "aemusa_ms.1121"
    ledger.step("aemusa_ms.1121", "care")
    assert route(ledger) == "aemusa_ms.1130"
    ledger.step("aemusa_ms.1130", "continue")
    assert route(ledger) == "aemusa_ms.1140"
    return ledger


def finish_response(ledger):
    ledger.elapse(90)
    ledger.open("aemusa_ms.1151")
    assert route(ledger) == "aemusa_ms.1160"
    ledger.step("aemusa_ms.1160", "continue")


def finish_chapter(ledger):
    assert route(ledger) == "aemusa_ms.1170"
    ledger.step("aemusa_ms.1170", "continue")
    for event, option in ((1200, "continue"), (1210, "open"), (1220, "respect"),
                          (1230, "reference"), (1240, "continue"), (1250, "finish")):
        assert route(ledger) == f"aemusa_ms.{event}"
        ledger.step(f"aemusa_ms.{event}", option)


class Awp04StoryTests(unittest.TestCase):
    def test_normal_response_requires_time_and_matching_crisis_result(self):
        ledger = prepared()
        self.assertEqual(ledger.variables[PREFIX + "crisis_aemusa_consent_index"], 1)
        ledger.step("aemusa_ms.1140", "limited")
        self.assertEqual(route(ledger), "aemusa_ms.1150")
        ledger.step("aemusa_ms.1150", "care")
        self.assertEqual(ledger.resources, {"energy": 500, "minerals": 750})
        self.assertIn(PREFIX + "crisis_intervention_performed", ledger.flags)
        before = ledger.snapshot()
        ledger.choose("aemusa_ms.1150", "study")
        self.assertEqual(ledger.snapshot(), before)
        ledger.open("aemusa_ms.1151", forced=True)
        self.assertNotIn(PREFIX + "crisis_response_completed", ledger.flags)
        self.assertEqual(route(ledger), "aemusa_ms.1155")
        ledger.choose("aemusa_ms.1155", "stop")
        self.assertIn(PREFIX + "crisis_intervention_stopped", ledger.flags)
        self.assertIn(PREFIX + "crisis_response_pending", ledger.flags)
        finish_response(ledger)
        self.assertEqual(route(ledger), "aemusa_ms.1175")
        # 另一个危机结束不能推进所选危机。
        ledger.global_flags.update({"ai_invasion_happened", "ai_invasion_defeated"})
        self.assertEqual(route(ledger), "aemusa_ms.1175")
        ledger.global_flags.add("prethoryn_invasion_defeated")
        finish_chapter(ledger)
        self.assertEqual(ledger.variables[PREFIX + "chapter_index"], 8)
        self.assertEqual(ledger.variables[PREFIX + "act_index"], 3)
        self.assertIn(PREFIX + "history_vanilla_crisis_settled", ledger.flags)
        self.assertNotIn(PREFIX + "fate_sovereign_authority_active", ledger.flags)
        ledger.open("aemusa_ms.100")
        self.assertEqual(ledger.queue.pop(), ("aemusa_ms.1300", 0))

    def test_already_ended_and_aemusa_refusal_use_ordinary_actions(self):
        for ended, refuses, consent in ((True, False, 3), (False, True, 2)):
            with self.subTest(ended=ended, refuses=refuses):
                ledger = prepared(ended, refuses)
                self.assertEqual(ledger.variables[PREFIX + "crisis_aemusa_consent_index"], consent)
                ledger.open("aemusa_ms.1140")
                before = ledger.snapshot()
                ledger.choose("aemusa_ms.1140", "limited")
                self.assertEqual(ledger.snapshot(), before)
                ledger.choose("aemusa_ms.1140", "ordinary")
                self.assertEqual(route(ledger), "aemusa_ms.1150")
                ledger.step("aemusa_ms.1150", "study")
                self.assertNotIn(PREFIX + "crisis_intervention_performed", ledger.flags)
                finish_response(ledger)
                ledger.global_flags.add("prethoryn_invasion_defeated")
                finish_chapter(ledger)
                self.assertEqual(ledger.variables[PREFIX + "chapter_index"], 8)
                self.assertNotIn(PREFIX + "crisis_intervention_performed", ledger.flags)

    def test_insufficient_resources_and_forced_finale_cannot_advance(self):
        ledger = prepared()
        ledger.step("aemusa_ms.1140", "ordinary")
        self.assertEqual(route(ledger), "aemusa_ms.1150")
        ledger.resources["energy"] = 499
        before = ledger.snapshot()
        ledger.choose("aemusa_ms.1150", "care")
        self.assertEqual(ledger.snapshot(), before)
        ledger.open("aemusa_ms.1250", forced=True)
        ledger.choose("aemusa_ms.1250", "finish")
        self.assertEqual(ledger.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
