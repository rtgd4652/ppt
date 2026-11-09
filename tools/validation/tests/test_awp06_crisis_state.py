"""回放真实危机脚本的账本保护，不模拟舰队、项目、巨构或引擎回调。

仅提供明确的外部接口夹具和一个行星矿藏集合，核对要求移除的 key、
一次性结算与权限边界。这里的通过不能替代游戏内损失或存读档验证。
"""

from copy import deepcopy
import operator
import re
import unittest

from test_awp02_state import ROOT, PREFIX, child, expand, scalar
from test_awp04_entry_state import CrisisLedger
from check_mod import parse


CRISIS = "aemusa_ms_crisis_"
HOST = "event_target:aemusa_ms_current_anchor_target"
OWNER = "event_target:aemusa_ms_crisis_route_owner"
BRIEFING = "event_target:aemusa_ms_linked_briefing_target"


def read_crisis_script(relative):
    """局部保留新代码的数字比较，不放宽旧解释器的未知语法检查。"""
    source = (ROOT / relative).read_text(encoding="utf-8")
    names = {">=": "ge", "<=": "le", ">": "gt", "<": "lt"}
    source = re.sub(
        r"\b(value|amount)\s*(>=|<=|>|<)\s*(-?\d+(?:\.\d+)?)",
        lambda match: f"{match[1]}_{names[match[2]]} = {match[3]}", source,
    )
    if re.search(r"[<>!]", re.sub(r"#[^\n]*", "", source)):
        raise AssertionError("危机账本测试遇到未支持的比较运算符")
    return parse(source)


TRIGGERS = {item.key: item.value for item in read_crisis_script(
    "mod/common/scripted_triggers/aemusa_ms_exclusive_triggers.txt")}
EFFECTS = {item.key: item.value for item in read_crisis_script(
    "mod/common/scripted_effects/aemusa_ms_exclusive_effects.txt")}
EVENTS = {scalar(item.value, "id"): item.value for item in read_crisis_script(
    "mod/events/aemusa_ms_exclusive_events.txt") if item.key == "country_event"}


