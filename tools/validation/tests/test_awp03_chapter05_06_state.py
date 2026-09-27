"""执行第五、六章账本片段；回调事实由测试显式注入。

该解释器不模拟 Stellaris 战争、UI 或读档，只检验已写脚本的门禁和副作用。
"""

import unittest

from test_awp02_state import EVENTS, Ledger, PREFIX, read_script, scalar


WAR_EVENTS = {}
for path in (
    "mod/events/aemusa_main_story_awp_03_chapter_05_events.txt",
    "mod/events/aemusa_main_story_awp_03_chapter_06_events.txt",
):
    WAR_EVENTS.update({
        scalar(entry.value, "id"): entry.value
        for entry in read_script(path)
        if entry.key == "country_event"
    })
ALL_EVENTS = {**EVENTS, **WAR_EVENTS}


def prepared(outcome="ongoing"):
    ledger = Ledger(events=ALL_EVENTS)
    ledger.variables[PREFIX + "chapter_index"] = 5
    ledger.variables[PREFIX + "act_index"] = 1
    ledger.variables[PREFIX + "fe_war_public_accountability_index"] = 1
    ledger.flags.update({
        PREFIX + "chapter_04_completed",
        PREFIX + "settlement_chapter_04_done",
        PREFIX + "history_fallen_empire_war_started",
    })
    if outcome != "ongoing":
        ledger.flags.add(PREFIX + "history_fallen_empire_war_completed")
        ledger.flags.add(PREFIX + {
            "victory": "fe_war_player_victory",
            "defeat": "fe_war_player_defeat",
            "status_quo": "fe_war_status_quo",
        }[outcome])
    return ledger


def run_first_three(ledger, priority):
    for event, option, next_event in (
        ("aemusa_ms.800", "continue", "aemusa_ms.810"),
        ("aemusa_ms.810", "continue", "aemusa_ms.820"),
        ("aemusa_ms.820", priority,
         "aemusa_ms.830" if PREFIX + "fe_war_player_victory" in ledger.flags
         else "aemusa_ms.104"),
    ):
        ledger.step(event, option)
        assert ledger.queue.pop() == (next_event, 0)


