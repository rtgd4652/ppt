"""执行E09正式脚本，核对付费阶段和条件收益；不模拟引擎巨构队列或真实存读档。"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_foundation_projects as foundation
import test_artifact_civil_supply as supply
import test_artifact_strategic_supply as strategic

TECH = 'tech_artifact_segmented_large_engineering'
YARD = 'building_artifact_large_engineering_yard'
PROJECT = 'acs_segmented_project'
WORK = 'acs_segmented_work'
BUILDING = foundation.load('mod/common/buildings/artifact_segmented_engineering_buildings.txt')[YARD]


class SegmentedEngineeringTests(unittest.TestCase):
    def setUp(self):
        for name in ('TRIGGERS', 'EFFECTS', 'EVENTS'):
            self.enterContext(patch.dict(getattr(foundation, name), getattr(supply, name)))
        self.w = self.new_world()
        self.a = self.w.countries['A']
        self.p, self.q = self.w.planets.values()

    @staticmethod
    def new_world():
        world = strategic.StrategicSupplyTests.new_world()
        for country in world.countries.values():
            country['techs'].add(TECH)
        for planet in world.planets.values():
            planet['buildings'].add(YARD)
        return world

    def start(self, world=None):
        world = world or self.w
        for action in ('register_receiver', 'reserve', 'strategic_reserve', 'segmented_start'):
            self.assertTrue(world.use(action, 'Q'), action)

    def months(self, count, world=None):
        world = world or self.w
        for _ in range(count):
            world.dispatch('artifact_civil_supply.1', world.countries['A'])

    def complete(self, world=None):
        world = world or self.w
        self.start(world)
        self.months(3, world)
        self.assertTrue(world.use('segmented_assemble', 'Q'))
        self.months(4, world)
        self.assertTrue(world.use('segmented_commission', 'Q'))
        self.months(2, world)

    def capacity(self, world=None, owner='A'):
        # 只求正式建筑的条件供源，不模拟原生并行建造规则。
        world = world or self.w
        modifier = foundation.child(BUILDING, 'triggered_country_modifier')
        total = 0
        for p in world.planets.values():
            if p['owner'] == owner and YARD in p['buildings'] - p['inactive']:
                if world.condition(foundation.child(modifier, 'potential'), world.colony_scope(p), {}):
                    total += float(foundation.scalar(modifier, 'country_megastructure_build_cap_add'))
        return total

    def view(self, expected):
        before = deepcopy((self.a['resources'], self.q['modifiers'], self.q['vars']))
        self.assertTrue(self.w.use('segmented_status', 'Q'))
        texts = [foundation.scalar(e.value, 'text') for e in supply.EVENTS['artifact_civil_supply.10']
                 if e.key == 'desc' and self.w.condition(foundation.child(e.value, 'trigger'), self.q, {})]
        self.assertEqual(texts, ['artifact_segmented.' + expected])
        self.assertEqual((self.a['resources'], self.q['modifiers'], self.q['vars']), before)

    def test_real_budget_paid_stages_wait_for_confirmation_and_deliver_once(self):
        before = deepcopy(self.a['resources'])
        self.view('intro')
        self.start()
        self.assertNotIn(strategic.STOCK, self.q['modifiers'])
        self.w.force_effect('segmented_start', 'Q')
        self.assertEqual(self.q['vars'][WORK], 0)
        self.view('preparing')
        self.months(3)
        self.view('prepared')
        paid = deepcopy(self.a['resources'])
        self.months(5)
        self.assertEqual(self.a['resources'], paid)
        self.assertEqual(self.q['vars'][WORK], 0)
        self.assertEqual(self.capacity(), 0)
        self.assertTrue(self.w.use('segmented_assemble', 'Q'))
        self.w.force_effect('segmented_assemble', 'Q')
        self.view('assembling')
        self.months(4)
        self.view('assembled')
        self.assertTrue(self.w.use('segmented_commission', 'Q'))
        self.w.force_effect('segmented_commission', 'Q')
        self.view('commissioning')
        self.months(1)
        self.assertEqual(self.capacity(), 0)
        self.months(1)
        self.view('operational')
        self.assertEqual(self.capacity(), 1)
        self.months(6)
        self.assertEqual(self.capacity(), 1)
        for resource, cost in {'minerals': 3000, 'alloys': 2500, 'energy': 1500, 'consumer_goods': 300}.items():
            self.assertEqual(self.a['resources'][resource], before[resource] - cost)
        self.assertNotIn(WORK, self.q['vars'])

    def test_without_actual_budget_or_later_phase_resources_nothing_is_charged(self):
        self.assertTrue(self.w.use('register_receiver', 'Q'))
        before = deepcopy(self.a['resources'])
        self.w.force_effect('segmented_start', 'Q')
        self.assertNotIn(PROJECT, self.q['modifiers'])
        self.assertEqual(self.a['resources'], before)
        self.assertTrue(self.w.use('reserve', 'Q'))
        self.assertTrue(self.w.use('strategic_reserve', 'Q'))
        self.assertTrue(self.w.use('segmented_start', 'Q'))
        self.w.force_effect('segmented_commission', 'Q')
        self.months(3)
        self.a['resources']['alloys'] = 1499
        before = deepcopy((self.a['resources'], self.q['modifiers'], self.q['vars']))
        self.assertFalse(self.w.use('segmented_assemble', 'Q'))
        self.w.force_effect('segmented_assemble', 'Q')
        self.assertEqual((self.a['resources'], self.q['modifiers'], self.q['vars']), before)

    def test_interrupted_months_preserve_progress_and_do_not_catch_up(self):
        self.start()
        self.months(1)
        paid = deepcopy(self.a['resources'])
        for key, value in [('controller', 'B'), ('bombarded', True), ('inactive', {YARD})]:
            old = deepcopy(self.q[key])
            self.q[key] = value
            self.months(4)
            self.view('paused')
            self.assertEqual(self.q['vars'][WORK], 1)
            self.assertEqual(self.a['resources'], paid)
            self.q[key] = old
        self.months(1)
        self.assertEqual(self.q['vars'][WORK], 2)
        self.assertIn('acs_segmented_preparing', self.q['modifiers'])
        self.months(1)
        self.view('prepared')

    def test_delivered_yard_requires_live_provider_but_not_construction_receiver(self):
        self.complete()
        self.assertTrue(self.w.use('unregister', 'Q'))
        self.q['inactive'].add(strategic.YARD)
        self.assertEqual(self.capacity(), 1)
        for key, value in [('controller', 'B'), ('bombarded', True), ('inactive', {YARD})]:
            old = deepcopy(self.q[key])
            self.q[key] = value
            self.assertEqual(self.capacity(), 0)
            self.view('offline')
            self.q[key] = old
            self.assertEqual(self.capacity(), 1)

    def test_offline_completed_project_keeps_unique_slot_and_does_not_consume_another_budget(self):
        self.complete()
        self.q['inactive'].add(YARD)
        self.assertTrue(self.w.use('unregister', 'Q'))
        for action in ('register_receiver', 'reserve', 'strategic_reserve'):
            self.assertTrue(self.w.use(action, 'P'))
        self.assertFalse(self.w.use('segmented_start', 'P'))
        self.w.force_effect('segmented_start', 'P')
        self.assertIn(strategic.STOCK, self.p['modifiers'])
        self.assertNotIn(PROJECT, self.p['modifiers'])

    def test_cancel_discards_progress_without_erasing_new_supply(self):
        self.start()
        self.months(1)
        for action in ('reserve', 'strategic_reserve', 'reserve'):
            self.assertTrue(self.w.use(action, 'Q'))
        self.q['buildings'].remove(YARD)
        before = deepcopy(self.a['resources'])
        self.assertTrue(self.w.use('segmented_cancel', 'Q'))
        self.w.force_effect('segmented_cancel', 'Q')
        self.assertEqual(self.a['resources'], before)
        self.assertNotIn(PROJECT, self.q['modifiers'])
        self.assertNotIn(WORK, self.q['vars'])
        self.assertIn(strategic.STOCK, self.q['modifiers'])
        self.assertIn('acs_supply_reserved', self.q['modifiers'])

    def test_owner_change_or_destruction_cleans_state_and_never_transfers_capacity(self):
        for event in ('transfer', 'monthly', 'destroy'):
            with self.subTest(event=event):
                world = self.new_world()
                self.complete(world)
                self.assertEqual(self.capacity(world), 1)
                q = world.planets['Q']
                before = {k: deepcopy(v['resources']) for k, v in world.countries.items()}
                if event != 'destroy':
                    q.update(owner='B', controller='B')
                    # 回调尚未清账时，新国也不能继承原国的容量或结算权。
                    self.assertEqual(self.capacity(world, 'B'), 0)
                    world.force_effect('segmented_assemble', 'Q')
                    world.force_effect('segmented_cancel', 'Q')
                    self.assertIn(PROJECT, q['modifiers'])
                if event == 'monthly':
                    world.dispatch('artifact_civil_supply.1', world.countries['B'])
                else:
                    world.dispatch('artifact_civil_supply.2' if event == 'transfer' else 'artifact_civil_supply.3', q)
                self.assertNotIn(PROJECT, q['modifiers'])
                self.assertNotIn('acs_segmented_operational', q['modifiers'])
                self.assertNotIn(WORK, q['vars'])
                self.assertEqual(self.capacity(world), 0)
                self.assertEqual(self.capacity(world, 'B'), 0)
                self.assertNotIn('acs_owner@Q', world.targets)
                self.assertEqual({k: v['resources'] for k, v in world.countries.items()}, before)


if __name__ == '__main__':
    unittest.main()
