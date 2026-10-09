"""执行首都工坊正式脚本的扣费、暂停和一次性结算检查。

原生对象、月份经过与科研选项均为外部夹具；复制账本不是游戏读档证据。
未知语句报错，不把这里的算术结果当作引擎乘区或UI验收。
"""
from copy import deepcopy
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_mod import parse, scalar

ROOT = Path(__file__).resolve().parents[3]


def load(path):
    text = (ROOT / path).read_text(encoding='utf-8')
    text = re.sub(r'\b(value|amount|has_base_skill)\s*>=\s*([\w.]+)', r'\1_ge = \2', text)
    return {entry.key: entry.value for entry in parse(text)}


EFFECTS = load('mod/common/scripted_effects/artifact_engineering_effects.txt')
TRIGGERS = load('mod/common/scripted_triggers/artifact_engineering_triggers.txt')
PERSONAL = load('mod/common/scripted_triggers/artifact_restoration_triggers.txt')
for key in ('ar_an_idle', 'ar_li_idle', 'ar_an_available', 'ar_li_available',
            'ar_an_official', 'ar_li_official', 'ar_li_scientist'):
    TRIGGERS[key] = PERSONAL[key]


class Ledger:
    def __init__(self):
        self.flags = set()
        self.variables = {'ar_an_completed_count': 1, 'ar_li_completed_count': 1}
        self.resources = dict.fromkeys(('energy', 'minerals', 'alloys', 'unity'), 10000)
        self.techs = {'tech_artifact_tarot_economy', 'tech_artifact_central_court_protocols',
                      'tech_artifact_relic_fabrication'}
        self.options, self.events = [], []
        self.capital = {'owned': True, 'controlled': True, 'colony': True,
                        'bombarded': False, 'flags': set(), 'modifiers': []}
        self.targets = {}
        self.leaders = {
            'an': {'flags': {'ar_an_unique'}, 'class': 'official', 'level': 7, 'xp': 0},
            'li': {'flags': {'ar_li_unique'}, 'class': 'scientist', 'level': 7, 'xp': 0},
        }

    def number(self, value):
        try:
            return float(value)
        except ValueError:
            return self.variables.get(value, 0)

    def condition(self, entries, obj=None):
        return all(self.term(entry, obj) for entry in entries)

    def term(self, entry, obj=None):
        k, v = entry.key, entry.value
        if k in TRIGGERS:
            return self.condition(TRIGGERS[k], obj) == (v == 'yes')
        if k in ('AND', 'limit', 'owner_main_species'):
            return self.condition(v, obj)
        if k == 'OR':
            return any(self.term(e, obj) for e in v)
        if k in ('NOT', 'NOR'):
            return not any(self.term(e, obj) for e in v)
        if k == 'ar_player':
            return v == 'yes'  # 外部提供玩家与起源事实。
        if k == 'is_species_class':
            return v == 'ARTIFACT_USER'
        if k == 'has_country_flag':
            return v in self.flags
        if k in ('has_technology', 'has_tech_option'):
            return v in (self.techs if k == 'has_technology' else self.options)
        if k == 'has_resource':
            return self.resources[scalar(v, 'type')] >= self.number(scalar(v, 'amount_ge'))
        if k == 'check_variable':
            return self.variables.get(scalar(v, 'which'), 0) >= self.number(scalar(v, 'value_ge'))
        if k == 'is_variable_set':
            return v in self.variables
        if k == 'exists':
            return self.capital is not None if v == 'capital_scope' else v[13:].split('@')[0] in self.targets
        if k == 'capital_scope':
            return self.capital is not None and self.condition(v, self.capital)
        if k.startswith('event_target:'):
            target = self.targets.get(k[13:].split('@')[0])
            return target is not None and self.condition(v, target)
        if k == 'any_owned_leader':
            return any(self.condition(v, leader) for leader in self.leaders.values())
        if k in ('has_planet_flag', 'has_leader_flag'):
            return v in obj['flags']
        if k == 'leader_class':
            return obj['class'] == v
        if k == 'has_base_skill_ge':
            return obj['level'] >= self.number(v)
        if k == 'is_owned_by':
            return obj['owned']
        if k == 'is_controlled_by':
            return obj['controlled']
        if k in ('is_colony', 'has_orbital_bombardment'):
            return obj['colony' if k == 'is_colony' else 'bombarded'] == (v == 'yes')
        raise AssertionError(('unknown condition', k, v))

    def effect(self, name):
        self.execute(EFFECTS[name])

    def execute(self, entries, obj=None):
        matched = None
        for entry in entries:
            k, v = entry.key, entry.value
            if k in ('if', 'else_if', 'else'):
                if k == 'if':
                    matched = False
                if not matched and (k == 'else' or self.condition(next(e.value for e in v if e.key == 'limit'), obj)):
                    self.execute([e for e in v if e.key != 'limit'], obj)
                    matched = True
            elif k in EFFECTS:
                self.execute(EFFECTS[k], obj)
            elif k in ('set_country_flag', 'remove_country_flag'):
                (self.flags.add if k == 'set_country_flag' else self.flags.discard)(v)
            elif k == 'set_timed_country_flag':
                self.flags.add(scalar(v, 'flag'))
            elif k in ('set_variable', 'change_variable', 'multiply_variable'):
                key, value = scalar(v, 'which'), self.number(scalar(v, 'value'))
                if k == 'set_variable':
                    self.variables[key] = value
                elif k == 'change_variable':
                    self.variables[key] = self.variables.get(key, 0) + value
                else:
                    self.variables[key] = self.variables.get(key, 0) * value
            elif k == 'add_resource':
                for resource in v:
                    self.resources[resource.key] += self.number(resource.value)
            elif k == 'capital_scope':
                self.execute(v, self.capital)
            elif k.startswith('event_target:'):
                self.execute(v, self.targets[k[13:].split('@')[0]])
            elif k == 'save_global_event_target_as':
                self.targets[v.split('@')[0]] = obj
            elif k == 'clear_global_event_target':
                self.targets.pop(v.split('@')[0], None)
            elif k in ('set_planet_flag', 'remove_planet_flag'):
                (obj['flags'].add if k == 'set_planet_flag' else obj['flags'].discard)(v)
            elif k == 'every_owned_leader':
                conditions = next(e.value for e in v if e.key == 'limit')
                for leader in self.leaders.values():
                    if self.condition(conditions, leader):
                        self.execute([e for e in v if e.key != 'limit'], leader)
            elif k == 'add_experience':
                obj['xp'] += self.number(v)
            elif k == 'add_modifier':
                obj['modifiers'].append(scalar(v, 'modifier'))
            elif k == 'add_research_option':
                self.options.append(v)
            elif k == 'country_event':
                self.events.append(scalar(v, 'id'))
            elif k in ('save_event_target_as', 'log'):
                pass  # 本地UI绑定和日志留给真实游戏，不伪造验收。
            else:
                raise AssertionError(('unknown effect', k, v))

    def month(self):
        self.flags.discard('ae_eng_month_checked')  # 夹具明确提供28日经过，不模拟游戏日历。
        self.effect('artifact_engineering_monthly')

    def finish(self):
        for _ in range(8):
            if 'ae_eng_active' not in self.flags:
                break
            self.month()
        assert 'ae_eng_completed' in self.flags


