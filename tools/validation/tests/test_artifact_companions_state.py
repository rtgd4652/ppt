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
    text = re.sub(r'\b(value|amount|has_base_skill)\s*>=\s*([\w.]+)', r'\1_ge = \2', text)
    return parse(text)


EFFECTS = {e.key: e.value for e in read_script(
    'mod/common/scripted_effects/artifact_companions_effects.txt')}
EFFECTS.update({e.key: e.value for e in read_script(
    'mod/common/scripted_effects/artifact_growth_effects.txt')})
TRIGGERS = {e.key: e.value for e in read_script(
    'mod/common/scripted_triggers/artifact_companions_triggers.txt')}


class Ledger:
    def __init__(self):
        self.flags = set()
        self.variables = {}
        self.effects, self.triggers = EFFECTS, TRIGGERS
        self.fleet_fixture = 'ac_yutong_force'
        self.timed_flags, self.delayed_events = {}, []
        self.leaders = {name: {'level': 7, 'flags': {f'{name}_unique_leader'}}
                        for name in ('seth', 'yutong', 'rabi')}
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

    def number(self, value):
        try:
            return float(value)
        except ValueError:
            return self.variables.get(value, 0)

    def condition(self, entries, obj=None, params=None):
        return all(self.term(e, obj, params or {}) for e in entries)

    def term(self, e, obj, params):
        key, value = e.key, e.value
        if key in self.external:
            return self.external[key] == (value == 'yes')
        if key in self.triggers:
            return self.condition(self.triggers[key], obj, params) == (value == 'yes')
        if key in ('AND', 'limit'):
            return self.condition(value, obj, params)
        if key == 'OR':
            return any(self.term(x, obj, params) for x in value)
        if key in ('NOT', 'NOR'):
            return not any(self.term(x, obj, params) for x in value)
        if key == 'always':
            return params.get(value, value) == 'yes'
        if key == 'has_country_flag':
            return value in (obj['flags'] if obj and obj.get('kind') == 'country' else self.flags)
        if key == 'any_owned_leader':
            return any(self.condition(value, actor, params) for actor in self.leaders.values())
        if key == 'has_leader_flag':
            return value in obj['flags']
        if key == 'has_base_skill_ge':
            return obj['level'] >= self.number(value)
        if key == 'check_variable':
            return self.variables.get(scalar(value, 'which'), 0) >= self.number(scalar(value, 'value_ge'))
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
        self.execute(self.effects[name], params=params or {})

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
            elif key in self.effects:
                self.execute(self.effects[key], obj, params)
            elif key in ('set_country_flag', 'remove_country_flag'):
                flags = obj['flags'] if obj and obj.get('kind') == 'country' else self.flags
                (flags.add if key == 'set_country_flag' else flags.discard)(value)
            elif key == 'set_timed_country_flag':
                self.flags.add(scalar(value, 'flag'))  # 测试不模拟时间到期。
                self.timed_flags[scalar(value, 'flag')] = int(scalar(value, 'days'))
            elif key in ('set_variable', 'change_variable'):
                which, number = scalar(value, 'which'), self.number(scalar(value, 'value'))
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
                obj.setdefault('modifier_days', {})[scalar(value, 'modifier')] = int(scalar(value, 'days'))
            elif key == 'remove_modifier':
                obj['modifiers'].discard(value)
            elif key in ('clear_global_event_target', 'save_global_event_target_as', 'log'):
                pass  # 对象存在性和持久引用由夹具提供，不冒称验证引擎引用。
            elif key == 'random_owned_fleet':
                body = [x for x in value if x.key != 'limit']
                limit = next(x.value for x in value if x.key == 'limit')
                target = self.objects[self.fleet_fixture]
                if self.condition(limit, target, params):
                    self.execute(body, target, params)
            elif key == 'solar_system':
                self.execute(value, self.objects['ac_yutong_anchor'], params)
            else:
                self.execute_extra(key, value, obj, params)

    def execute_extra(self, key, value, obj, params):
        raise AssertionError(('unsupported effect', key, value))


class CompanionStateTests(unittest.TestCase):
    def test_seth_growth_paid_work_still_requires_duty_and_settles_once(self):
        for level, work, months, duration in ((7, 1, 3, 360), (11, 1.25, 3, 450), (21, 1.5, 2, 540)):
            with self.subTest(level=level):
                x = Ledger()
                x.leaders['seth']['level'] = level
                x.flags.add('ac_seth_ready')
                x.effect('ac_seth_start_public')
                paid = deepcopy(x.resources)
                x.external['ac_seth_official'] = False
                x.effect('ac_seth_monthly')
                self.assertEqual(0, x.variables['ac_seth_progress'])
                x.external['ac_seth_official'] = True
                x.effect('ac_seth_monthly')
                self.assertEqual(work, x.variables['ac_seth_progress'])
                for _ in range(months - 1):
                    x.effect('ac_seth_monthly')
                x.effect('ac_seth_monthly')
                self.assertEqual(1, x.variables['ac_seth_completed_count'])
                self.assertEqual(duration, x.objects['ac_seth_target']['modifier_days']['ac_seth_fulfilled'])
                self.assertEqual(paid, x.resources)

    def test_yutong_and_rabi_growth_keeps_contact_confirmation_and_recovery(self):
        for role, action, level, days in (
                (r, a, l, d) for r, a in (('yutong', 'burst'), ('rabi', 'counter'))
                for l, d in ((7, 30), (11, 40), (21, 50))):
            with self.subTest(role=role, level=level):
                x = Ledger()
                x.leaders[role]['level'] = level
                x.flags.add(f'ac_{role}_active')
                if role == 'yutong':
                    x.flags.add('ac_yutong_stable')
                    x.variables['ac_yutong_progress'] = 3
                    x.effect('ac_yutong_burst')
                    self.assertNotIn('ac_yutong_recovery', x.flags)
                    x.flags.add('ac_yutong_contact')
                else:
                    x.external['ac_rabi_threat_valid'] = False
                    x.effect('ac_rabi_counter')
                    self.assertNotIn('ac_rabi_recovery', x.flags)
                    x.external['ac_rabi_threat_valid'] = True
                x.effect(f'ac_{role}_{action}')
                self.assertEqual(days, x.objects[f'ac_{role}_force']['modifier_days'][f'ac_{role}_{action}'])
                self.assertEqual(180, x.timed_flags[f'ac_{role}_recovery'])
                x.effect(f'ac_{role}_close')
                self.assertIn(f'ac_{role}_recovery', x.flags)

    def test_yutong_calibration_growth_cannot_work_in_combat(self):
        x = Ledger()
        x.leaders['yutong']['level'] = 21
        x.flags.add('ac_yutong_active')
        x.effect('ac_yutong_monthly')
        self.assertEqual(0, x.variables.get('ac_yutong_progress', 0))
        x.objects['ac_yutong_force']['combat'] = False
        x.effect('ac_yutong_monthly')
        self.assertEqual(1.5, x.variables['ac_yutong_progress'])
        x.effect('ac_yutong_monthly')
        self.assertIn('ac_yutong_stable', x.flags)

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
