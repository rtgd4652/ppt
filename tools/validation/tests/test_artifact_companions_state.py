"""回放正式三人脚本的付费、月度推进与不可重置恢复期。

人物、舰队位置和实际交战由小型外部夹具提供，不模拟原版作用域或存档引擎。
未支持的条件、效果直接报错，避免把未执行脚本当作通过。
"""

from copy import deepcopy
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_mod import parse, scalar

ROOT = Path(__file__).resolve().parents[3]


def read_script(relative):
    text = (ROOT / relative).read_text(encoding='utf-8')
    text = re.sub(r'\b(value|amount)\s*>=\s*(\d+)', r'\1_ge = \2', text)
    return parse(text)


EFFECTS = {e.key: e.value for e in read_script(
    'mod/common/scripted_effects/artifact_companions_effects.txt')}
TRIGGERS = {e.key: e.value for e in read_script(
    'mod/common/scripted_triggers/artifact_companions_triggers.txt')}


class Ledger:
    def __init__(self):
        self.flags = set()
        self.variables = {}
        self.resources = {'energy': 10000, 'consumer_goods': 10000, 'alloys': 10000}
        self.objects = {
            name: {'flags': set(), 'modifiers': set(), 'combat': True, 'bombarded': False}
            for name in ('ac_seth_target', 'ac_yutong_force', 'ac_yutong_anchor',
                         'ac_rabi_force', 'ac_rabi_threat')
        }
        # 引擎外部事实，不把“外交敌对”替代真实威胁或人物实际任职。
        self.external = dict.fromkeys((
            'ac_player', 'ac_seth_available', 'ac_seth_official',
            'ac_seth_target_accessible', 'ac_seth_direct_present',
            'ac_yutong_available', 'ac_yutong_in_position',
            'ac_yutong_commanded_force', 'ac_rabi_available',
            'ac_rabi_on_duty', 'ac_rabi_threat_valid'), True)

    def condition(self, entries, obj=None, params=None):
        return all(self.term(e, obj, params or {}) for e in entries)

    def term(self, e, obj, params):
        key, value = e.key, e.value
        if key in self.external:
            return self.external[key] == (value == 'yes')
        if key in TRIGGERS:
            return self.condition(TRIGGERS[key], obj, params) == (value == 'yes')
        if key in ('AND', 'limit'):
            return self.condition(value, obj, params)
        if key == 'OR':
            return any(self.term(x, obj, params) for x in value)
        if key in ('NOT', 'NOR'):
            return not any(self.term(x, obj, params) for x in value)
        if key == 'always':
            return params.get(value, value) == 'yes'
        if key == 'has_country_flag':
            return value in self.flags
        if key == 'check_variable':
            return self.variables.get(scalar(value, 'which'), 0) >= float(scalar(value, 'value_ge'))
        if key == 'has_resource':
            return self.resources.get(scalar(value, 'type'), 0) >= float(scalar(value, 'amount_ge'))
        if key.startswith('event_target:'):
            return self.condition(value, self.objects[key[13:].split('@')[0]], params)
        if key == 'exists' and value.startswith('event_target:'):
            return value[13:].split('@')[0] in self.objects
        if key == 'is_in_combat':
            return obj['combat'] == (value == 'yes')
        if key == 'has_orbital_bombardment':
            return obj['bombarded'] == (value == 'yes')
        if key == 'root':
            return self.condition(value, None, params)
        if key == 'any_owned_fleet':
            return self.condition(value, self.objects['ac_yutong_force'], params)
        raise AssertionError(('unsupported condition', key, value))

    def effect(self, name, params=None):
        self.execute(EFFECTS[name], params=params or {})

    def execute(self, entries, obj=None, params=None):
        params = params or {}
        matched = None
        for e in entries:
            key, value = e.key, e.value
            if key in ('if', 'else_if', 'else'):
                if key == 'if':
                    matched = False
                if not matched and (key == 'else' or self.condition(
                        next(x.value for x in value if x.key == 'limit'), obj, params)):
                    self.execute([x for x in value if x.key != 'limit'], obj, params)
                    matched = True
            elif key in EFFECTS:
                self.execute(EFFECTS[key], obj, params)
            elif key in ('set_country_flag', 'remove_country_flag'):
                (self.flags.add if key == 'set_country_flag' else self.flags.discard)(value)
            elif key == 'set_timed_country_flag':
                self.flags.add(scalar(value, 'flag'))  # 测试不模拟时间到期。
            elif key in ('set_variable', 'change_variable'):
                which, number = scalar(value, 'which'), float(scalar(value, 'value'))
                self.variables[which] = number if key == 'set_variable' else self.variables.get(which, 0) + number
            elif key == 'add_resource':
                for resource in value:
                    self.resources[resource.key] = self.resources.get(resource.key, 0) + float(resource.value)
            elif key.startswith('event_target:'):
                target = value if isinstance(value, str) else key[13:].split('@')[0]
                self.execute(value, self.objects[target], params)
            elif key in ('remove_planet_flag', 'remove_fleet_flag', 'remove_star_flag'):
                obj['flags'].discard(value)
            elif key in ('set_fleet_flag', 'set_star_flag'):
                obj['flags'].add(value)
            elif key == 'add_modifier':
                obj['modifiers'].add(scalar(value, 'modifier'))
            elif key == 'remove_modifier':
                obj['modifiers'].discard(value)
            elif key in ('clear_global_event_target', 'save_global_event_target_as', 'log'):
                pass  # 对象存在性和持久引用由夹具提供，不冒称验证引擎引用。
            elif key == 'random_owned_fleet':
                body = [x for x in value if x.key != 'limit']
                limit = next(x.value for x in value if x.key == 'limit')
                target = self.objects['ac_yutong_force']
                if self.condition(limit, target, params):
                    self.execute(body, target, params)
            elif key == 'solar_system':
                self.execute(value, self.objects['ac_yutong_anchor'], params)
            else:
                raise AssertionError(('unsupported effect', key, value))


