"""执行R4a正式脚本，检查付费阶段与防护失效边界；不模拟引擎日期、减伤或存读档。"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_foundation_projects as foundation
import test_artifact_civil_supply as supply

load, child, scalar = foundation.load, foundation.child, foundation.scalar
LAB = 'building_artifact_controlled_boundary_lab'
SITE = 'building_artifact_rule_anchor_test_site'
RECORD = 'artifact_public_rule_interface_record'
RESULT = 'artifact_foundation_boundary_result'
WINDOW = 'acs_rule_anchor_window'
RESEARCH = 'tech_artifact_controlled_boundary_experiments'
INTERFACE = 'tech_artifact_stable_rule_interface'
TECHS = load('mod/common/technology/artifact_boundary_engineering_technology.txt')
BUILDINGS = load('mod/common/buildings/artifact_boundary_engineering_buildings.txt')


class World(supply.World):
    """共享已有严格脚本执行器；只增加国家知识旗标，不复写项目算法。"""
    def __init__(self):
        super().__init__()
        for country in self.countries.values():
            country['flags'] = set()
            country['techs'].update(TECHS)
            country['resources']['rare_crystals'] = 1000
        self.planets['P']['buildings'] = {LAB}
        self.planets['Q']['buildings'] = {SITE}

    def term(self, entry, obj, ctx, prev):
        if entry.key == 'has_country_flag':
            assert obj['kind'] == 'country'
            return entry.value in obj['flags']
        return super().term(entry, obj, ctx, prev)

    def execute(self, entries, obj, ctx, prev=None):
        if any(e.key == 'set_country_flag' for e in entries):
            assert obj['kind'] == 'country'
            assert all(e.key == 'set_country_flag' for e in entries)
            obj['flags'].update(e.value for e in entries)
            return
        return super().execute(entries, obj, ctx, prev)

    def pick(self, name, event='artifact_foundation.40', planet='P', ctx=None):
        ctx = self.open('boundary', planet) if ctx is None else ctx
        if ctx is None:
            return False
        p = self.planets[planet]
        option = next(e.value for e in foundation.EVENTS[event]
                      if e.key == 'option' and scalar(e.value, 'name') == name)
        if not (self.condition(child(option, 'trigger', []), p, ctx)
                and self.condition(child(option, 'allow', []), p, ctx)):
            return False
        self.execute(child(option, 'hidden_effect', []), p, ctx)
        return True

    def begin(self, planet='P', ctx=None):
        return self.pick('artifact_boundary.start', planet=planet, ctx=ctx)

    def archive(self, ctx=None):
        return self.pick('artifact_boundary.archive', 'artifact_foundation.30', ctx=ctx)

    def anchor(self):
        d = supply.DECISIONS['decision_artifact_rule_anchor']
        p = self.planets['Q']
        if not (self.condition(child(d, 'potential'), p, {})
                and self.condition(child(d, 'allow'), p, {})):
            return False
        self.execute(child(d, 'effect'), p, {})
        return True

    def protection(self):
        modifier = child(BUILDINGS[SITE], 'triggered_planet_modifier')
        enabled = self.condition(child(modifier, 'potential'),
                                 self.colony_scope(self.planets['Q']), {})
        return float(scalar(modifier, 'planet_orbital_bombardment_damage')) if enabled else 0


class BoundaryEngineeringTests(unittest.TestCase):
    def setUp(self):
        for name, extra in [('TRIGGERS', supply.TRIGGERS), ('EFFECTS', supply.EFFECTS),
                            ('EVENTS', supply.EVENTS)]:
            self.enterContext(patch.dict(getattr(foundation, name), extra))
        self.w = World()
        self.p, self.q = self.w.planets.values()
        self.a = self.w.countries['A']

    def complete(self):
        self.assertTrue(self.w.begin())
        for _ in range(6):
            self.w.monthly()

    def test_three_stages_pay_once_and_only_recovered_result_can_be_archived(self):
        before = deepcopy(self.a['resources'])
        self.assertTrue(self.w.begin())
        self.assertFalse(self.w.begin())
        self.q['buildings'].add(LAB)
        self.assertFalse(self.w.begin('Q'))
        self.assertEqual(self.a['resources']['energy'], before['energy'] - 600)
        self.assertEqual(self.a['resources']['consumer_goods'], before['consumer_goods'] - 200)
        self.assertEqual(self.a['resources']['alloys'], before['alloys'] - 100)
        for expected in [(1, 0, 0), (2, 0, 0), (2, 1, 0), (2, 2, 0), (2, 3, 0), (2, 3, 1)]:
            self.w.open('boundary')
            self.assertFalse(self.w.archive())
            self.w.monthly()
            self.assertEqual(tuple(self.p['vars']['arf_r4_' + k] for k in
                                   ('preparation', 'experiment', 'recovery')), expected)
        self.assertEqual(self.p['modifiers'], {RESULT: 720})
        self.assertFalse(self.w.begin('Q'))  # 待提交的结果也占用本国试验名额。
        self.a['techs'].remove(INTERFACE)
        self.assertFalse(self.w.archive())
        self.a['techs'].add(INTERFACE)
        paid = deepcopy(self.a['resources'])
        self.assertTrue(self.w.archive())
        self.assertFalse(self.w.archive())
        self.assertEqual(self.a['flags'], {RECORD})
        self.assertEqual(self.a['resources'], paid)
        self.assertEqual(self.p['modifiers'], {})
        self.assertFalse(self.w.begin())
        self.assertFalse(self.w.begin('Q'))
        self.assertNotIn(RECORD, self.w.countries['B']['flags'])

    def test_missing_resources_and_paused_sites_preserve_paid_progress(self):
        self.a['resources']['alloys'] = 99
        before = deepcopy(self.a['resources'])
        self.assertFalse(self.w.begin())
        self.assertEqual(self.a['resources'], before)
        self.a['resources']['alloys'] = 1000
        self.w.begin()
        self.w.monthly()
        paid = deepcopy(self.a['resources'])
        for key, blocked, restored in [('inactive', {LAB}, set()), ('buildings', set(), {LAB}),
                                        ('controller', 'B', 'A'), ('bombarded', True, False)]:
            self.p[key] = blocked
            self.w.monthly()
            self.assertEqual(self.p['vars']['arf_r1_progress'], 1)
            self.p[key] = restored
        self.a['techs'].remove(RESEARCH)
        self.w.monthly()
        self.assertEqual(self.p['vars']['arf_r1_progress'], 1)
        self.a['techs'].add(RESEARCH)
        for _ in range(5):
            self.w.monthly()
        self.assertIn(RESULT, self.p['modifiers'])
        self.assertEqual(self.a['resources'], paid)

    def test_transfer_and_stale_window_do_not_move_knowledge_or_charge_new_owner(self):
        ctx = self.w.open('boundary')
        self.w.begin(ctx=ctx)
        for _ in range(3):
            self.w.monthly()
        self.p['owner'] = self.p['controller'] = 'B'
        before = deepcopy(self.w.countries['B']['resources'])
        self.w.dispatch('artifact_foundation.2', self.p)
        self.assertEqual(self.p['vars']['arf_r4_last_preparation'], 2)
        self.assertEqual(self.p['vars']['arf_r4_last_experiment'], 1)
        self.assertNotIn('arf_r1_active', self.p['flags'])
        self.assertFalse(self.w.begin(ctx=ctx))
        self.assertFalse(self.w.archive(ctx=ctx))
        self.assertEqual(self.w.countries['B']['resources'], before)
        self.assertNotIn(RECORD, self.w.countries['B']['flags'])

    def test_anchor_requires_actual_record_and_keeps_protection_during_bombardment(self):
        before = deepcopy(self.a['resources'])
        self.assertFalse(self.w.anchor())
        self.assertEqual(self.a['resources'], before)
        self.complete()
        self.w.archive()
        self.q['bombarded'] = True
        self.assertFalse(self.w.anchor())  # 启动前需要清洁现场。
        self.q['bombarded'] = False
        before = deepcopy(self.a['resources'])
        self.assertTrue(self.w.anchor())
        self.assertEqual(self.a['resources']['energy'], before['energy'] - 500)
        self.assertEqual(self.a['resources']['rare_crystals'], before['rare_crystals'] - 100)
        self.assertEqual(self.w.targets['acs_owner@Q'], ('country', 'A'))
        self.q['bombarded'] = True
        self.assertEqual(self.w.protection(), -0.20)
        self.w.elapsed(30)
        self.assertFalse(self.w.anchor())
        self.assertEqual(self.q['modifiers'][WINDOW], 330)
        self.q['inactive'].add(SITE)
        self.assertEqual(self.w.protection(), 0)
        self.w.elapsed(30)
        self.q['inactive'].clear()
        self.assertEqual(self.w.protection(), -0.20)
        self.assertEqual(self.q['modifiers'][WINDOW], 300)
        self.q['controller'] = 'B'
        self.assertEqual(self.w.protection(), 0)
        self.q['controller'] = 'A'
        self.assertEqual(self.w.protection(), -0.20)

    def test_anchor_expiry_transfer_and_destruction_do_not_duplicate_or_inherit(self):
        self.complete()
        self.w.archive()
        self.assertTrue(self.w.anchor())
        self.w.elapsed(360)
        self.assertEqual(self.w.protection(), 0)
        self.assertIn(RECORD, self.a['flags'])
        paid = deepcopy(self.a['resources'])
        self.assertTrue(self.w.anchor())
        self.assertEqual(self.a['resources']['energy'], paid['energy'] - 500)
        self.q['owner'] = self.q['controller'] = 'B'
        self.assertEqual(self.w.protection(), 0)
        self.w.dispatch('artifact_civil_supply.2', self.q)
        self.assertNotIn(WINDOW, self.q['modifiers'])
        self.assertNotIn('acs_owner@Q', self.w.targets)
        self.assertFalse(self.w.anchor())
        self.assertIn(RECORD, self.a['flags'])
        self.q['owner'] = self.q['controller'] = 'A'
        self.assertTrue(self.w.anchor())
        self.w.dispatch('artifact_civil_supply.3', self.q)
        self.assertEqual(self.w.protection(), 0)
        self.assertNotIn('acs_managed', self.q['flags'])

    def test_expired_experiment_never_archives_and_retry_costs_again(self):
        self.complete()
        self.w.elapsed(720)
        self.assertFalse(self.w.archive())
        paid = deepcopy(self.a['resources'])
        self.assertTrue(self.w.begin())
        self.assertEqual(self.a['resources']['energy'], paid['energy'] - 600)
        self.assertEqual(self.p['vars']['arf_r4_recovery'], 0)

    def test_upgraded_lab_keeps_original_sample_project_and_capacity_contract(self):
        self.assertTrue(self.w.choose('sample_analysis'))
        for _ in range(3):
            self.w.monthly()
        self.assertEqual(self.p['modifiers'], {'artifact_foundation_sample_analysis': 720})
        low = load('mod/common/buildings/artifact_public_foundation_buildings.txt')['building_artifact_sample_repository']
        self.assertEqual([e.value or e.key for e in child(low, 'upgrades')], [LAB])
        self.assertEqual(scalar(child(low, 'triggered_planet_modifier'), 'job_artifact_junior_observer_add'), '100')
        self.assertEqual(scalar(child(BUILDINGS[LAB], 'planet_modifier'), 'job_artifact_junior_observer_add'), '300')
        potential = child(child(low, 'triggered_planet_modifier'), 'potential')
        self.assertFalse(self.w.condition(potential, self.p, {}))
        self.p['inactive'].add(LAB)
        self.assertTrue(self.w.condition(potential, self.p, {}))
        # 升级不能让A05联合观测丢失原样本来源。
        obs = load('mod/common/buildings/aemusa_buildings.txt')['building_artifact_black_gate_observatory']
        comparison = next(e.value for e in obs if e.key == 'triggered_planet_modifier'
                          and scalar(e.value, 'planet_jobs_physics_research_produces_mult'))
        self.p['buildings'].add('building_artifact_black_gate_observatory')
        self.a['techs'].add('tech_artifact_multi_source_comparison')
        self.assertFalse(self.w.condition(child(comparison, 'potential'), self.p, {}))
        self.p['inactive'].clear()
        self.assertTrue(self.w.condition(child(comparison, 'potential'), self.p, {}))


if __name__ == '__main__':
    unittest.main()
