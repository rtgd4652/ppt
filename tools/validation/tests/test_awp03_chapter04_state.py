"""执行第四章真实账本片段，验证战争入口和旧窗口幂等性。

此测试不模拟 Stellaris 回调；宣战与胜利旗标由测试明确注入，游戏内仍需独立验收。
"""

import unittest

from test_awp02_state import EVENTS, Ledger, PREFIX, read_script, scalar


CHAPTER_EVENTS = {
    scalar(entry.value, "id"): entry.value
    for entry in read_script("mod/events/aemusa_main_story_awp_03_story_events.txt")
    if entry.key == "country_event"
}
ALL_EVENTS = {**EVENTS, **CHAPTER_EVENTS}


def prepared(war_started=False, won=False):
    ledger = Ledger(events=ALL_EVENTS)
    ledger.variables[PREFIX + "chapter_index"] = 4
    ledger.variables[PREFIX + "act_index"] = 1
    ledger.flags.update({
        PREFIX + "chapter_03_completed",
        PREFIX + "settlement_chapter_03_done",
    })
    if war_started:
        ledger.flags.add(PREFIX + "history_fallen_empire_war_started")
    if won:
        ledger.flags.update({
            PREFIX + "history_fallen_empire_war_completed",
            PREFIX + "fe_war_player_victory",
        })
    return ledger


class Chapter04StateTests(unittest.TestCase):
    def test_without_real_war_only_wait_page_opens(self):
        ledger = prepared()
        ledger.open("aemusa_ms.100")
        self.assertEqual(ledger.queue.pop(), ("aemusa_ms.103", 0))
        before = ledger.snapshot()
        ledger.open("aemusa_ms.700", forced=True)
        ledger.choose("aemusa_ms.700", "continue")
        ledger.open("aemusa_ms.740", forced=True)
        ledger.choose("aemusa_ms.740", "finish")
        self.assertEqual(ledger.snapshot(), before)

    def test_both_public_decisions_settle_once_without_writing_war_result(self):
        for decision in ("open", "phased"):
            with self.subTest(decision=decision):
                ledger = prepared(war_started=True)
                ledger.open("aemusa_ms.100")
                self.assertEqual(ledger.queue.pop(), ("aemusa_ms.700", 0))
                steps = [
                    ("aemusa_ms.700", "continue", "aemusa_ms.710"),
                    ("aemusa_ms.710", "continue", "aemusa_ms.720"),
                    ("aemusa_ms.720", "continue", "aemusa_ms.730"),
                    ("aemusa_ms.730", decision, "aemusa_ms.740"),
                ]
                for event, option, next_event in steps:
                    ledger.step(event, option)
                    self.assertEqual(ledger.queue.pop(), (next_event, 0))
                    before = ledger.snapshot()
                    for stale in ("open", "phased") if event.endswith(".730") else (option,):
                        ledger.choose(event, stale)
                        self.assertEqual(ledger.snapshot(), before)
                ledger.step("aemusa_ms.740", "finish")
                self.assertEqual(ledger.variables[PREFIX + "chapter_index"], 5)
                self.assertEqual(ledger.variables[PREFIX + "fe_war_public_accountability_index"],
                                 1 if decision == "open" else 2)
                self.assertIn(PREFIX + "chapter_04_completed", ledger.flags)
                self.assertIn(PREFIX + "settlement_chapter_04_done", ledger.flags)
                self.assertFalse(any(PREFIX + result in ledger.flags for result in (
                    "history_fallen_empire_war_completed", "fe_war_player_victory",
                    "fe_war_player_defeat", "fe_war_status_quo")))
                before = ledger.snapshot()
                ledger.choose("aemusa_ms.740", "finish")
                self.assertEqual(ledger.snapshot(), before)

    def test_chapter_four_preserves_preexisting_war_victory(self):
        ledger = prepared(war_started=True, won=True)
        for event, option in (
            ("aemusa_ms.700", "continue"),
            ("aemusa_ms.710", "continue"),
            ("aemusa_ms.720", "continue"),
            ("aemusa_ms.730", "open"),
            ("aemusa_ms.740", "finish"),
        ):
            ledger.step(event, option)
            ledger.queue.clear()
        self.assertIn(PREFIX + "history_fallen_empire_war_completed", ledger.flags)
        self.assertIn(PREFIX + "fe_war_player_victory", ledger.flags)

    def test_forced_later_cluster_cannot_skip_predecessors(self):
        ledger = prepared(war_started=True)
        before = ledger.snapshot()
        ledger.open("aemusa_ms.730", forced=True)
        ledger.choose("aemusa_ms.730", "phased")
        ledger.open("aemusa_ms.740", forced=True)
        ledger.choose("aemusa_ms.740", "finish")
        self.assertEqual(ledger.snapshot(), before)

    def test_missing_public_decision_cannot_start_chapter_settlement(self):
        ledger = prepared(war_started=True)
        ledger.flags.add(PREFIX + "cluster_aed_04_30_settled")
        before = ledger.snapshot()
        ledger.open("aemusa_ms.740", forced=True)
        ledger.choose("aemusa_ms.740", "finish")
        self.assertEqual(ledger.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
