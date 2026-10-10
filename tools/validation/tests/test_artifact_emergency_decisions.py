"""读取正式决议检查扣费与有限效期；夹具时间和复制不代表游戏存读档。"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_mod import parse, scalar

ROOT = Path(__file__).resolve().parents[3]
DECISIONS = {e.key: e.value for e in parse((ROOT / 'mod/common/decisions/artifact_emergency_decisions.txt').read_text(encoding='utf-8'))}
MODIFIERS = {e.key: e.value for e in parse((ROOT / 'mod/common/static_modifiers/artifact_emergency_modifiers.txt').read_text(encoding='utf-8'))}
PREPARE = 'decision_artifact_emergency_prepare'
ACTIVATE = 'decision_artifact_emergency_activate'


class Colony:
    """原生国别、控制权、资源与日历作为外部事实输入，未知语句直接失败。"""
    def __init__(self):
        self.controlled = self.command = self.tech = True
        self.bombarded = False
        self.resources = {'energy': 3000, 'consumer_goods': 1500}
        self.modifiers = {}

    def condition(self, entries):
        return all(self.term(e) for e in entries)

    def term(self, e):
        k, v = e.key, e.value
        if k in ('owner', 'owner_main_species', 'custom_tooltip'):
            return self.condition(v)
        if k == 'fail_text':
            return True
        if k == 'NOR':
            return not any(self.term(x) for x in v)
        if k == 'has_modifier':
            return v in self.modifiers
        if k == 'has_technology':
            return self.tech
        if k == 'has_building':
            return self.command
        if k == 'is_controlled_by':
            return self.controlled
        if k == 'has_orbital_bombardment':
            return self.bombarded == (v == 'yes')
        if k in ('is_colony', 'exists'):
            return True  # 外部夹具：已殖民、有拥有者。
        if k == 'is_ai':
            return v == 'no'
        if k == 'is_species_class':
            return v == 'ARTIFACT_USER'
        raise AssertionError(('unknown trigger', k))

    def select(self, name):
        fields = {e.key: e.value for e in DECISIONS[name]}
        costs = {}
        if 'resources' in fields:
            costs = {e.key: int(e.value) for e in next(e.value for e in fields['resources'] if e.key == 'cost')}
        if not self.condition(fields['potential']) or not self.condition(fields['allow']):
            return False
        if any(self.resources[k] < value for k, value in costs.items()):
            return False
        # 决议引擎扣费为外部规则，随后执行本项目正式效果。
        for k, value in costs.items():
            self.resources[k] -= value
        for e in fields['effect']:
            if e.key == 'remove_modifier':
                self.modifiers.pop(e.value, None)
            elif e.key == 'add_modifier':
                self.modifiers[scalar(e.value, 'modifier')] = int(scalar(e.value, 'days'))
            else:
                raise AssertionError(('unknown effect', e.key))
        return True

    def elapsed(self, days):
        # 只提供期限经过，不模拟群星历法或轰炸伤害结算。
        self.modifiers = {k: value if value == -1 else value - days
                          for k, value in self.modifiers.items() if value == -1 or value > days}


class EmergencyDecisionTests(unittest.TestCase):
    def test_bad_frontier_never_spends(self):
        for fault in ('tech', 'command', 'controlled', 'resources', 'bombarded'):
            with self.subTest(fault=fault):
                x = Colony()
                if fault == 'resources':
                    x.resources['consumer_goods'] = 499
                else:
                    setattr(x, fault, fault == 'bombarded')
                before = deepcopy(x.resources)
                self.assertFalse(x.select(PREPARE))
                self.assertEqual(x.resources, before)
                self.assertEqual(x.modifiers, {})

    def test_prepared_record_survives_fixture_restore_without_second_charge(self):
        x = Colony()
        self.assertTrue(x.select(PREPARE))
        paid = dict(x.resources)
        self.assertEqual(paid, {'energy': 2000, 'consumer_goods': 1000})
        restored = deepcopy(x)  # 不是真实.sav读档证明。
        self.assertFalse(restored.select(PREPARE))
        self.assertFalse(restored.select(ACTIVATE))
        self.assertEqual(restored.resources, paid)
        restored.elapsed(600)
        self.assertEqual(restored.modifiers['artifact_emergency_prepared'], -1)

    def test_activation_consumes_once_and_full_rearm_is_required(self):
        x = Colony()
        x.select(PREPARE)
        x.bombarded = True
        self.assertTrue(x.select(ACTIVATE))
        self.assertNotIn('artifact_emergency_prepared', x.modifiers)
        original = deepcopy(x.modifiers)
        self.assertFalse(x.select(ACTIVATE))
        self.assertEqual(x.modifiers, original)
        x.bombarded = False
        x.elapsed(180)
        self.assertNotIn('artifact_emergency_protection', x.modifiers)
        self.assertFalse(x.select(PREPARE))
        x.elapsed(359)
        self.assertFalse(x.select(PREPARE))
        x.elapsed(1)
        self.assertTrue(x.select(PREPARE))
        self.assertEqual(x.resources, {'energy': 1000, 'consumer_goods': 500})

    def test_occupation_cannot_consume_and_existing_aid_is_not_refreshed(self):
        x = Colony()
        x.select(PREPARE)
        x.bombarded = True
        x.controlled = False
        self.assertFalse(x.select(ACTIVATE))
        self.assertIn('artifact_emergency_prepared', x.modifiers)
        x.controlled = True
        x.modifiers['ac_seth_emergency_aid'] = 20
        self.assertTrue(x.select(ACTIVATE))
        self.assertEqual(x.modifiers['ac_seth_emergency_aid'], 20)
        self.assertEqual(float(scalar(MODIFIERS['artifact_emergency_protection'], 'planet_orbital_bombardment_damage')), -0.25)


if __name__ == '__main__':
    unittest.main()
