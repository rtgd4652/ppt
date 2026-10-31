"""核对整补付费、失控与续期边界及电脑原生角色合同；不模拟引擎战斗或读档。"""
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

import test_artifact_civil_supply as supply
from check_mod import parse, scalar

ROOT = supply.ROOT
child = supply.child
TECH = supply.load('mod/common/technology/artifact_joint_operations_technology.txt')
PARTS = {scalar(e.value, 'key'): e.value for e in parse(
    (ROOT / 'mod/common/component_templates/artifact_joint_operations_components.txt').read_text(encoding='utf-8'))}
RESEARCH = 'tech_artifact_expedition_reconstitution'
PLAN = 'acs_expedition_reconstitution'


class JointOperationsTests(unittest.TestCase):
    def setUp(self):
        for name, values in [('TRIGGERS', supply.TRIGGERS), ('EFFECTS', supply.EFFECTS), ('EVENTS', supply.EVENTS)]:
            self.enterContext(patch.dict(getattr(supply.foundation, name), values))
        self.w = supply.World()
        self.a = self.w.countries['A']
        self.a['techs'].update(TECH)
        self.q = self.w.planets['Q']

    def supplied_receiver(self):
        self.assertTrue(self.w.use('register_source'))
        self.assertTrue(self.w.use('register_receiver', 'Q'))
        self.assertTrue(self.w.use('reserve'))
        self.assertTrue(self.w.use('transfer'))

    def bonus(self, key):
        # 以原生建筑的殖民地作用域执行正式条件，必须回到行星求动态拥有者。
        colony = self.w.colony_scope(self.q)
        return sum(float(scalar(e.value, key) or 0)
                   for e in supply.BUILDINGS[supply.TERMINAL]
                   if e.key == 'triggered_planet_modifier'
                   and self.w.condition(child(e.value, 'potential'), colony, {}))

    def test_paid_stock_consumed_once_and_renewal_waits_for_expiry(self):
        self.supplied_receiver()
        before = deepcopy(self.a['resources'])
        self.assertTrue(self.w.use('expedition', 'Q'))
        self.assertNotIn('acs_supply_reserved', self.q['modifiers'])
        self.assertEqual(self.a['resources']['energy'], before['energy'] - 500)
        self.assertEqual(self.a['resources']['consumer_goods'], before['consumer_goods'] - 200)
        self.assertFalse(self.w.use('refund', 'Q'))
        self.w.elapsed(30)
        self.assertTrue(self.w.use('reserve', 'Q'))
        paid = deepcopy(self.a['resources'])
        self.w.force_effect('expedition', 'Q')
        self.assertEqual(self.a['resources'], paid)
        self.assertEqual(self.q['modifiers'][PLAN], 330)
        self.assertIn('acs_supply_reserved', self.q['modifiers'])
        self.w.elapsed(330)
        self.assertTrue(self.w.use('expedition', 'Q'))
        self.assertEqual(self.q['modifiers'][PLAN], 360)
        self.assertEqual(self.a['resources']['energy'], paid['energy'] - 500)

    def test_missing_research_or_cost_never_spends_or_creates_plan(self):
        self.supplied_receiver()
        for resource, amount in [('energy', 499), ('consumer_goods', 199)]:
            original = self.a['resources'][resource]
            self.a['resources'][resource] = amount
            before = deepcopy(self.a['resources'])
            self.assertFalse(self.w.use('expedition', 'Q'))
            self.w.force_effect('expedition', 'Q')
            self.assertEqual(self.a['resources'], before)
            self.assertNotIn(PLAN, self.q['modifiers'])
            self.assertIn('acs_supply_reserved', self.q['modifiers'])
            self.a['resources'][resource] = original
        self.a['techs'].remove(RESEARCH)
        self.w.force_effect('expedition', 'Q')
        self.assertNotIn(PLAN, self.q['modifiers'])
        self.assertIn('acs_supply_reserved', self.q['modifiers'])

    def test_control_facilities_and_role_suspend_bonus_without_resetting_clock(self):
        self.supplied_receiver()
        self.w.use('expedition', 'Q')
        self.assertEqual(self.bonus('planet_army_build_speed_mult'), .25)
        self.assertEqual(self.bonus('army_starting_experience_add'), 50)
        for problem, value in [('controller', 'B'), ('bombarded', True),
                               ('inactive', {supply.TERMINAL}), ('inactive', {supply.DEPOT})]:
            original = self.q[problem]
            self.q[problem] = value
            self.assertEqual(self.bonus('planet_army_build_speed_mult'), 0)
            self.w.elapsed(1)
            self.q[problem] = original
            self.assertEqual(self.bonus('planet_army_build_speed_mult'), .25)
        self.assertEqual(self.q['modifiers'][PLAN], 356)
        self.assertTrue(self.w.use('unregister', 'Q'))
        self.assertEqual(self.bonus('planet_army_build_speed_mult'), 0)
        self.assertTrue(self.w.use('register_receiver', 'Q'))
        self.assertEqual(self.bonus('planet_army_build_speed_mult'), .25)
        self.w.elapsed(356)
        self.assertEqual(self.bonus('planet_army_build_speed_mult'), 0)

    def test_transfer_of_ownership_clears_plan_without_refund(self):
        self.supplied_receiver()
        self.w.use('expedition', 'Q')
        self.q.update(owner='B', controller='B')
        before = deepcopy(self.w.countries['B']['resources'])
        self.assertEqual(self.bonus('planet_army_build_speed_mult'), 0)
        self.w.dispatch('artifact_civil_supply.1', self.w.countries['B'])
        self.assertNotIn(PLAN, self.q['modifiers'])
        self.assertNotIn('acs_owner@Q', self.w.targets)
        self.assertEqual(self.w.countries['B']['resources'], before)
        self.assertIn('acs_link_source', self.w.planets['P']['modifiers'])

    def test_computers_use_native_roles_while_aux_never_changes_behavior(self):
        # 舰体适配留给原生角色条件，禁止所有舰体共享单一line行为。
        for role in ('swarm', 'picket', 'line', 'artillery', 'carrier', 'torpedo', 'platform'):
            p = PARTS['ARTIFACT_JOINT_COMPUTER_' + role.upper()]
            self.assertEqual(scalar(p, 'component_set'), 'combat_computers')
            self.assertEqual(scalar(p, 'ship_behavior'), role)
            self.assertEqual(scalar(p, 'size'), 'small')
            required = 'ship_uses_platform_computers' if role == 'platform' else f'ship_uses_{role}_role'
            potential = child(p, 'potential')
            # R4e仅为炮击/航母增加明确舰型，原角色助手仍是原生舰型的入口。
            if role in ('artillery', 'carrier'):
                choices = child(potential, 'OR')
                self.assertEqual(scalar(choices, required), 'yes')
                self.assertEqual(scalar(choices, 'is_ship_size'), 'artifact_strategic_cruiser')
            else:
                self.assertEqual(scalar(potential, required), 'yes')
            self.assertIsNone(scalar(p, 'upgrades_to'))
        for key in ('ARTIFACT_TACTICAL_COORDINATION_MODULE', 'ARTIFACT_SUPPORT_COORDINATION_MODULE'):
            p = PARTS[key]
            self.assertEqual(scalar(p, 'size'), 'aux')
            self.assertEqual(scalar(p, 'component_set'), key)
            self.assertIsNone(scalar(p, 'ship_behavior'))
            self.assertFalse(child(p, 'aura'))
        old = {scalar(e.value, 'key') for path in (ROOT / 'mod/common/component_templates').glob('*.txt')
               if path.name != 'artifact_joint_operations_components.txt'
               for e in parse(path.read_text(encoding='utf-8-sig')) if isinstance(e.value, list)}
        self.assertFalse(old.intersection(PARTS))

    def test_public_dependencies_and_native_fields_have_no_personal_gate(self):
        all_tech = {e.key for path in (ROOT / 'mod/common/technology').glob('*.txt')
                    for e in parse(path.read_text(encoding='utf-8-sig'))}
        for key, body in TECH.items():
            prerequisites = {e.value for e in child(body, 'prerequisites')}
            self.assertLessEqual(prerequisites, all_tech)
            self.assertNotIn(key, prerequisites)
            self.assertIn('tech_artifact_intercolony_transport', prerequisites)
            self.assertNotIn('aemusa_ms_', str(body))
            self.assertFalse(child(body, 'modifier'))
        for part in PARTS.values():
            self.assertIn('ARTIFACT_USER', str(child(part, 'potential')))
            self.assertIn('country_uses_bio_ships', str(child(part, 'potential')))
            self.assertGreater(float(scalar(child(child(part, 'resources'), 'cost'), 'alloys')), 0)
            self.assertLess(float(scalar(part, 'power')), 0)
        # carrier的交战启动距离与炮击射程是两套独立字段。
        carrier = child(PARTS['ARTIFACT_JOINT_COMPUTER_CARRIER'], 'ship_modifier')
        self.assertIsNotNone(scalar(carrier, 'ship_engagement_range_mult'))
        self.assertIsNone(scalar(carrier, 'ship_weapon_range_mult'))


if __name__ == '__main__':
    unittest.main()
