"""直接执行四人正式账本的严重失败检查。

领袖、控制权、真实交战和损伤为外部夹具，不模拟游戏引擎或真实读档。
只解释实际使用的语句，未知项报错；测试通过不等于游戏运行通过。
"""
from copy import deepcopy
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_mod import parse, scalar

ROOT = Path(__file__).resolve().parents[3]


def load(relative):
    text = (ROOT / relative).read_text(encoding='utf-8')
    # 静态解析器不保存比较运算符；仅在测试输入中显式保留运算类型。
    text = re.sub(r'\b(value|amount)\s*>=\s*([\w.]+)', r'\1_ge = \2', text)
    text = re.sub(r'\bplanet_devastation\s*>\s*(\d+)', r'planet_devastation_gt = \1', text)
    return {e.key: e.value for e in parse(text)}


EFFECTS = load('mod/common/scripted_effects/artifact_restoration_effects.txt')
TRIGGERS = load('mod/common/scripted_triggers/artifact_restoration_triggers.txt')


class Ledger:
    def __init__(self):
        self.flags, self.variables = set(), {}
        self.resources = dict.fromkeys(('energy', 'unity', 'minerals', 'alloys', 'consumer_goods'), 10000)
        self.external = {'ar_player': True}
        self.objects = {}
        for p in ('an', 'greysa', 'wenzi', 'li'):
            self.external[f'ar_{p}_available'] = True
            self.external[f'ar_{p}_work_ready'] = True
            self.external[f'ar_{p}_target_valid'] = True
            self.external[f'ar_{p}_commanded_force'] = True
            for cls in ('official', 'scientist', 'commander'):
                self.external[f'ar_{p}_{cls}'] = True
            self.objects[f'ar_{p}_target'] = {'flags': {f'ar_{p}_target@root'}, 'modifiers': [], 'combat': False, 'bombarded': False, 'controlled': True, 'damaged': True, 'mia': False, 'devastation': 20}
            self.objects[f'ar_{p}'] = {'xp': 0}

    def number(self, value):
        try:
            return float(value)
        except ValueError:
            return self.variables.get(value, 0)

    def condition(self, entries, obj=None):
        return all(self.term(e, obj) for e in entries)

    def term(self, entry, obj=None):
        k, v = entry.key, entry.value
        if k in self.external:
            return self.external[k] == (v == 'yes')
        if k in TRIGGERS:
            return self.condition(TRIGGERS[k], obj) == (v == 'yes')
        if k in ('AND', 'limit'):
            return self.condition(v, obj)
        if k == 'OR':
            return any(self.term(e, obj) for e in v)
        if k in ('NOT', 'NOR'):
            return not any(self.term(e, obj) for e in v)
        if k == 'has_country_flag':
            return v in self.flags
        if k == 'has_resource':
            return self.resources[scalar(v, 'type')] >= self.number(scalar(v, 'amount_ge'))
        if k == 'check_variable':
            return self.variables.get(scalar(v, 'which'), 0) >= self.number(scalar(v, 'value_ge'))
        if k.startswith('event_target:'):
            target = self.objects.get(k[13:].split('@')[0])
            return target is not None and self.condition(v, target)
        if k == 'exists':
            return v == 'capital_scope' or v[13:].split('@')[0] in self.objects
        if k in ('is_colony', 'is_owned_by', 'can_go_mia'):
            return True  # 外部对象事实，非原版语义证明。
        if k == 'is_controlled_by':
            return obj['controlled']
        if k == 'has_orbital_bombardment':
            return obj['bombarded'] == (v == 'yes')
        if k == 'is_in_combat':
            return obj['combat'] == (v == 'yes')
        if k == 'is_damaged':
            return obj['damaged'] == (v == 'yes')
        if k == 'planet_devastation_gt':
            return obj['devastation'] > self.number(v)
        if k == 'any_owned_ship':
            return self.condition(v, obj)
        if k in ('capital_scope', 'any_owned_planet'):
            return self.condition(v, self.objects['ar_li_target'])
        raise AssertionError(('unknown condition', k, v))

    def effect(self, name):
        self.execute(EFFECTS[name])

    def execute(self, entries, obj=None):
        matched = None
        for e in entries:
            k, v = e.key, e.value
            if k in ('if', 'else_if', 'else'):
                if k == 'if':
                    matched = False
                if not matched and (k == 'else' or self.condition(next(x.value for x in v if x.key == 'limit'), obj)):
                    self.execute([x for x in v if x.key != 'limit'], obj)
                    matched = True
            elif k in EFFECTS:
                self.execute(EFFECTS[k], obj)
            elif k in ('set_country_flag', 'remove_country_flag'):
                (self.flags.add if k == 'set_country_flag' else self.flags.discard)(v)
            elif k == 'set_timed_country_flag':
                self.flags.add(scalar(v, 'flag'))  # 到期由测试明确提供，不冒充游戏时间。
            elif k in ('set_variable', 'change_variable'):
                name, number = scalar(v, 'which'), self.number(scalar(v, 'value'))
                self.variables[name] = number if k == 'set_variable' else self.variables.get(name, 0) + number
            elif k == 'add_resource':
                for x in v:
                    self.resources[x.key] += float(x.value)
            elif k.startswith('event_target:'):
                self.execute(v, self.objects[k[13:].split('@')[0]])
            elif k in ('remove_planet_flag', 'remove_fleet_flag'):
                obj['flags'].discard(v)
            elif k == 'set_planet_flag':
                obj['flags'].add(v)
            elif k == 'add_modifier':
                obj['modifiers'].append(scalar(v, 'modifier'))
            elif k == 'add_experience':
                obj['xp'] += float(v)
            elif k == 'set_mia':
                obj['mia'] = True
            elif k == 'set_mia_return_delay':
                obj['return_days'] = int(v)
            elif k == 'clear_global_event_target':
                self.objects.pop(v.split('@')[0], None)
            elif k == 'save_global_event_target_as':
                self.objects[v.split('@')[0]] = obj
            elif k == 'capital_scope':
                self.execute(v, self.objects['ar_li_target'])
            elif k == 'log':
                pass
            else:
                raise AssertionError(('unknown effect', k, v))


