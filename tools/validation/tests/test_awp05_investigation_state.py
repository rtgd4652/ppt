"""检查新增调查主流程、实际支出与两方决定；不模拟引擎或穷举选择。"""

from copy import deepcopy
import unittest

from test_awp02_state import PREFIX, read_script, scalar
from test_awp04_entry_state import CrisisLedger


class InvestigationLedger(CrisisLedger):
    def __init__(self):
        super().__init__()
        self.level = 12
        for chapter in (8, 9, 10):
            self.events.update({scalar(entry.value, "id"): entry.value for entry in
                                read_script(f"mod/events/aemusa_main_story_chapter_{chapter:02}_events.txt")
                                if entry.key == "country_event"})

    def term(self, entry):
        if entry.key == "event_target:aemusa_leader":
            return self.condition(entry.value)
        if entry.key == "has_base_skill_greater_equal":
            return self.level >= int(entry.value)
        return super().term(entry)


def ready():
    ledger = InvestigationLedger()
    ledger.variables.update({PREFIX + "chapter_index": 8, PREFIX + "act_index": 3})
    ledger.flags.update(PREFIX + name for name in (
        "chapter_07_completed", "history_vanilla_crisis_settled", "crisis_response_completed",
        "fe_war_recovery_reviewed", "crisis_anomaly_investigation_ready"))
    return ledger


def route(ledger):
    ledger.queue.clear()
    ledger.open("aemusa_ms.1300")
    event, days = ledger.queue.pop()
    while event in ("aemusa_ms.1331", "aemusa_ms.1411", "aemusa_ms.1526"):
        assert days == 0
        ledger.open(event)
        event, days = ledger.queue.pop()
    assert days == 0
    return event


def start_sources(ledger):
    ledger.step("aemusa_ms.1310", "start")
    ledger.step("aemusa_ms.1320", "samples")


def finish_sources(ledger):
    start_sources(ledger)
    for source in ("astronomy", "laboratory", "risk"):
        ledger.step("aemusa_ms.1330", source)
        ledger.elapse(30)
        assert route(ledger) == "aemusa_ms.1332"
        ledger.step("aemusa_ms.1332", "record")
    ledger.step("aemusa_ms.1330", "gather")
    ledger.step("aemusa_ms.1340", "phased")
    ledger.step("aemusa_ms.1350", "model")


def reach_hearing_decision(ledger):
    finish_sources(ledger)
    assert route(ledger) == "aemusa_ms.1410"
    ledger.step("aemusa_ms.1410", "verify")
    assert route(ledger) == "aemusa_ms.1415"
    ledger.elapse(45)
    assert route(ledger) == "aemusa_ms.1410"
    ledger.step("aemusa_ms.1410", "contact")
    for event, option in ((1420, "continue"), (1430, "responsibility"),
                          (1440, "public"), (1450, "archive"),
                          (1510, "hearing"), (1520, "protect")):
        assert route(ledger) == f"aemusa_ms.{event}"
        ledger.step(f"aemusa_ms.{event}", option)
    assert route(ledger) == "aemusa_ms.1530"
    ledger.open("aemusa_ms.1530")