class ExclusiveLedger(CrisisLedger):
    # 只提供已在外部确认的接口结果，不实现真实到场、控制权与巨构状态。
    EXTERNAL_CONDITIONS = {
        "aemusa_ms_anchor_controlled", "aemusa_ms_flagship_at_current_anchor",
        "aemusa_ms_baseline_operational", "aemusa_ms_has_anchor_candidate",
        "aemusa_ms_anchor_reachable", "aemusa_ms_has_operational_flagship",
        "artifact_crisis_intelligence_identified",
    }
    EXTERNAL_EFFECTS = {
        "aemusa_ms_flagship_ensure_present", "aemusa_ms_flagship_monthly_update",
        "aemusa_ms_baseline_monthly_update", "random_system_within_border",
    }

    def __init__(self):
        super().__init__()
        self.events.update(EVENTS)
        self.variables.update({PREFIX + "chapter_index": 11, PREFIX + "act_index": 4})
        self.flags.update(PREFIX + key for key in (
            "chapter_10_completed", "history_vanilla_crisis_settled",
            "investigation_joint_response_authorized",
        ))
        self.scope = "country"
        self.targets = {HOST, OWNER}
        self.host_number = 1
        self.briefing_host = None
        self.planet_flags = {"aemusa_ms_anchor_active", "aemusa_ms_anchor_minerals_2"}
        self.deposits = {"d_minerals_2", "d_energy_5"}
        self.removed_deposits = []
        self.external_conditions = {name: True for name in self.EXTERNAL_CONDITIONS}
        self.external_conditions["artifact_crisis_intelligence_identified"] = False
        self.external_requests = []
        self.projects = set()

    def snapshot(self):
        return deepcopy((super().snapshot(), self.targets, self.planet_flags,
                         self.deposits, self.removed_deposits, self.external_requests, self.projects,
                         self.host_number, self.briefing_host))

    def in_scope(self, target, operation, entries):
        if target not in self.targets:
            raise AssertionError(f"夹具中不存在目标：{target}")
        previous = self.scope
        self.scope = {HOST: "planet", OWNER: "country", BRIEFING: "briefing_planet"}[target]
        try:
            return operation(entries)
        finally:
            self.scope = previous

    def term(self, entry):
        key, value = entry.key, entry.value
        if key in self.EXTERNAL_CONDITIONS:
            result = self.external_conditions[key]
            return result if value == "yes" else not result
        if key in TRIGGERS:
            return self.condition(TRIGGERS[key]) == (value == "yes")
        if key in (HOST, OWNER, BRIEFING):
            return self.in_scope(key, self.condition, value)
        if key == "exists" and value in (HOST, OWNER, BRIEFING):
            return value in self.targets
        if key == "is_same_value" and value == HOST:
            assert self.scope == "briefing_planet"
            return HOST in self.targets and self.briefing_host == self.host_number
        if key == "is_colony":
            assert self.scope == "planet"
            return value == "no"
        if key == "has_planet_flag":
            assert self.scope == "planet"
            return value in self.planet_flags
        if key == "has_deposit":
            assert self.scope == "planet"
            return value in self.deposits
        if key == "has_special_project":
            assert self.scope == "country"
            return value in self.projects
        if key in ("check_variable", "has_resource"):
            if key == "check_variable":
                assert self.scope == "country"
                current = self.variables.get(scalar(value, "which"), 0)
                field = "value"
            else:
                current = self.resources[scalar(value, "type")]
                field = "amount"
            for suffix, comparison in (("ge", operator.ge), ("le", operator.le),
                                       ("gt", operator.gt), ("lt", operator.lt)):
                expected = scalar(value, field + "_" + suffix)
                if expected is not None:
                    return comparison(current, float(expected))
            if key == "has_resource":
                return current == float(scalar(value, field))
        return super().term(entry)

    def execute_extra(self, entry):
        key, value = entry.key, entry.value
        if key in EFFECTS:
            arguments = {item.key: item.value for item in value} if isinstance(value, list) else {}
            self.execute(expand(EFFECTS[key], arguments))
        elif key in self.EXTERNAL_EFFECTS:
            self.external_requests.append(key)
        elif key == "change_variable":
            name = scalar(value, "which")
            delta = scalar(value, "value")
            amount = self.variables[delta] if delta in self.variables else float(delta)
            self.variables[name] = self.variables.get(name, 0) + amount
        elif key == "save_event_target_as" and "event_target:" + value == BRIEFING:
            assert self.scope == "planet"
            self.briefing_host = self.host_number
            self.targets.add(BRIEFING)
        elif key == "save_global_event_target_as":
            self.targets.add("event_target:" + value)
        elif key == "clear_global_event_target":
            self.targets.discard("event_target:" + value)
        elif key == "abort_special_project":
            # 只核对请求取消哪项现有项目；不模拟引擎项目与科研船调度。
            self.projects.discard(scalar(value, "type"))
        elif key in (HOST, OWNER):
            self.in_scope(key, self.execute, value)
        elif key == "remove_deposit":
            assert self.scope == "planet"
            self.deposits.remove(value)
            self.removed_deposits.append(value)
        elif key == "set_planet_flag":
            assert self.scope == "planet"
            self.planet_flags.add(value)
        elif key == "remove_planet_flag":
            assert self.scope == "planet"
            self.planet_flags.discard(value)
        else:
            super().execute_extra(entry)

    def effect(self, name):
        self.execute(EFFECTS[name])


def active_anchor():
    ledger = ExclusiveLedger()
    ledger.effect("aemusa_ms_exclusive_initialize")
    ledger.variables.update({
        PREFIX + "chapter_index": 12,
        PREFIX + "anchor_stage": 30,
        PREFIX + "anchor_result": 0,
        PREFIX + "anchor_pressure": 12,
        PREFIX + "anchor_analysis_ticks": 0,
    })
    ledger.flags.update({PREFIX + "chapter_11_completed", PREFIX + "anchor_projection_spawned"})
    return ledger


