"""重放正式战争适配脚本，检查重复通知与不同战争之间的状态隔离。

仅提供回调中的国家、战争及参与者事实，不模拟引擎调度、外交或存读档。
未知条件和效果立即失败；真实作用域仍需游戏运行证据。
"""

from copy import deepcopy
import unittest

from test_awp02_state import PREFIX, ROOT, child, scalar
from check_mod import parse


EVENTS = {
    scalar(entry.value, "id"): entry.value
    for entry in parse((ROOT / "mod/events/aemusa_main_story_awp_03_adapter_events.txt")
                       .read_text(encoding="utf-8"))
    if entry.key == "country_event"
}
TRIGGERS = {
    entry.key: entry.value
    for entry in parse((ROOT / "mod/common/scripted_triggers/aemusa_ms_awp_03_adapter_triggers.txt")
                       .read_text(encoding="utf-8"))
}
WAR_FLAG = "aemusa_ms_qualified_fe_war"
STARTED = PREFIX + "history_fallen_empire_war_started"
COMPLETED = PREFIX + "history_fallen_empire_war_completed"


class CallbackFixture:
    def __init__(self):
        self.player = dict(id="0", type="default", ai=False, leader=True,
                           flags={PREFIX + "route_initialized"})
        self.enemy = dict(id="7", type="awakened_fallen_empire", ai=True,
                          leader=True, flags=set())
        self.war = self.make_war("first")
        self.targets = {}
        self.logs = []
        self.scopes = {}

    def make_war(self, name):
        return dict(id=name, proxy=False, flags=set(),
                    attackers=[self.enemy], defenders=[self.player])

    def snapshot(self):
        return deepcopy((self.player, self.war, self.targets, self.logs))

    def condition(self, entries, scope):
        return all(self.term(entry, scope) for entry in entries)

    def term(self, entry, scope):
        key, value = entry.key, entry.value
        if key in TRIGGERS:
            result = self.condition(TRIGGERS[key], scope)
            return result if value == "yes" else not result
        if key in self.scopes:
            return self.condition(value, self.scopes[key])
        if key in {"AND", "OR", "NOT", "NOR"}:
            if key == "NOT" and len(value) != 1:
                raise AssertionError("NOT 必须只包含一个条件")
            if key == "AND":
                return self.condition(value, scope)
            matched = any(self.term(item, scope) for item in value)
            return matched if key == "OR" else not matched
        if key in {"has_country_flag", "has_war_flag"}:
            return value in scope["flags"]
        if key in {"is_ai", "is_war_leader", "is_from_proxy_war"}:
            field = {"is_ai": "ai", "is_war_leader": "leader",
                     "is_from_proxy_war": "proxy"}[key]
            return scope[field] == (value == "yes")
        if key == "is_country_type":
            return scope["type"] == value
        if key == "is_same_value" and value == "root":
            return scope["id"] == self.player["id"]
        if key in {"any_attacker", "any_defender"}:
            side = "attackers" if key == "any_attacker" else "defenders"
            return any(self.condition(value, country) for country in scope[side])
        raise AssertionError(f"未支持的战争条件：{key}")

    def execute(self, entries, scope):
        branch_taken = False
        for entry in entries:
            key, value = entry.key, entry.value
            if key in {"if", "else_if", "else"}:
                if key == "if":
                    branch_taken = False
                if not branch_taken and (key == "else" or self.condition(child(value, "limit"), scope)):
                    self.execute([item for item in value if item.key != "limit"], scope)
                    branch_taken = True
            elif key in self.scopes:
                self.execute(value, self.scopes[key])
            elif key in {"set_country_flag", "set_war_flag"}:
                scope["flags"].add(value)
            elif key == "random_attacker":
                candidates = [country for country in scope["attackers"]
                              if self.condition(child(value, "limit"), country)]
                if len(candidates) != 1:
                    raise AssertionError("本回放只支持唯一攻击领袖")
                self.execute([item for item in value if item.key != "limit"], candidates[0])
            elif key == "save_global_event_target_as":
                self.targets[value.replace("@root", self.player["id"])] = scope["id"]
            elif key == "log":
                self.logs.append(value)
            else:
                raise AssertionError(f"未支持的战争效果：{key}")

    def fire(self, event, war=None):
        # 对照本机 4.5.1 原版 on_action 注释提供作用域，不伪造战争结果。
        war = self.war if war is None else war
        self.scopes = {"root": self.player, "from": war if event == "610" else self.enemy,
                       "fromfrom": war, "fromfromfrom": self.player, "fromfromfromfrom": war}
        body = EVENTS["aemusa_ms." + event]
        if not self.condition(child(body, "trigger"), self.player):
            return False
        self.execute(child(body, "immediate"), self.player)
        return True