class Chapter05And06StateTests(unittest.TestCase):
    def test_without_war_history_forced_entry_has_no_effect(self):
        ledger = prepared()
        ledger.flags.remove(PREFIX + "history_fallen_empire_war_started")
        before = ledger.snapshot()
        ledger.open("aemusa_ms.800", forced=True)
        ledger.choose("aemusa_ms.800", "continue")
        self.assertEqual(ledger.snapshot(), before)

    def test_ongoing_war_waits_then_same_war_victory_unlocks(self):
        ledger = prepared()
        run_first_three(ledger, "civilians")
        self.assertEqual(ledger.variables[PREFIX + "fe_war_response_priority_index"], 1)
        before = ledger.snapshot()
        ledger.open("aemusa_ms.830", forced=True)
        ledger.choose("aemusa_ms.830", "continue")
        self.assertEqual(ledger.snapshot(), before)
        ledger.flags.update({
            PREFIX + "history_fallen_empire_war_completed",
            PREFIX + "fe_war_player_victory",
        })
        ledger.open("aemusa_ms.100")
        self.assertEqual(ledger.queue.pop(), ("aemusa_ms.830", 0))
        ledger.step("aemusa_ms.830", "continue")
        self.assertEqual(ledger.queue.pop(), ("aemusa_ms.840", 0))
        ledger.step("aemusa_ms.840", "finish")
        self.assertEqual(ledger.variables[PREFIX + "chapter_index"], 6)
        self.assertEqual(ledger.queue.pop(), ("aemusa_ms.900", 0))

    def test_defeat_and_status_quo_never_count_as_victory(self):
        for outcome in ("defeat", "status_quo"):
            with self.subTest(outcome=outcome):
                ledger = prepared(outcome)
                run_first_three(ledger, "fleet")
                self.assertEqual(ledger.variables[PREFIX + "fe_war_response_priority_index"], 2)
                before = ledger.snapshot()
                ledger.open("aemusa_ms.830", forced=True)
                ledger.choose("aemusa_ms.830", "continue")
                ledger.open("aemusa_ms.900", forced=True)
                ledger.choose("aemusa_ms.900", "continue")
                self.assertEqual(ledger.snapshot(), before)
                ledger.open("aemusa_ms.100")
                self.assertEqual(ledger.queue.pop(), ("aemusa_ms.104", 0))

    def test_preexisting_victory_completes_both_chapters_without_writing_result(self):
        for priority in ("civilians", "fleet"):
            for disclosure in ("open", "phased"):
                for recovery in ("domestic", "shared"):
                    with self.subTest(priority=priority, disclosure=disclosure,
                                      recovery=recovery):
                        ledger = prepared("victory")
                        war_flags = {
                            flag for flag in ledger.flags
                            if flag.startswith(PREFIX + "fe_war_player_")
                            or flag == PREFIX + "history_fallen_empire_war_completed"
                        }
                        run_first_three(ledger, priority)
                        for event, option, next_event in (
                            ("aemusa_ms.830", "continue", "aemusa_ms.840"),
                            ("aemusa_ms.840", "finish", "aemusa_ms.900"),
                            ("aemusa_ms.900", "continue", "aemusa_ms.910"),
                            ("aemusa_ms.910", "continue", "aemusa_ms.920"),
                            ("aemusa_ms.920", disclosure, "aemusa_ms.930"),
                            ("aemusa_ms.930", "continue", "aemusa_ms.940"),
                            ("aemusa_ms.940", recovery, "aemusa_ms.990"),
                        ):
                            ledger.step(event, option)
                            self.assertEqual(ledger.queue.pop(), (next_event, 0))
                            before = ledger.snapshot()
                            if event.endswith(".920"):
                                ledger.choose(event, "phased" if disclosure == "open" else "open")
                            elif event.endswith(".940"):
                                ledger.choose(event, "shared" if recovery == "domestic" else "domestic")
                            else:
                                ledger.choose(event, option)
                            self.assertEqual(ledger.snapshot(), before)
                        ledger.step("aemusa_ms.990", "finish")
                        self.assertEqual(ledger.variables[PREFIX + "chapter_index"], 7)
                        self.assertEqual(ledger.variables[PREFIX + "act_index"], 2)
                        self.assertIn(PREFIX + "chapter_06_completed", ledger.flags)
                        self.assertIn(PREFIX + "act_02_completed", ledger.flags)
                        self.assertIn(PREFIX + "history_fallen_empire_war_settled", ledger.flags)
                        self.assertIn(PREFIX + "fe_war_recovery_period_active", ledger.flags)
                        self.assertEqual(ledger.variables[PREFIX + "fe_war_postwar_disclosure_index"],
                                         1 if disclosure == "open" else 2)
                        self.assertEqual(ledger.variables[PREFIX + "fe_war_recovery_priority_index"],
                                         1 if recovery == "domestic" else 2)
                        self.assertEqual({
                            flag for flag in ledger.flags
                            if flag.startswith(PREFIX + "fe_war_player_")
                            or flag == PREFIX + "history_fallen_empire_war_completed"
                        }, war_flags)
                        before = ledger.snapshot()
                        ledger.choose("aemusa_ms.990", "finish")
                        self.assertEqual(ledger.snapshot(), before)

    def test_forced_chapter_six_cannot_skip_fifth_or_choices(self):
        ledger = prepared("victory")
        before = ledger.snapshot()
        ledger.open("aemusa_ms.900", forced=True)
        ledger.choose("aemusa_ms.900", "continue")
        ledger.open("aemusa_ms.990", forced=True)
        ledger.choose("aemusa_ms.990", "finish")
        self.assertEqual(ledger.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