class RestorationStateTests(unittest.TestCase):
    def test_an_requires_real_combat_and_consumes_only_one_record(self):
        x = Ledger()
        x.flags.update(('ar_an_active', 'ar_an_fleet'))
        for _ in range(3):
            x.effect('ar_an_monthly')
        self.assertEqual(x.variables.get('ar_an_progress', 0), 0)
        x.flags.add('ar_an_combat_observed')
        x.external['ar_an_work_ready'] = False  # 职业／任职不符时原记录暂停。
        x.effect('ar_an_monthly')
        self.assertEqual(x.variables.get('ar_an_progress', 0), 0)
        x.external['ar_an_work_ready'] = True
        for _ in range(3):
            x.effect('ar_an_monthly')
        self.assertEqual(x.variables['ar_an_completed_count'], 1)
        self.assertEqual(x.objects['ar_an']['xp'], 200)
        force = x.objects['ar_an_target']
        force['combat'] = True
        x.effect('ar_an_escape')
        self.assertTrue(force['mia'])
        self.assertEqual(force['return_days'], 60)
        self.assertNotIn('ar_an_record_ready', x.flags)
        x.effect('ar_an_escape')
        x.effect('ar_an_withdraw')
        self.assertIn('ar_an_escape_recovery', x.flags)

    def test_greysa_emergency_is_not_analysis_and_archive_pays_once(self):
        x = Ledger()
        x.flags.update(('ar_greysa_active', 'ar_greysa_planet'))
        x.objects['ar_greysa_target']['bombarded'] = True
        x.external['ar_greysa_work_ready'] = False
        x.effect('ar_greysa_emergency')
        paid = deepcopy(x.resources)
        x.effect('ar_greysa_emergency')
        x.effect('ar_greysa_monthly')
        self.assertEqual(x.resources, paid)
        self.assertEqual(x.variables.get('ar_greysa_progress', 0), 0)
        x.objects['ar_greysa_target']['bombarded'] = False
        x.external['ar_greysa_work_ready'] = True
        for _ in range(3):
            x.effect('ar_greysa_monthly')
        x.effect('ar_greysa_finish_care')
        final = deepcopy(x.resources)
        x.effect('ar_greysa_finish_care')
        self.assertEqual(x.resources, final)
        self.assertEqual(x.variables['ar_greysa_completed_count'], 1)
        self.assertEqual(x.objects['ar_greysa_archive']['modifiers'].count('ar_greysa_stable_care'), 1)
        self.assertIn('ar_greysa_emergency_recent', x.flags)

    def test_wenzi_repeat_colour_requires_correction_and_no_repeated_reward(self):
        x = Ledger()
        x.flags.update(('ar_wenzi_active', 'ar_wenzi_planet', 'ar_wenzi_objective_agreed', 'ar_wenzi_boundary_agreed'))
        for _ in range(3):
            x.flags.discard('ar_wenzi_turn_recent')  # 夹具表示28日已过。
            x.effect('ar_wenzi_play_black')
        self.assertEqual(x.variables['ar_wenzi_imbalance'], 2)
        paid = deepcopy(x.resources)
        x.flags.discard('ar_wenzi_turn_recent')
        x.effect('ar_wenzi_play_black')
        x.effect('ar_wenzi_finish')
        self.assertEqual(x.resources, paid)
        self.assertNotIn('ar_wenzi_completed', x.flags)
        x.effect('ar_wenzi_play_white')
        self.assertEqual(x.variables['ar_wenzi_imbalance'], 1)
        target = x.objects['ar_wenzi_target']
        x.effect('ar_wenzi_finish')
        x.effect('ar_wenzi_finish')
        self.assertEqual(x.variables['ar_wenzi_completed_count'], 1)
        self.assertEqual(target['modifiers'].count('ar_wenzi_balanced_service'), 1)
        self.assertEqual(x.variables['ar_wenzi_progress'], 4)

    def test_li_duplicate_funding_pause_risk_cost_and_single_fulfilment(self):
        x = Ledger()
        x.effect('ar_li_start_planet')
        first = deepcopy(x.resources)
        x.effect('ar_li_start_planet')
        self.assertEqual(x.resources, first)
        x.effect('ar_li_monthly')
        x.effect('ar_li_fund_full')
        funded = deepcopy(x.resources)
        x.effect('ar_li_fund_scaled')
        x.effect('ar_li_fund_full')
        self.assertEqual(x.resources, funded)
        x.external['ar_li_work_ready'] = False
        x.effect('ar_li_monthly')
        self.assertEqual(x.variables['ar_li_progress'], 0)
        x.external['ar_li_work_ready'] = True
        x.effect('ar_li_monthly')
        x.objects['ar_li_target']['bombarded'] = True
        x.effect('ar_li_monthly')
        self.assertIn('ar_li_risk', x.flags)
        self.assertEqual(x.variables['ar_li_progress'], 1)
        x.objects['ar_li_target']['bombarded'] = False
        x.effect('ar_li_monthly')
        self.assertEqual(x.variables['ar_li_progress'], 1)
        x.effect('ar_li_resolve_risk')
        extra = deepcopy(x.resources)
        x.effect('ar_li_resolve_risk')
        self.assertEqual(x.resources, extra)
        target = x.objects['ar_li_target']
        for _ in range(3):
            x.effect('ar_li_monthly')
        self.assertEqual(x.variables['ar_li_completed_count'], 1)
        self.assertEqual(x.variables['ar_li_cost_energy'], 750)
        self.assertEqual(target['modifiers'].count('ar_li_public_engineering'), 1)


if __name__ == '__main__':
    unittest.main()