class WarAdapterStateTests(unittest.TestCase):
    def test_repeated_qualified_start_is_a_noop(self):
        fixture = CallbackFixture()
        self.assertTrue(fixture.fire("610"))
        self.assertIn(STARTED, fixture.player["flags"])
        self.assertIn(WAR_FLAG, fixture.war["flags"])
        self.assertEqual(fixture.targets, {"aemusa_ms_fe_war_attacker0": "7"})
        before = fixture.snapshot()
        for _ in range(3):
            fixture.fire("610")
            self.assertEqual(fixture.snapshot(), before)

    def test_completed_result_cannot_be_repeated_or_changed(self):
        for event, outcome in (("620", "player_victory"), ("621", "player_defeat"),
                               ("622", "status_quo")):
            with self.subTest(outcome=outcome):
                fixture = CallbackFixture()
                fixture.fire("610")
                self.assertTrue(fixture.fire(event))
                self.assertIn(COMPLETED, fixture.player["flags"])
                self.assertIn(PREFIX + "fe_war_" + outcome, fixture.player["flags"])
                before = fixture.snapshot()
                for repeated in (event, "610", "620", "621", "622"):
                    fixture.fire(repeated)
                    self.assertEqual(fixture.snapshot(), before)

    def test_unmarked_war_cannot_supply_any_result(self):
        fixture = CallbackFixture()
        fixture.fire("610")
        other_war = fixture.make_war("other")
        before = fixture.snapshot()
        for event in ("620", "621", "622"):
            self.assertFalse(fixture.fire(event, other_war))
            self.assertEqual(fixture.snapshot(), before)
        self.assertEqual(other_war["flags"], set())

    def test_second_war_does_not_replace_original_qualification(self):
        fixture = CallbackFixture()
        fixture.fire("610")
        other_war = fixture.make_war("other")
        fixture.fire("610", other_war)
        self.assertEqual(other_war["flags"], set())
        self.assertIn(PREFIX + "fe_war_blocked_defense_recorded", fixture.player["flags"])
        self.assertEqual(fixture.targets, {"aemusa_ms_fe_war_attacker0": "7"})

    def test_other_human_ally_still_records_participation_in_marked_war(self):
        fixture = CallbackFixture()
        fixture.player["leader"] = False
        fixture.war["defenders"].append(dict(id="2", type="default", ai=False,
                                               leader=True, flags={STARTED}))
        fixture.war["flags"].add(WAR_FLAG)
        self.assertTrue(fixture.fire("610"))
        self.assertNotIn(STARTED, fixture.player["flags"])
        self.assertIn(PREFIX + "fe_war_ally_defense_recorded", fixture.player["flags"])
        self.assertEqual(fixture.targets, {})

    def test_marked_ally_war_is_not_mistaken_for_players_own_war(self):
        fixture = CallbackFixture()
        fixture.fire("610")
        other_war = fixture.make_war("ally_war")
        fixture.player["leader"] = False
        other_war["defenders"].append(dict(id="2", type="default", ai=False,
                                          leader=True, flags={STARTED}))
        other_war["flags"].add(WAR_FLAG)
        self.assertTrue(fixture.fire("610", other_war))
        self.assertIn(PREFIX + "fe_war_ally_defense_recorded", fixture.player["flags"])
        self.assertNotIn(PREFIX + "fe_war_blocked_defense_recorded", fixture.player["flags"])
        self.assertEqual(fixture.targets, {"aemusa_ms_fe_war_attacker0": "7"})

    def test_proxy_war_cannot_qualify(self):
        fixture = CallbackFixture()
        fixture.war["proxy"] = True
        fixture.fire("610")
        self.assertNotIn(STARTED, fixture.player["flags"])
        self.assertEqual(fixture.war["flags"], set())


if __name__ == "__main__":
    unittest.main()