class Awp05InvestigationTests(unittest.TestCase):
    def test_main_flow_spends_resources_and_keeps_final_authority_separate(self):
        ledger = ready()
        ledger.open("aemusa_ms.100")
        self.assertEqual(ledger.queue.pop(), ("aemusa_ms.1300", 0))
        reach_hearing_decision(ledger)
        self.assertEqual(ledger.resources, {"energy": 200, "minerals": 600})
        self.assertEqual(ledger.variables[PREFIX + "chapter_index"], 10)
        self.assertEqual(ledger.variables[PREFIX + "investigation_aemusa_decision_index"], 1)
        self.assertNotIn(PREFIX + "investigation_player_support_confirmed", ledger.flags)
        ledger.choose("aemusa_ms.1530", "support")
        ledger.step("aemusa_ms.1540", "care")
        ledger.step("aemusa_ms.1550", "prepare")
        self.assertEqual(route(ledger), "aemusa_ms.1560")
        self.assertEqual(ledger.variables[PREFIX + "chapter_index"], 11)
        self.assertEqual(ledger.variables[PREFIX + "act_index"], 4)
        self.assertEqual(ledger.variables[PREFIX + "investigation_level_snapshot_index"], 1)
        self.assertIn(PREFIX + "act_04_completed", ledger.flags)
        self.assertNotIn("aemusa_ms_decision_player_authorized", ledger.flags)
        self.assertNotIn("aemusa_ms_decision_aemusa_accepted", ledger.flags)
        self.assertNotIn("aemusa_ms_truth_world_difference_mutually_confirmed", ledger.flags)
        self.assertNotIn(PREFIX + "final_gate_level_30_met", ledger.flags)
        before = ledger.snapshot()
        ledger.choose("aemusa_ms.1550", "prepare")
        self.assertEqual(ledger.snapshot(), before)

    def test_each_source_is_unique_and_wait_resumes_from_persistent_state(self):
        ledger = ready()
        start_sources(ledger)
        ledger.step("aemusa_ms.1330", "astronomy")
        before = ledger.snapshot()
        ledger.choose("aemusa_ms.1330", "laboratory")
        ledger.open("aemusa_ms.1350", forced=True)
        ledger.choose("aemusa_ms.1350", "model")
        self.assertEqual(ledger.snapshot(), before)
        # 这里只回放持久状态，真实游戏保存与载入另作关键运行检查。
        ledger = deepcopy(ledger)
        ledger.elapse(29)
        self.assertEqual(route(ledger), "aemusa_ms.1335")
        self.assertNotIn(PREFIX + "investigation_evidence_astronomy", ledger.flags)
        ledger.elapse(1)
        self.assertEqual(route(ledger), "aemusa_ms.1332")
        self.assertIn(PREFIX + "investigation_evidence_astronomy", ledger.flags)
        self.assertNotIn(PREFIX + "investigation_evidence_laboratory", ledger.flags)
        before = ledger.snapshot()
        ledger.choose("aemusa_ms.1330", "astronomy")
        ledger.choose("aemusa_ms.1330", "gather")
        self.assertEqual(ledger.snapshot(), before)

    def test_insufficient_resources_and_forced_hearing_do_not_write(self):
        ledger = ready()
        start_sources(ledger)
        ledger.resources["energy"] = 199
        before = ledger.snapshot()
        ledger.choose("aemusa_ms.1330", "astronomy")
        ledger.open("aemusa_ms.1530", forced=True)
        ledger.choose("aemusa_ms.1530", "support")
        ledger.open("aemusa_ms.1550", forced=True)
        ledger.choose("aemusa_ms.1550", "prepare")
        self.assertEqual(ledger.snapshot(), before)

    def test_refusal_requires_review_and_does_not_erase_history(self):
        ledger = ready()
        ledger.flags.add(PREFIX + "first_intervention_oracle_narrative_recorded")
        reach_hearing_decision(ledger)
        self.assertEqual(ledger.variables[PREFIX + "investigation_aemusa_decision_index"], 2)
        before = ledger.snapshot()
        ledger.choose("aemusa_ms.1530", "support")
        self.assertEqual(ledger.snapshot(), before)
        ledger.choose("aemusa_ms.1530", "review")
        ledger.step("aemusa_ms.1525", "repair")
        self.assertEqual(route(ledger), "aemusa_ms.1527")
        ledger.elapse(30)
        self.assertEqual(route(ledger), "aemusa_ms.1530")
        ledger.open("aemusa_ms.1530")
        self.assertEqual(ledger.variables[PREFIX + "investigation_aemusa_decision_index"], 1)
        self.assertIn(PREFIX + "investigation_refusal_recorded", ledger.flags)
        self.assertIn(PREFIX + "first_intervention_oracle_narrative_recorded", ledger.flags)
        self.assertIn(PREFIX + "first_intervention_attribution_corrected", ledger.flags)
        self.assertNotIn(PREFIX + "investigation_player_support_confirmed", ledger.flags)


if __name__ == "__main__":
    unittest.main()
