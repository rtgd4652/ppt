"""执行R4b正式脚本，核对实付备料、重复结算与所有权；不模拟引擎建造或真实存读档。"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_foundation_projects as foundation
import test_artifact_civil_supply as supply

TECH = 'tech_artifact_strategic_engineering_supply'
YARD = 'building_artifact_engineering_supply_yard'
STOCK = 'acs_strategic_supply_reserved'


class StrategicSupplyTests(unittest.TestCase):
    def setUp(self):
        # 沿用严格脚本执行器；不重写备料算法或默许未知作用域。
        for name in ('TRIGGERS', 'EFFECTS', 'EVENTS'):
            self.enterContext(patch.dict(getattr(foundation, name), getattr(supply, name)))
        self.w = self.new_world()
        self.a = self.w.countries['A']
        self.p, self.q = self.w.planets.values()

    @staticmethod
    def new_world():
        world = supply.World()
        for country in world.countries.values():
            country['techs'].add(TECH)
        for planet in world.planets.values():
            planet['buildings'].add(YARD)
        return world

    def reserve(self, world=None):
        world = world or self.w
        self.assertTrue(world.use('register_receiver', 'Q'))
        self.assertTrue(world.use('reserve', 'Q'))
        self.assertTrue(world.use('strategic_reserve', 'Q'))

    def test_real_payment_and_release_cannot_refund_twice(self):
        before = deepcopy(self.a['resources'])
        self.reserve()
        self.assertEqual(self.a['resources']['minerals'], before['minerals'] - 2000)
        self.assertEqual(self.a['resources']['alloys'], before['alloys'] - 1000)
        self.assertEqual(self.a['resources']['energy'], before['energy'] - 500)
        paid = deepcopy(self.a['resources'])
        self.w.force_effect('strategic_reserve', 'Q')
        self.assertEqual(self.a['resources'], paid)
        self.assertFalse(self.w.use('refund', 'Q'))
        self.assertNotIn('acs_supply_reserved', self.q['modifiers'])
        self.assertTrue(self.w.use('strategic_release', 'Q'))
        self.w.force_effect('strategic_release', 'Q')
        self.assertEqual(self.a['resources']['minerals'], before['minerals'] - 400)
        self.assertEqual(self.a['resources']['alloys'], before['alloys'] - 200)
        self.assertEqual(self.a['resources']['energy'], before['energy'] - 500)
        self.assertNotIn(STOCK, self.q['modifiers'])
        self.assertNotIn('acs_supply_reserved', self.q['modifiers'])

    def test_missing_stock_short_payment_or_disabled_yard_never_charge(self):
        for missing in ('stock', 'alloys', 'yard'):
            with self.subTest(missing=missing):
                world = self.new_world()
                self.assertTrue(world.use('register_receiver', 'Q'))
                self.assertTrue(world.use('reserve', 'Q'))
                q, a = world.planets['Q'], world.countries['A']
                if missing == 'stock':
                    q['modifiers'].pop('acs_supply_reserved')
                elif missing == 'alloys':
                    a['resources']['alloys'] = 899
                else:
                    q['inactive'].add(YARD)
                before = deepcopy((a['resources'], q['modifiers']))
                self.assertFalse(world.use('strategic_reserve', 'Q'))
                world.force_effect('strategic_reserve', 'Q')
                self.assertEqual((a['resources'], q['modifiers']), before)

    def test_national_slot_survives_disabled_site_and_receiver_reassignment(self):
        self.reserve()
        self.q['inactive'].add(YARD)
        self.assertTrue(self.w.use('unregister', 'Q'))
        self.assertTrue(self.w.use('register_receiver', 'P'))
        self.assertTrue(self.w.use('reserve', 'P'))
        before = deepcopy(self.a['resources'])
        self.assertFalse(self.w.use('strategic_reserve', 'P'))
        self.w.force_effect('strategic_reserve', 'P')
        self.assertEqual(self.a['resources'], before)
        self.assertIn(STOCK, self.q['modifiers'])
        # 撤回不要求原设施或接收端仍存在；释放全国名额后另一端才能正常备料。
        self.q['buildings'].remove(YARD)
        self.assertTrue(self.w.use('strategic_release', 'Q'))
        self.assertTrue(self.w.use('strategic_reserve', 'P'))
        self.assertIn(STOCK, self.p['modifiers'])

    def test_occupation_bombardment_or_site_loss_pauses_without_destroying_stock(self):
        self.reserve()
        paid = deepcopy(self.a['resources'])
        for key, value in [('controller', 'B'), ('bombarded', True), ('inactive', {YARD})]:
            with self.subTest(condition=key):
                old = deepcopy(self.q[key])
                self.q[key] = value
                self.w.force_effect('strategic_consume', 'Q')
                self.assertIn(STOCK, self.q['modifiers'])
                self.w.dispatch('artifact_civil_supply.1', self.a)
                self.assertIn(STOCK, self.q['modifiers'])
                self.assertEqual(self.a['resources'], paid)
                self.q[key] = old
        self.assertTrue(self.w.condition(supply.TRIGGERS['artifact_civil_supply_strategic_ready'], self.q, {}))
        self.assertEqual(self.w.targets['acs_owner@Q'], ('country', 'A'))

    def test_transfer_monthly_fallback_and_destruction_discard_without_refund(self):
        for event in ('transfer', 'monthly', 'destroy'):
            with self.subTest(event=event):
                world = self.new_world()
                self.reserve(world)
                q = world.planets['Q']
                before = {k: deepcopy(v['resources']) for k, v in world.countries.items()}
                if event != 'destroy':
                    q.update(owner='B', controller='B')
                    world.force_effect('strategic_release', 'Q')
                    world.force_effect('strategic_consume', 'Q')
                    self.assertIn(STOCK, q['modifiers'])
                if event == 'monthly':
                    world.dispatch('artifact_civil_supply.1', world.countries['B'])
                else:
                    world.dispatch('artifact_civil_supply.2' if event == 'transfer' else 'artifact_civil_supply.3', q)
                self.assertNotIn(STOCK, q['modifiers'])
                self.assertNotIn('acs_owner@Q', world.targets)
                self.assertEqual({k: v['resources'] for k, v in world.countries.items()}, before)

    def test_consume_once_prevents_refund_and_requires_new_payment(self):
        self.reserve()
        paid = deepcopy(self.a['resources'])
        self.w.force_effect('strategic_consume', 'Q')
        self.w.force_effect('strategic_consume', 'Q')
        self.assertNotIn(STOCK, self.q['modifiers'])
        self.assertFalse(self.w.use('strategic_release', 'Q'))
        self.assertEqual(self.a['resources'], paid)
        self.assertFalse(self.w.use('strategic_reserve', 'Q'))
        self.assertTrue(self.w.use('reserve', 'Q'))
        self.assertTrue(self.w.use('strategic_reserve', 'Q'))
        self.assertEqual(self.a['resources']['minerals'], paid['minerals'] - 2000)
        self.assertEqual(self.a['resources']['alloys'], paid['alloys'] - 1000)


if __name__ == '__main__':
    unittest.main()