class EngineeringStateTests(unittest.TestCase):
    def test_missing_resources_record_or_free_person_cannot_start(self):
        for fault in ('resources', 'record', 'busy'):
            with self.subTest(fault=fault):
                x = Ledger()
                if fault == 'resources':
                    x.resources['energy'] = 499
                elif fault == 'record':
                    x.variables['ar_li_completed_count'] = 0
                else:
                    x.flags.add('ar_li_cooldown')
                paid = deepcopy(x.resources)
                x.effect('artifact_engineering_start_li_an')
                self.assertEqual(x.resources, paid)
                self.assertNotIn('ae_eng_active', x.flags)
                self.assertNotIn('ae_eng_an_committed', x.flags)

    def test_stale_start_cannot_pay_twice_or_change_team(self):
        x = Ledger()
        x.effect('artifact_engineering_start_li_an')
        paid = deepcopy(x.resources)
        self.assertEqual(paid, {'energy': 9500, 'minerals': 9000, 'alloys': 9700, 'unity': 9800})
        x.effect('artifact_engineering_start_an')
        x.effect('artifact_engineering_start_li_an')
        self.assertEqual(x.resources, paid)
        self.assertNotIn('ae_eng_lead_an', x.flags)
        self.assertFalse(x.condition(TRIGGERS['ar_an_idle']))
        self.assertFalse(x.condition(TRIGGERS['ar_li_idle']))

    def test_actual_script_multiplies_and_repeated_pulse_does_not_advance(self):
        x = Ledger()
        x.leaders['li']['level'], x.leaders['an']['level'] = 21, 11
        x.techs.add('tech_artifact_resonance_manufacturing')
        x.effect('artifact_engineering_start_li_an')
        self.assertEqual(x.variables['ae_eng_monthly_work'], 45)
        x.month()
        x.effect('artifact_engineering_monthly')
        self.assertEqual(x.variables['ae_eng_progress'], 45)
        restored = deepcopy(x)  # 仅检查已有账本不被重新初始化，不是.sav读档。
        restored.effect('artifact_engineering_refresh')
        self.assertEqual(restored.variables['ae_eng_progress'], 45)
        restored.month()
        self.assertEqual(restored.variables['ae_eng_progress'], 90)

    def test_occupation_and_class_switch_pause_then_resume(self):
        x = Ledger()
        x.effect('artifact_engineering_start_li_an')
        x.month()
        progress, paid = x.variables['ae_eng_progress'], deepcopy(x.resources)
        x.capital['controlled'] = False
        x.month()
        self.assertEqual(x.variables['ae_eng_progress'], progress)
        x.capital['controlled'] = True
        x.leaders['li']['class'] = 'commander'
        x.month()
        self.assertEqual(x.variables['ae_eng_progress'], progress)
        self.assertIn('ae_eng_li_committed', x.flags)
        x.leaders['li']['class'] = 'scientist'
        x.month()
        self.assertEqual(x.variables['ae_eng_progress'], progress * 2)
        self.assertEqual(x.resources, paid)

    def test_lost_original_capital_stops_without_retarget_or_refund(self):
        x = Ledger()
        x.effect('artifact_engineering_start_an')
        x.month()
        original, paid = x.capital, deepcopy(x.resources)
        original['owned'] = False
        x.capital = deepcopy(original)
        x.capital['owned'] = True
        x.month()
        x.effect('artifact_engineering_monthly')
        self.assertEqual(x.resources, paid)
        self.assertEqual(x.variables['ae_eng_failed_count'], 1)
        self.assertEqual(x.variables['ae_eng_last_progress'], 20)
        self.assertNotIn('ae_eng_target', x.targets)
        self.assertNotIn('ae_eng_an_committed', x.flags)
        self.assertNotIn('ae_eng_completed', x.flags)
        self.assertEqual(x.events.count('artifact_engineering.30'), 1)

    def test_completion_and_stale_claims_cannot_repeat_rewards(self):
        x = Ledger()
        x.effect('artifact_engineering_start_li_an')
        x.finish()
        x.effect('artifact_engineering_complete')
        self.assertEqual(x.capital['modifiers'], ['artifact_engineering_calibrated_workshop'])
        self.assertEqual([p['xp'] for p in x.leaders.values()], [200, 200])
        x.effect('artifact_engineering_claim_energy')
        x.effect('artifact_engineering_claim_trade')
        x.effect('artifact_engineering_claim_energy')
        self.assertEqual(x.options, ['tech_artifact_phase_energy'])
        self.assertFalse(x.condition(TRIGGERS['artifact_engineering_idle']))

    def test_single_person_route_does_not_require_or_reward_partner(self):
        for person, absent in (('an', 'li'), ('li', 'an')):
            with self.subTest(person=person):
                x = Ledger()
                del x.leaders[absent]
                x.effect('artifact_engineering_start_' + person)
                self.assertNotIn('ae_eng_' + absent + '_committed', x.flags)
                self.assertEqual(x.variables['ae_eng_monthly_work'], 20)
                x.finish()
                self.assertEqual(x.leaders[person]['xp'], 200)

    def test_research_choice_requires_prerequisite_and_never_grants_technology(self):
        x = Ledger()
        x.techs.discard('tech_artifact_relic_fabrication')
        x.effect('artifact_engineering_start_li')
        x.finish()
        before = set(x.techs)
        x.effect('artifact_engineering_claim_manufacturing')
        self.assertIn('ae_eng_ready', x.flags)
        self.assertEqual(x.options, [])
        x.effect('artifact_engineering_claim_trade')
        self.assertEqual(x.options, ['tech_artifact_crossing_trade'])
        self.assertEqual(x.techs, before)


if __name__ == '__main__':
    unittest.main()