class CompanionStateTests(unittest.TestCase):
    def test_seth_repeat_payment_pause_and_once_only_fulfilment(self):
        ledger = Ledger()
        ledger.flags.add('ac_seth_ready')
        ledger.effect('ac_seth_start_public')
        after_payment = deepcopy(ledger.resources)
        ledger.effect('ac_seth_start_public')
        self.assertEqual(ledger.resources, after_payment)
        ledger.external['ac_seth_official'] = False
        ledger.effect('ac_seth_monthly')
        self.assertEqual(ledger.variables['ac_seth_progress'], 0)
        ledger.external['ac_seth_official'] = True
        ledger.objects['ac_seth_target']['bombarded'] = True
        ledger.effect('ac_seth_monthly')
        self.assertEqual(ledger.variables['ac_seth_progress'], 0)
        self.assertIn('ac_seth_emergency', ledger.flags)
        ledger.objects['ac_seth_target']['bombarded'] = False
        for _ in range(3):
            ledger.effect('ac_seth_monthly')
        ledger.effect('ac_seth_monthly')
        self.assertEqual(ledger.variables['ac_seth_completed_count'], 1)
        self.assertIn('ac_seth_cooldown', ledger.flags)

    def test_yutong_old_start_cannot_change_principle(self):
        ledger = Ledger()
        ledger.effect('ac_yutong_start', {'$PRECISION$': 'no'})
        paid = ledger.resources['energy']
        ledger.effect('ac_yutong_start', {'$PRECISION$': 'yes'})
        self.assertEqual(ledger.resources['energy'], paid)
        self.assertNotIn('ac_yutong_precision_order', ledger.flags)

    def test_yutong_consumes_calibration_and_keeps_recovery_after_withdrawal(self):
        ledger = Ledger()
        ledger.flags.update(('ac_yutong_active', 'ac_yutong_stable', 'ac_yutong_contact'))
        ledger.variables['ac_yutong_progress'] = 3
        ledger.effect('ac_yutong_burst')
        self.assertEqual(ledger.variables['ac_yutong_progress'], 0)
        self.assertIn('ac_yutong_recovery', ledger.flags)
        restored = deepcopy(ledger)  # 仅账本复制，游戏存读档另验。
        restored.effect('ac_yutong_close')
        self.assertIn('ac_yutong_recovery', restored.flags)
        self.assertNotIn('ac_yutong_burst', restored.objects['ac_yutong_force']['modifiers'])

    def test_rabi_diplomatic_hostility_does_not_allow_counter_and_recovery_survives(self):
        ledger = Ledger()
        ledger.flags.add('ac_rabi_active')
        ledger.external['ac_rabi_threat_valid'] = False
        ledger.effect('ac_rabi_counter')
        self.assertNotIn('ac_rabi_recovery', ledger.flags)
        ledger.external['ac_rabi_threat_valid'] = True
        ledger.effect('ac_rabi_counter')
        self.assertIn('ac_rabi_recovery', ledger.flags)
        ledger.effect('ac_rabi_close')
        self.assertIn('ac_rabi_recovery', ledger.flags)
        self.assertNotIn('ac_rabi_counter', ledger.objects['ac_rabi_force']['modifiers'])


if __name__ == '__main__':
    unittest.main()