class Awp06CrisisStateTests(unittest.TestCase):
    def test_unreachable_pre_warning_target_can_relocate_but_recovery_cannot(self):
        ledger = ExclusiveLedger()
        ledger.effect("aemusa_ms_exclusive_initialize")
        ledger.variables[PREFIX + "anchor_stage"] = 10
        ledger.flags.update(PREFIX + name for name in (
            "anchor_baseline_recorded", "exclusive_laboratory_verified",
            "exclusive_public_response_ready"))
        ledger.external_conditions["aemusa_ms_anchor_reachable"] = False
        before = ledger.snapshot()
        ledger.effect("aemusa_ms_anchor_confirm")
        self.assertEqual(ledger.snapshot(), before)
        recovering = deepcopy(ledger)
        recovering.external_conditions["aemusa_ms_has_operational_flagship"] = False
        before = recovering.snapshot()
        recovering.choose("aemusa_exclusive.20", "relocate")
        self.assertEqual(recovering.snapshot(), before)
        warned = deepcopy(ledger)
        warned.variables[PREFIX + "anchor_stage"] = 20
        warned.flags.add(PREFIX + "anchor_warning_active")
        before = warned.snapshot()
        warned.choose("aemusa_exclusive.20", "relocate")
        self.assertEqual(warned.snapshot(), before)
        ledger.choose("aemusa_exclusive.20", "relocate")
        self.assertEqual(ledger.variables[PREFIX + "anchor_stage"], 0)
        self.assertNotIn(PREFIX + "anchor_baseline_recorded", ledger.flags)
        self.assertIn(PREFIX + "exclusive_laboratory_verified", ledger.flags)
        self.assertIn(PREFIX + "exclusive_public_response_ready", ledger.flags)

    def test_preparation_actions_stay_visible_but_cannot_spend_missing_resources(self):
        for action, energy, minerals, pending in (
            ("laboratory", 150, 50, "exclusive_laboratory_pending"),
            ("response", 200, 150, "exclusive_public_response_pending"),
        ):
            with self.subTest(action=action):
                ledger = ExclusiveLedger()
                ledger.effect("aemusa_ms_exclusive_initialize")
                ledger.variables[PREFIX + "anchor_stage"] = 10
                option = ledger.option("aemusa_exclusive.20", action)
                ledger.resources = {"energy": energy - 1, "minerals": minerals}
                self.assertTrue(ledger.condition(child(option, "trigger")))
                self.assertFalse(ledger.condition(child(option, "allow")))
                before = ledger.snapshot()
                ledger.choose("aemusa_exclusive.20", action)
                self.assertEqual(ledger.snapshot(), before)
                ledger.resources["energy"] += 1
                self.assertTrue(ledger.condition(child(option, "allow")))
                ledger.choose("aemusa_exclusive.20", action)
                self.assertEqual(ledger.resources, {"energy": 0, "minerals": 0})
                self.assertIn(PREFIX + pending, ledger.flags)
                self.assertFalse(ledger.condition(child(option, "trigger")))
                before = ledger.snapshot()
                ledger.choose("aemusa_exclusive.20", action)
                self.assertEqual(ledger.snapshot(), before)

    def test_only_invalid_pre_warning_target_can_be_released_without_resetting_progress(self):
        ledger = ExclusiveLedger()
        ledger.effect("aemusa_ms_exclusive_initialize")
        ledger.variables[PREFIX + "anchor_stage"] = 10
        ledger.variables[PREFIX + "anchor_losses"] = 1
        ledger.flags.update(PREFIX + key for key in (
            "exclusive_laboratory_verified", "exclusive_public_response_pending",
            "loss_has_permanent_losses", "anchor_baseline_recorded",
        ))
        ledger.timers[PREFIX + "exclusive_public_response_timer"] = 12
        ledger.planet_flags.add("aemusa_ms_anchor_used")
        ledger.projects.add("AEMUSA_MS_ANCHOR_SURVEY")

        # 有效目标不能靠旧选项重选；公开预警后的失效目标也不能重置计时。
        before = ledger.snapshot()
        ledger.choose("aemusa_exclusive.20", "relocate")
        self.assertEqual(ledger.snapshot(), before)
        ledger.deposits.remove("d_minerals_2")
        warned = deepcopy(ledger)
        warned.variables[PREFIX + "anchor_stage"] = 20
        warned.flags.add(PREFIX + "anchor_warning_active")
        before = warned.snapshot()
        warned.choose("aemusa_exclusive.20", "relocate")
        self.assertEqual(warned.snapshot(), before)

        ledger.choose("aemusa_exclusive.20", "relocate")
        self.assertEqual(ledger.variables[PREFIX + "anchor_stage"], 0)
        self.assertNotIn(HOST, ledger.targets)
        self.assertNotIn("aemusa_ms_anchor_active", ledger.planet_flags)
        self.assertIn("aemusa_ms_anchor_used", ledger.planet_flags)
        self.assertNotIn("AEMUSA_MS_ANCHOR_SURVEY", ledger.projects)
        self.assertNotIn(PREFIX + "anchor_baseline_recorded", ledger.flags)
        self.assertIn(PREFIX + "exclusive_laboratory_verified", ledger.flags)
        self.assertIn(PREFIX + "exclusive_public_response_pending", ledger.flags)
        self.assertEqual(ledger.timers[PREFIX + "exclusive_public_response_timer"], 12)
        self.assertEqual(ledger.variables[PREFIX + "anchor_losses"], 1)
        self.assertEqual(ledger.queue[-1], ("aemusa_exclusive.1", 0))

    def test_initialization_requires_current_authority_and_never_resets_history(self):
        blocked = ExclusiveLedger()
        blocked.flags.discard(PREFIX + "investigation_joint_response_authorized")
        before = blocked.snapshot()
        blocked.choose("aemusa_exclusive.10", "begin")
        self.assertEqual(blocked.snapshot(), before)

        ledger = ExclusiveLedger()
        ledger.effect("aemusa_ms_exclusive_initialize")
        self.assertIn(CRISIS + "exclusive_initialized", ledger.flags)
        self.assertIn(PREFIX + "flagship_commissioned", ledger.flags)
        self.assertIn(PREFIX + "baseline_authorized", ledger.flags)
        ledger.variables[PREFIX + "anchor_losses"] = 1
        ledger.flags.add(PREFIX + "loss_has_permanent_losses")
        before = ledger.snapshot()
        ledger.effect("aemusa_ms_exclusive_initialize")
        ledger.choose("aemusa_exclusive.10", "begin")
        self.assertEqual(ledger.snapshot(), before)
        self.assertEqual(ledger.external_requests.count("aemusa_ms_flagship_ensure_present"), 1)

    def test_battle_record_counts_only_once_and_not_before_projection(self):
        ledger = active_anchor()
        ledger.flags.discard(PREFIX + "anchor_projection_spawned")
        before = ledger.snapshot()
        ledger.effect("aemusa_ms_anchor_record_battle")
        self.assertEqual(ledger.snapshot(), before)
        ledger.flags.add(PREFIX + "anchor_projection_spawned")
        ledger.effect("aemusa_ms_anchor_record_battle")
        self.assertEqual(ledger.variables[PREFIX + "projections_defeated"], 1)
        before = ledger.snapshot()
        ledger.effect("aemusa_ms_anchor_record_battle")
        self.assertEqual(ledger.snapshot(), before)

    def test_destroy_removes_only_locked_deposit_once_and_failure_can_archive(self):
        ledger = active_anchor()
        ledger.effect("aemusa_ms_anchor_destroy_host")
        self.assertEqual(ledger.removed_deposits, ["d_minerals_2"])
        self.assertEqual(ledger.deposits, {"d_energy_5"})
        self.assertEqual(ledger.variables[PREFIX + "anchor_losses"], 1)
        self.assertIn(PREFIX + "loss_has_permanent_losses", ledger.flags)
        before = ledger.snapshot()
        ledger.effect("aemusa_ms_anchor_destroy_host")
        ledger.effect("aemusa_ms_anchor_liberate")
        self.assertEqual(ledger.snapshot(), before)
        self.assertEqual(ledger.variables[PREFIX + "anchors_liberated"], 0)

        # 提供外部行动完成事实；并不在 Python 中模拟战斗或勘查。
        ledger.effect("aemusa_ms_anchor_record_battle")
        ledger.flags.update(PREFIX + name for name in (
            "anchor_field_evidence", "anchor_stabilization_recorded", "anchor_stabilization_window",
        ))
        self.assertTrue(ledger.condition(TRIGGERS["aemusa_ms_anchor_analysis_ready"]))
        ledger.external_conditions["aemusa_ms_baseline_operational"] = False
        self.assertFalse(ledger.condition(TRIGGERS["aemusa_ms_anchor_analysis_ready"]))
        ledger.external_conditions["aemusa_ms_baseline_operational"] = True
        ledger.variables[PREFIX + "anchor_analysis_ticks"] = 3
        ledger.effect("aemusa_ms_anchor_archive")
        self.assertEqual(ledger.variables[PREFIX + "anchors_archived"], 1)
        self.assertIn(PREFIX + "anchor_1_destroyed", ledger.flags)
        self.assertNotIn(PREFIX + "anchor_1_liberated", ledger.flags)
        self.assertEqual(ledger.variables[PREFIX + "anchor_losses"], 1)
        before = ledger.snapshot()
        ledger.effect("aemusa_ms_anchor_archive")
        self.assertEqual(ledger.snapshot(), before)

    def test_external_resource_change_is_not_claimed_as_new_crisis_loss(self):
        ledger = active_anchor()
        ledger.deposits.remove("d_minerals_2")
        ledger.variables[PREFIX + "anchor_losses"] = 1
        ledger.flags.add(PREFIX + "loss_has_permanent_losses")
        ledger.effect("aemusa_ms_anchor_destroy_host")
        self.assertEqual(ledger.removed_deposits, [])
        self.assertEqual(ledger.variables[PREFIX + "anchor_result"], 2)
        self.assertEqual(ledger.variables[PREFIX + "anchor_losses"], 1)
        self.assertIn(PREFIX + "anchor_external_change_recorded", ledger.flags)

    def test_final_settlement_requires_both_counts_and_separate_future_action(self):
        ledger = active_anchor()
        ledger.variables.update({PREFIX + "chapter_index": 13, PREFIX + "anchor_stage": 40,
                                 PREFIX + "anchors_archived": 3, PREFIX + "projections_defeated": 3})
        ledger.flags.add(CRISIS + "weakness_verified")
        for absent in ("anchors_archived", "projections_defeated", "future"):
            with self.subTest(absent=absent):
                trial = deepcopy(ledger)
                trial.flags.add(PREFIX + "exclusive_future_reopened")
                if absent == "future":
                    trial.flags.discard(PREFIX + "exclusive_future_reopened")
                else:
                    trial.variables[PREFIX + absent] = 2
                before = trial.snapshot()
                trial.choose("aemusa_exclusive.60", "settle")
                self.assertEqual(trial.snapshot(), before)

        ledger.effect("aemusa_ms_exclusive_reopen_future")
        self.assertIn(PREFIX + "exclusive_future_reopened", ledger.flags)
        self.assertNotIn(CRISIS + "exclusive_completed", ledger.flags)
        before = ledger.snapshot()
        ledger.effect("aemusa_ms_exclusive_reopen_future")
        self.assertEqual(ledger.snapshot(), before)
        ledger.effect("aemusa_ms_exclusive_settle")
        self.assertIn(CRISIS + "exclusive_completed", ledger.flags)
        self.assertEqual(ledger.variables[CRISIS + "exclusive_phase_index"], 60)
        self.assertEqual(ledger.variables[PREFIX + "chapter_index"], 13)
        before = ledger.snapshot()
        ledger.effect("aemusa_ms_exclusive_settle")
        self.assertEqual(ledger.snapshot(), before)

        ledger.choose("aemusa_exclusive.80", "record")
        self.assertEqual(ledger.variables[PREFIX + "chapter_index"], 14)
        self.assertIn(PREFIX + "chapter_13_completed", ledger.flags)
        self.assertNotIn(PREFIX + "chapter_14_completed", ledger.flags)
        self.assertNotIn("aemusa_ms_decision_player_authorized", ledger.flags)
        self.assertNotIn("aemusa_ms_decision_aemusa_accepted", ledger.flags)
        self.assertNotIn(PREFIX + "final_gate_level_30_met", ledger.flags)


