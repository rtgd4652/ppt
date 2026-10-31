"""执行E12正式资格、原C12方案和E09/E11费用，保留C2一次性边界。

命运都市和建筑是已有系统的输入；不模拟原生改造、维修/就业或读档。
实际执行旧工业协调的付费/调整，以及备料、阶段投入和原月度流程。
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_system_engineering as system

calibration, base, child = system.calibration, system.base, system.child
TECH = 'tech_artifact_civil_engineering_coordination'
CITY = 'pc_artifact_destiny_city'
CENTER = 'building_artifact_coordination_center'
ASSEMBLY = 'building_artifact_cogovernance_assembly'
C12 = 'tech_artifact_covenant_cogovernance'
HISTORY = 'aemod_has_special_planet'
CITY_DECISION = base.load('mod/common/decisions/aemusa_destiny_city_decisions.txt')['decision_artifact_destiny_city_project']
UNIQUE_GUARD = child(child(child(CITY_DECISION, 'allow'), 'owner'), 'custom_tooltip')


class World(system.World):
    def __init__(self):
        super().__init__()
        for c in self.countries.values():
            c['techs'].add(TECH)
            c['flags'] = set()
        self.city = self.add_planet('C', system='S')
        self.city['planet_class'] = CITY
        self.city['buildings'] = {CENTER, ASSEMBLY}
        self.a['flags'].add(HISTORY)

    def term(self, e, stack):
        obj = stack[-1]
        if e.key == 'is_planet_class':
            assert obj['kind'] in ('planet', 'colony')
            return obj.get('planet_class') == e.value
        if e.key == 'has_country_flag':
            assert obj['kind'] == 'country'
            return e.value in obj['flags']
        if e.key == 'any_owned_planet':
            assert obj['kind'] == 'country'
            return any(self.condition(e.value, stack+[p]) for p in self.planets.values() if p['owner'] is obj)
        return super().term(e, stack)

    def budget(self, country=None):
        return self.condition(calibration.TRIGGERS['artifact_civil_engineering_budget_active'],
                              [self.a if country is None else country])

    def activate(self):
        assert self.use('civic_industry', self.city, old=True)
        self.elapsed(180)
        assert self.budget()

    def ready_assembly(self):
        self.prepare()
        assert self.use('dispatch')
        assert self.use('segmented_start', self.q, old=True)
        for _ in range(3): self.monthly()


class CivilEngineeringTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(calibration.TRIGGERS, system.TRIGGERS))
        self.enterContext(patch.dict(calibration.EFFECTS, system.EFFECTS))

    def test_requires_real_owned_city_and_operational_paid_scheme(self):
        w = World(); self.assertFalse(w.budget()); w.activate()
        for stop, resume in (
            (lambda: w.city.update(planet_class='pc_continental'), lambda: w.city.update(planet_class=CITY)),
            (lambda: w.city['modifiers'].pop('acs_civic_industry'), lambda: w.city['modifiers'].update(acs_civic_industry=-1)),
            (lambda: w.city['modifiers'].update(acs_civic_adjusting=180), lambda: w.city['modifiers'].pop('acs_civic_adjusting')),
            (lambda: w.city.update(controller=w.countries['B']), lambda: w.city.update(controller=w.a)),
            (lambda: w.city.update(bombarded=True), lambda: w.city.update(bombarded=False)),
            (lambda: w.city['inactive'].update({CENTER, ASSEMBLY}), lambda: w.city['inactive'].clear()),
            (lambda: w.a['techs'].remove(TECH), lambda: w.a['techs'].add(TECH)),
            (lambda: w.a['techs'].remove(C12), lambda: w.a['techs'].add(C12)),
        ):
            stop(); before = w.state()
            self.assertFalse(w.budget()); self.assertEqual(w.state(), before)
            resume(); self.assertTrue(w.budget())

    def test_reuses_exact_civic_fee_adjustment_and_mutually_exclusive_choice(self):
        w = World(); before = deepcopy(w.a['resources'])
        self.assertTrue(w.use('civic_industry', w.city, old=True))
        expected = {**before, 'energy':before['energy']-500, 'unity':before['unity']-250}
        self.assertEqual(w.a['resources'], expected)
        self.assertFalse(w.use('civic_industry', w.city, old=True)); self.assertFalse(w.budget())
        w.elapsed(179); self.assertFalse(w.budget())
        w.elapsed(1); self.assertTrue(w.budget())
        # 两种高级设施并存仍只有一个布尔预算来源，不叠加优惠档位。
        w.city['inactive'].add(CENTER); self.assertTrue(w.budget())
        w.city['inactive'].clear()
        self.assertTrue(w.use('civic_research', w.city, old=True)); self.assertFalse(w.budget())
        w.elapsed(180); self.assertFalse(w.budget())
        self.assertNotIn('acs_civic_industry', w.city['modifiers'])
        paid = deepcopy(w.a['resources'])
        self.assertTrue(w.use('cancel_civic', w.city, old=True))
        self.assertEqual(w.a['resources'], paid)

    def test_dispatch_checks_exact_300_balance_and_moves_only_one_pack(self):
        w = World(); w.activate(); w.prepare()
        w.a['resources']['energy'] = 299; before = w.state()
        self.assertFalse(w.use('dispatch')); w.force('dispatch'); self.assertEqual(w.state(), before)
        w.a['resources']['energy'] = 300; self.assertTrue(w.use('dispatch'))
        self.assertEqual(w.a['resources']['energy'], 0); self.assertTrue(w.budget())
        self.assertNotIn(system.STOCK, w.p['modifiers']); self.assertIn(system.STOCK, w.q['modifiers'])
        paid = w.state(); self.assertFalse(w.use('dispatch')); w.force('dispatch')
        self.assertEqual(w.state(), paid)

    def test_exact_discounted_stage_costs_keep_original_work_and_capacity(self):
        w = World(); w.activate(); w.ready_assembly()
        for minerals, alloys in [(749,1200),(750,1199)]:
            w.a['resources'].update(minerals=minerals,alloys=alloys); before = w.state()
            self.assertFalse(w.use('segmented_assemble', w.q, old=True)); self.assertEqual(w.state(), before)
        w.a['resources'].update(minerals=750,alloys=1200)
        self.assertTrue(w.use('segmented_assemble', w.q, old=True))
        self.assertEqual((w.a['resources']['minerals'],w.a['resources']['alloys']),(0,0))
        paid = w.state()
        w.execute(calibration.EFFECTS['artifact_civil_supply_segmented_assemble'],[w.q])
        self.assertEqual(w.state(), paid)
        for _ in range(4): w.monthly()
        for energy, goods in [(749,225),(750,224)]:
            w.a['resources'].update(energy=energy,consumer_goods=goods); before = w.state()
            self.assertFalse(w.use('segmented_commission', w.q, old=True)); self.assertEqual(w.state(), before)
        w.a['resources'].update(energy=750,consumer_goods=225)
        self.assertTrue(w.use('segmented_commission', w.q, old=True))
        self.assertEqual((w.a['resources']['energy'],w.a['resources']['consumer_goods']),(0,0))
        for _ in range(2): w.monthly()
        self.assertEqual(w.capacity(), 1); self.assertEqual(w.a['flags'], {HISTORY})
        self.assertEqual(w.city['planet_class'], CITY)

    def test_loss_before_payment_uses_standard_price_and_never_recharges_paid_stage(self):
        w = World(); w.activate(); w.ready_assembly()
        w.a['resources'].update(minerals=750,alloys=1200)
        w.city['inactive'].update({CENTER, ASSEMBLY}); before = w.state()
        self.assertFalse(w.use('segmented_assemble', w.q, old=True)); self.assertEqual(w.state(), before)
        w.a['resources'].update(minerals=1000,alloys=1500)
        self.assertTrue(w.use('segmented_assemble', w.q, old=True))
        self.assertEqual((w.a['resources']['minerals'],w.a['resources']['alloys']),(0,0))
        paid = deepcopy(w.a['resources'])
        w.monthly(); self.assertEqual(w.q['vars']['acs_segmented_work'],1)
        self.assertEqual(w.a['resources'],paid)
        w.city['inactive'].clear()
        for _ in range(3): w.monthly()
        w.a['resources'].update(energy=750,consumer_goods=225)
        self.assertTrue(w.use('segmented_commission', w.q, old=True))
        self.assertEqual((w.a['resources']['energy'],w.a['resources']['consumer_goods']),(0,0))

    def test_C2_unique_guard_and_history_survive_budget_and_city_transfer(self):
        w = World(); w.activate()
        self.assertFalse(w.condition(UNIQUE_GUARD,[w.a]))
        w.a['flags'].clear()  # 旧档已有都市而缺国家标记时，原C2仍禁止第二颗。
        self.assertFalse(w.condition(UNIQUE_GUARD,[w.a]))
        w.a['flags'].add(HISTORY)
        w.city['owner'] = w.city['controller'] = w.countries['B']
        self.assertFalse(w.budget()); self.assertFalse(w.budget(w.countries['B']))
        w.execute(child(calibration.CIV_EVENTS['artifact_civil_supply.2'],'immediate'),[w.city])
        self.assertNotIn('acs_civic_industry',w.city['modifiers'])
        self.assertEqual(w.a['flags'],{HISTORY}); self.assertEqual(w.city['planet_class'],CITY)
        self.assertFalse(w.condition(UNIQUE_GUARD,[w.a]))


if __name__ == '__main__':
    unittest.main()
