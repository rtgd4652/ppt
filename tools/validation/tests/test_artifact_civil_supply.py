"""执行R3e正式脚本检查物资守恒与失控边界；不模拟引擎就业、升级或真实存读档。"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_foundation_projects as foundation
from check_mod import parse, scalar

ROOT = foundation.ROOT
load, child = foundation.load, foundation.child
PREFIX = 'artifact_civil_supply_'
TRIGGERS = load('mod/common/scripted_triggers/artifact_civil_supply_triggers.txt')
TRIGGERS.update(load('mod/common/scripted_triggers/artifact_garrison_triggers.txt'))
EFFECTS = load('mod/common/scripted_effects/artifact_civil_supply_effects.txt')
DECISIONS = load('mod/common/decisions/artifact_civil_supply_decisions.txt')
BUILDINGS = load('mod/common/buildings/artifact_civil_supply_buildings.txt')
BUILDINGS.update(load('mod/common/buildings/aemusa_buildings.txt'))
JOBS = load('mod/common/pop_jobs/artifact_civil_supply_jobs.txt')
EVENTS = {scalar(e.value, 'id'): e.value for e in parse(
    (ROOT / 'mod/events/artifact_civil_supply_events.txt').read_text(encoding='utf-8'))
    if e.key.endswith('_event')}
DEPOT = 'building_artifact_distribution_depot'
TERMINAL = 'building_artifact_intercolony_terminal'
REFINERY = 'building_artifact_directed_resonance_refinery'
CENTER = 'building_artifact_coordination_center'
ASSEMBLY = 'building_artifact_cogovernance_assembly'


class World(foundation.World):
    """复用已有严格夹具，只扩展本包实际用到的原生接口。"""
    def __init__(self):
        super().__init__()
        techs = set(load('mod/common/technology/artifact_civil_supply_technology.txt'))
        for country in self.countries.values():
            country['techs'].update(techs | {'tech_artifact_planetary_garrison'})
            country['resources']['unity'] = 5000
            country.update(modifiers={}, megastructures=[])
        self.add_planet('Q')
        for p in self.planets.values():
            p['buildings'] = {DEPOT, TERMINAL, REFINERY, CENTER, ASSEMBLY}
            p['inactive'] = set()

    def term(self, e, obj, ctx, prev):
        k, v = e.key, e.value
        if k in ('carrier', 'planet'):
            assert obj['kind'] in ('planet', 'colony')
            p = self.planets[obj['carrier_id']] if obj['kind'] == 'colony' else obj
            return self.condition(v, p, ctx, obj)
        if k == 'colony':
            assert obj['kind'] == 'job'
            return self.condition(v, self.colony_scope(self.planets[obj['planet_id']]), ctx, obj)
        if k == 'has_active_building':
            return v in obj['buildings'] - obj['inactive']
        if k == 'any_owned_megastructure':
            assert obj['kind'] == 'country'
            return any(self.condition(v, m, ctx, obj) for m in obj['megastructures'])
        if k == 'always':
            return v == 'yes'
        return super().term(e, obj, ctx, prev)

    def execute(self, entries, obj, ctx, prev=None):
        if not any(e.key == 'random_owned_colony' for e in entries):
            return super().execute(entries, obj, ctx, prev)
        # 本包此处没有if/else链；固定选首个合格端点，结果不依赖随机顺序。
        assert not any(e.key in ('else', 'else_if') for e in entries)
        for e in entries:
            if e.key != 'random_owned_colony':
                super().execute([e], obj, ctx, prev)
                continue
            for p in self.planets.values():
                c = self.colony_scope(p)
                if p['owner'] == obj['id'] and self.condition(child(e.value, 'limit'), c, ctx, obj):
                    self.execute([x for x in e.value if x.key != 'limit'], c, ctx, obj)
                    break

    def use(self, action, planet='P'):
        p = self.planets[planet]
        d = DECISIONS['decision_artifact_civil_' + action]
        if not self.condition(child(d, 'potential'), p, {}):
            return False
        if not self.condition(child(d, 'allow'), p, {}):
            return False
        self.execute(child(d, 'effect'), p, {})
        return True

    def force_effect(self, action, planet='P'):
        self.execute(EFFECTS[PREFIX + action], self.planets[planet], {})

    def elapsed(self, days):
        # 原生永久修正-1不会随时间到期；国家与行星定期修正同样处理。
        for obj in [*self.planets.values(), *self.countries.values()]:
            m = obj['modifiers']
            updated = {k: (-1 if left < 0 else left-days) for k, left in m.items()
                       if left < 0 or left > days}
            m.clear()
            m.update(updated)

    def recipe(self):
        job = {'kind': 'job', 'id': 'test_job', 'planet_id': 'P'}
        recipes = [e.value for e in child(JOBS['artifact_directed_resonator'], 'resources')
                   if e.key == 'produces' and self.condition(child(e.value, 'trigger'), job, {})]
        assert len(recipes) == 1, '同一个岗位必须只有一套有效配方'
        return {e.key: float(e.value) for e in recipes[0] if e.key != 'trigger'}

    def building_bonus(self, key):
        p = self.planets['P']
        colony = self.colony_scope(p)
        total = 0
        for name in p['buildings'] - p['inactive']:
            for e in BUILDINGS.get(name, []):
                if e.key == 'triggered_planet_modifier' and self.condition(child(e.value, 'potential'), colony, {}):
                    total += float(scalar(e.value, key) or 0)
        return total


class CivilSupplyTests(unittest.TestCase):
    def setUp(self):
        # 补充正式脚本词典仅限本测试，退出恢复，避免污染旧包测试。
        for name, values in [('TRIGGERS', TRIGGERS), ('EFFECTS', EFFECTS), ('EVENTS', EVENTS)]:
            self.enterContext(patch.dict(getattr(foundation, name), values))
        self.w = World()
        self.a = self.w.countries['A']
        self.p, self.q = self.w.planets.values()

    def network(self):
        self.assertTrue(self.w.use('register_source'))
        self.assertTrue(self.w.use('register_receiver', 'Q'))

    def test_paid_stock_refunds_once_and_cannot_be_created_without_resources(self):
        before = deepcopy(self.a['resources'])
        self.assertTrue(self.w.use('reserve'))
        self.w.force_effect('reserve')
        self.assertEqual(self.a['resources']['minerals'], before['minerals'] - 500)
        self.assertTrue(self.w.use('refund'))
        self.w.force_effect('refund')
        self.assertEqual(self.a['resources']['minerals'], before['minerals'] - 100)
        self.assertEqual(self.a['resources']['alloys'], before['alloys'] - 20)
        self.a['resources']['alloys'] = 99
        before = deepcopy(self.a['resources'])
        self.w.force_effect('reserve')
        self.assertEqual(self.a['resources'], before)
        self.assertNotIn('acs_supply_reserved', self.p['modifiers'])

    def test_unique_endpoints_transfer_one_existing_stock_and_local_use_is_final(self):
        self.assertTrue(self.w.use('register_source'))
        self.assertFalse(self.w.use('register_source', 'Q'))
        self.assertFalse(self.w.use('register_receiver'))
        self.assertTrue(self.w.use('register_receiver', 'Q'))
        self.assertTrue(self.w.use('reserve'))
        energy = self.a['resources']['energy']
        self.assertTrue(self.w.use('transfer'))
        self.w.force_effect('transfer')
        self.assertEqual(self.a['resources']['energy'], energy - 100)
        self.assertNotIn('acs_supply_reserved', self.p['modifiers'])
        self.assertIn('acs_supply_reserved', self.q['modifiers'])
        self.assertTrue(self.w.use('construction', 'Q'))
        self.assertFalse(self.w.use('refund', 'Q'))
        self.w.elapsed(30)
        self.w.force_effect('construction', 'Q')
        self.assertEqual(self.q['modifiers']['acs_construction_supply'], 150)

    def test_occupation_bombardment_and_disabled_facility_block_delivery_without_cost(self):
        self.network()
        self.w.use('reserve')
        before = deepcopy(self.a['resources'])
        for problem in ('controller', 'bombarded', 'inactive'):
            old = deepcopy(self.q[problem])
            self.q[problem] = {'controller': 'B', 'bombarded': True, 'inactive': {TERMINAL}}[problem]
            self.w.force_effect('transfer')
            self.assertEqual(self.a['resources'], before)
            self.assertIn('acs_supply_reserved', self.p['modifiers'])
            self.q[problem] = old
        self.assertTrue(self.w.use('transfer'))

    def test_new_owner_cannot_refund_and_monthly_uses_carrier_index(self):
        self.network()
        self.w.use('reserve')
        self.w.dispatch('artifact_civil_supply.1', self.a)
        self.assertIn('acs_supply_reserved', self.p['modifiers'])
        self.assertEqual(self.w.targets['acs_owner@P'], ('country', 'A'))
        self.assertEqual(self.w.targets['acs_owner@Q'], ('country', 'A'))
        self.p.update(owner='B', controller='B')
        before = deepcopy(self.w.countries['B']['resources'])
        self.w.force_effect('refund')
        self.assertEqual(self.w.countries['B']['resources'], before)
        # 模拟丢失转让回调，月度仍应清理，且不影响另一个端点。
        self.w.dispatch('artifact_civil_supply.1', self.w.countries['B'])
        self.assertEqual(self.p['modifiers'], {})
        self.assertNotIn('acs_owner@P', self.w.targets)
        self.assertIn('acs_link_receiver', self.q['modifiers'])
        self.w.dispatch('artifact_civil_supply.3', self.q)
        self.assertEqual(self.q['modifiers'], {})

    def test_large_engineering_consumes_both_stocks_once_and_cannot_refresh(self):
        self.network()
        self.w.use('reserve'); self.w.use('reserve', 'Q')
        before = deepcopy(self.a['resources'])
        self.assertFalse(self.w.use('megastructure'))
        self.assertEqual(self.a['resources'], before)
        self.a['megastructures'] = [{'kind': 'megastructure', 'id': 'M'}]
        self.assertTrue(self.w.use('megastructure'))
        self.assertEqual(self.a['resources']['energy'], before['energy'] - 1000)
        self.assertEqual(self.a['resources']['alloys'], before['alloys'] - 300)
        self.assertFalse(any('acs_supply_reserved' in p['modifiers'] for p in (self.p, self.q)))
        self.w.elapsed(30)
        self.w.use('reserve'); self.w.use('reserve', 'Q')
        before = deepcopy(self.a['resources'])
        self.w.force_effect('megastructure')
        self.assertEqual(self.a['resources'], before)
        self.assertEqual(self.a['modifiers']['acs_megastructure_supply'], 330)

    def test_refinery_switch_has_one_recipe_and_pays_again_after_cooldown(self):
        self.assertEqual(set(self.w.recipe().values()), {3.5})
        self.assertTrue(self.w.use('refinery_motes'))
        after = deepcopy(self.a['resources'])
        self.w.force_effect('refinery_crystals')
        self.assertEqual(self.a['resources'], after)
        self.assertEqual(set(self.w.recipe().values()), {3})
        self.w.elapsed(90)
        self.assertEqual(self.w.recipe(), {'volatile_motes': 6, 'rare_crystals': 1.5, 'exotic_gases': 1.5})
        self.assertTrue(self.w.use('refinery_crystals'))
        self.assertNotIn('acs_refinery_motes', self.p['modifiers'])
        self.assertEqual(self.a['resources']['energy'], after['energy'] - 300)
        self.w.elapsed(90)
        self.assertEqual(self.w.recipe()['rare_crystals'], 6)
        self.assertTrue(self.w.use('refinery_balanced'))
        self.w.elapsed(90)
        self.assertEqual(set(self.w.recipe().values()), {3.5})

    def test_civic_bonus_has_one_provider_and_cancel_does_not_erase_cooldown(self):
        self.assertTrue(self.w.use('civic_industry'))
        self.assertEqual(self.w.building_bonus('planet_jobs_alloys_produces_mult'), 0)
        self.w.elapsed(180)
        self.assertEqual(self.w.building_bonus('planet_jobs_alloys_produces_mult'), .10)
        self.p['inactive'].add(CENTER)
        self.assertEqual(self.w.building_bonus('planet_jobs_alloys_produces_mult'), .10)
        self.p['controller'] = 'B'
        self.assertEqual(self.w.building_bonus('planet_jobs_alloys_produces_mult'), 0)
        self.p['controller'] = 'A'
        self.assertTrue(self.w.use('civic_research'))
        self.assertTrue(self.w.use('cancel_civic'))
        self.assertFalse(self.w.use('civic_services'))
        self.assertEqual(self.p['modifiers']['acs_civic_adjusting'], 180)

    def test_governance_upgrade_keeps_single_existing_garrison_and_removes_old_jobs(self):
        self.p['flags'].add('artifact_garrison_enabled')
        self.w.targets['artifact_garrison_owner@P'] = ('country', 'A')
        self.p['buildings'].add('building_artifact_sanctum')
        self.assertEqual(self.w.building_bonus('planet_defense_armies_add'), 2)
        self.assertEqual(self.w.building_bonus('job_artifact_black_gate_warden_add'), 0)
        self.p['inactive'].add(CENTER)
        self.assertEqual(self.w.building_bonus('planet_defense_armies_add'), 2)
        self.assertEqual(self.w.building_bonus('job_artifact_black_gate_warden_add'), 200)


if __name__ == '__main__':
    unittest.main()