class LinkedCoreAnchorTests(unittest.TestCase):
    @staticmethod
    def confirmed(archived=1, losses=0):
        ledger = ExclusiveLedger()
        ledger.effect("aemusa_ms_exclusive_initialize")
        ledger.variables.update({PREFIX + "anchor_stage": 10, PREFIX + "anchor_result": 0,
                                 PREFIX + "anchor_pressure": 0, PREFIX + "anchors_archived": archived,
                                 PREFIX + "anchor_losses": losses})
        ledger.flags.update(PREFIX + name for name in (
            "anchor_baseline_recorded", "exclusive_laboratory_verified", "exclusive_public_response_ready",
        ))
        ledger.choose("aemusa_exclusive.20", "confirm")
        ledger.execute(child(EVENTS["aemusa_exclusive.1"], "immediate"))
        return ledger

    @staticmethod
    def combat(ledger):
        # 成锚生成舰队由引擎负责。夹具提供已生成事实，随后执行实际月检及战果接口。
        ledger.variables[PREFIX + "anchor_stage"] = 30
        ledger.flags.add(PREFIX + "anchor_projection_spawned")
        ledger.execute(child(EVENTS["aemusa_exclusive.1"], "immediate"))

    def test_confirmation_binds_only_future_core_nodes_and_copies_real_losses_once(self):
        for archived, losses in ((0, 0), (1, 0), (1, 1), (2, 2)):
            with self.subTest(archived=archived, losses=losses):
                ledger = self.confirmed(archived, losses)
                self.assertEqual(PREFIX + "anchor_linked" in ledger.flags, archived > 0)
                self.assertEqual(ledger.variables[PREFIX + "anchor_pressure"], losses)
                self.assertEqual(BRIEFING in ledger.targets, archived > 0)
                self.assertEqual(ledger.timers[PREFIX + "anchor_warning_active"], 90)
                ledger.elapse(20)
                again = deepcopy(ledger)
                before = again.snapshot()
                again.choose("aemusa_exclusive.20", "confirm")
                self.assertEqual(again.snapshot(), before)
                self.assertEqual(again.timers[PREFIX + "anchor_warning_active"], 70)

        old = active_anchor()
        old.variables.update({PREFIX + "anchors_archived": 2, PREFIX + "anchor_losses": 1,
                              PREFIX + "anchor_pressure": 5})
        old.effect("aemusa_ms_exclusive_monthly_update")
        self.assertEqual(old.variables[PREFIX + "anchor_pressure"], 6)
        self.assertNotIn(PREFIX + "anchor_linked", old.flags)
        self.assertNotIn(("aemusa_exclusive.32", 0), old.queue)

    def test_stale_briefing_missing_resources_and_hub_shutdown_cannot_consume(self):
        for event in ("aemusa_exclusive.25", "aemusa_exclusive.30"):
            initial = self.confirmed()
            if event.endswith(".30"):
                self.combat(initial)
            for block in ("old_host", "missing_target", "energy", "minerals", "hub", "battle", "settled"):
                with self.subTest(event=event, block=block):
                    ledger = deepcopy(initial)
                    if block == "old_host":
                        ledger.host_number += 1
                    elif block == "missing_target":
                        ledger.targets.remove(BRIEFING)
                    elif block in ("energy", "minerals"):
                        ledger.resources[block] = 299 if block == "energy" else 149
                    elif block == "hub":
                        ledger.external_conditions["aemusa_ms_baseline_operational"] = False
                    elif block == "battle":
                        ledger.flags.add(PREFIX + "anchor_battle_won")
                    else:
                        ledger.variables[PREFIX + "anchor_result"] = 2
                    self.assertFalse(ledger.condition(child(ledger.option(event, "isolate"), "allow")))
                    before = ledger.snapshot()
                    ledger.choose(event, "isolate")
                    self.assertEqual(ledger.snapshot(), before)

    def test_next_node_resets_local_response_and_preserves_costs_and_actual_losses(self):
        ledger = self.confirmed(archived=1, losses=1)
        ledger.choose("aemusa_exclusive.25", "isolate")
        ledger.flags.add(PREFIX + "anchor_pressure_warning_sent")
        ledger.variables.update({PREFIX + "anchor_pressure": 9, PREFIX + "anchor_stage": 0,
                                 PREFIX + "anchors_archived": 2, PREFIX + "anchor_isolation_ticks": 2})
        # 提供星系搜索已找到下一个真实宿主的结果，执行选中后与预警确认的源码。
        ledger.host_number += 1
        ledger.effect("aemusa_ms_anchor_select")
        self.assertEqual(ledger.variables[PREFIX + "anchor_stage"], 10)
        for flag in ("anchor_linked", "anchor_isolation_ordered", "anchor_pressure_warning_sent"):
            self.assertNotIn(PREFIX + flag, ledger.flags)
        self.assertEqual(ledger.variables[PREFIX + "anchor_pressure"], 0)
        ledger.flags.add(PREFIX + "anchor_baseline_recorded")
        ledger.choose("aemusa_exclusive.20", "confirm")
        self.assertEqual(ledger.variables[PREFIX + "anchor_pressure"], 1)
        self.assertEqual(ledger.variables[PREFIX + "anchor_isolation_ticks"], 0)
        before = ledger.snapshot()
        ledger.choose("aemusa_exclusive.25", "isolate")
        self.assertEqual(ledger.snapshot(), before)
        ledger.execute(child(EVENTS["aemusa_exclusive.1"], "immediate"))
        ledger.choose("aemusa_exclusive.25", "isolate")
        self.assertEqual(ledger.resources, {"energy": 400, "minerals": 700})
        self.assertEqual(ledger.variables[PREFIX + "anchor_losses"], 1)

    def test_warning_isolation_charges_once_and_uses_only_operating_months(self):
        for identified in (False, True):
            with self.subTest(identified=identified):
                ledger = self.confirmed()
                ledger.external_conditions["artifact_crisis_intelligence_identified"] = identified
                ledger.choose("aemusa_exclusive.25", "isolate")
                self.assertEqual(ledger.resources, {"energy": 700, "minerals": 850})
                self.assertEqual(ledger.variables[PREFIX + "anchor_isolation_ticks"], int(identified))
                interrupted = deepcopy(ledger)
                interrupted.external_conditions["aemusa_ms_baseline_operational"] = False
                interrupted.effect("aemusa_ms_exclusive_monthly_update")
                self.assertEqual(interrupted.variables[PREFIX + "anchor_isolation_ticks"], int(identified))
                before = interrupted.snapshot()
                interrupted.choose("aemusa_exclusive.25", "isolate")
                self.assertEqual(interrupted.snapshot(), before)
                interrupted.external_conditions["aemusa_ms_baseline_operational"] = True
                for _ in range(2 - int(identified)):
                    interrupted.effect("aemusa_ms_exclusive_monthly_update")
                self.assertEqual(interrupted.variables[PREFIX + "anchor_isolation_ticks"], 2)
                self.combat(interrupted)
                interrupted.effect("aemusa_ms_exclusive_monthly_update")
                self.assertEqual(interrupted.variables[PREFIX + "anchor_pressure"], 1)
                self.assertEqual(interrupted.variables[PREFIX + "anchor_isolation_ticks"], 2)
                self.assertNotIn(PREFIX + "anchor_battle_won", interrupted.flags)
                self.assertEqual(interrupted.variables[PREFIX + "projections_defeated"], 0)

    def test_briefing_reports_current_isolation_state_and_settled_result(self):
        definition = read_crisis_script("mod/common/scripted_loc/aemusa_exclusive_anchor_loc.txt")[0].value
        self.assertEqual(scalar(definition, "random"), "no")
        ledger = self.confirmed()

        def status():
            for entry in definition:
                if entry.key == "text" and ledger.condition(child(entry.value, "trigger")):
                    return scalar(entry.value, "localization_key")
            return scalar(definition, "default")

        self.assertEqual(status(), "aemusa_exclusive_link_open")
        ledger.choose("aemusa_exclusive.25", "isolate")
        self.assertEqual(status(), "aemusa_exclusive_link_working")
        ledger.external_conditions["aemusa_ms_baseline_operational"] = False
        self.assertEqual(status(), "aemusa_exclusive_link_paused")
        ledger.external_conditions["aemusa_ms_baseline_operational"] = True
        for _ in range(2):
            ledger.effect("aemusa_ms_exclusive_monthly_update")
        self.assertEqual(status(), "aemusa_exclusive_link_isolated")
        self.combat(ledger)
        ledger.effect("aemusa_ms_anchor_record_battle")
        self.assertEqual(status(), "aemusa_exclusive_link_defeated")
        for result, label in enumerate(("linked", "liberated", "lost")):
            ledger.variables[PREFIX + "anchor_result"] = result
            descriptions = [scalar(item.value, "text") for item in EVENTS["aemusa_exclusive.30"]
                            if item.key == "desc" and ledger.condition(child(item.value, "trigger"))]
            self.assertEqual(descriptions, ["aemusa_exclusive.30." + label + "_desc"])

    def test_local_window_fleet_victory_and_wartime_isolation_change_different_pressure(self):
        ledger = self.confirmed()
        self.combat(ledger)
        ledger.effect("aemusa_ms_exclusive_monthly_update")
        self.assertEqual(ledger.variables[PREFIX + "anchor_pressure"], 2)
        ledger.effect("aemusa_ms_anchor_stabilize")
        ledger.effect("aemusa_ms_exclusive_monthly_update")
        self.assertEqual(ledger.variables[PREFIX + "anchor_pressure"], 2)
        ledger.external_conditions["aemusa_ms_flagship_at_current_anchor"] = False
        ledger.effect("aemusa_ms_exclusive_monthly_update")
        self.assertEqual(ledger.variables[PREFIX + "anchor_pressure"], 4)
        ledger.choose("aemusa_exclusive.30", "isolate")
        ledger.effect("aemusa_ms_exclusive_monthly_update")
        self.assertEqual(ledger.variables[PREFIX + "anchor_pressure"], 6)
        ledger.effect("aemusa_ms_exclusive_monthly_update")
        self.assertEqual(ledger.variables[PREFIX + "anchor_pressure"], 7)
        self.assertFalse(ledger.condition(TRIGGERS["aemusa_ms_anchor_can_engineer"]))

        battle = self.confirmed()
        self.combat(battle)
        battle.effect("aemusa_ms_anchor_record_battle")
        battle.effect("aemusa_ms_exclusive_monthly_update")
        self.assertEqual(battle.variables[PREFIX + "anchor_pressure"], 1)
        self.assertEqual(battle.variables[PREFIX + "projections_defeated"], 1)
        self.assertNotIn(PREFIX + "anchor_field_evidence", battle.flags)

    def test_pressure_warning_and_actual_loss_remain_single_through_reload(self):
        ledger = self.confirmed(archived=1, losses=1)
        self.combat(ledger)
        for _ in range(4):
            ledger.effect("aemusa_ms_exclusive_monthly_update")
        self.assertEqual(ledger.variables[PREFIX + "anchor_pressure"], 9)
        self.assertEqual(ledger.queue.count(("aemusa_exclusive.32", 0)), 1)
        self.assertEqual(ledger.removed_deposits, [])
        restored = deepcopy(ledger)
        for _ in range(5):
            restored.effect("aemusa_ms_exclusive_monthly_update")
        self.assertEqual(restored.queue.count(("aemusa_exclusive.32", 0)), 1)
        self.assertEqual(restored.queue.count(("aemusa_exclusive.35", 0)), 1)
        self.assertEqual(restored.variables[PREFIX + "anchor_pressure"], 12)
        self.assertEqual(restored.removed_deposits, ["d_minerals_2"])
        self.assertEqual(restored.variables[PREFIX + "anchor_losses"], 2)
        self.assertEqual(restored.variables[PREFIX + "projections_defeated"], 0)


if __name__ == "__main__":
    unittest.main()
