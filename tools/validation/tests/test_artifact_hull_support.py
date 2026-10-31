"""读取R4d正式脚本，检查实付定型与公共组件资格；不模拟引擎配装、战斗或存读档。"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_foundation_projects as foundation
import test_artifact_civil_supply as supply
import test_artifact_strategic_supply as strategic
from check_mod import parse, scalar

TECH = 'tech_artifact_terminal_hull_support'
PROJECT = 'acs_hull_project'
WORK = 'acs_hull_work'
QUALIFIED = 'acs_hull_qualified'
BRANCHES = {'reactor': 'tech_artifact_ship_phase_power',
            'thruster': 'tech_artifact_phase_maneuvering',
            'ftl': 'tech_artifact_hyperspace_coordination'}
PARTS = {scalar(e.value, 'key'): e.value for e in parse(
    (foundation.ROOT / 'mod/common/component_templates/artifact_hull_support_components.txt').read_text(encoding='utf-8'))}


class World(supply.World):
    def term(self, e, obj, ctx, prev):
        # 这里只扩展本机原生国家资格，不模拟部件船型助手或设计器行为。
        if e.key == 'country_uses_bio_ships':
            return obj.get('bio', False) == (e.value == 'yes')
        return super().term(e, obj, ctx, prev)

    def component_country_ready(self, component, country='A'):
        body = PARTS[component]
        c = self.countries[country]
        prerequisites = {e.value for e in foundation.child(body, 'prerequisites')}
        country_potential = foundation.child(foundation.child(body, 'potential'), 'from')
        return prerequisites <= c['techs'] and self.condition(country_potential, c, {})


class HullSupportTests(unittest.TestCase):
    def setUp(self):
        for name in ('TRIGGERS', 'EFFECTS', 'EVENTS'):
            self.enterContext(patch.dict(getattr(foundation, name), getattr(supply, name)))
        self.w = self.world()
        self.a = self.w.countries['A']
        self.p, self.q = self.w.planets.values()

    @staticmethod
    def world():
        w = World()
        for country in w.countries.values():
            country['techs'].update({TECH, strategic.TECH, *BRANCHES.values()})
        for planet in w.planets.values():
            planet['buildings'].add(strategic.YARD)
        return w

    def reserve(self, planet='Q', world=None):
        w = world or self.w
        for action in ('register_receiver', 'reserve', 'strategic_reserve'):
            self.assertTrue(w.use(action, planet), action)

    def start(self, world=None):
        w = world or self.w
        self.reserve(world=w)
        self.assertTrue(w.use('hull_start', 'Q'))

    def months(self, count, world=None, owner='A'):
        w = world or self.w
        for _ in range(count):
            w.dispatch('artifact_civil_supply.1', w.countries[owner])

    def view(self, expected):
        before = deepcopy((self.a, self.q))
        self.assertTrue(self.w.use('hull_status', 'Q'))
        descriptions = [scalar(e.value, 'text') for e in supply.EVENTS['artifact_civil_supply.11']
                        if e.key == 'desc' and self.w.condition(foundation.child(e.value, 'trigger'), self.q, {})]
        self.assertEqual(descriptions, ['artifact_hull.' + expected])
        self.assertEqual((self.a, self.q), before)

    def test_real_budget_then_six_valid_months_grants_country_result_once(self):
        before = deepcopy(self.a['resources'])
        self.view('intro')
        self.start()
        self.assertNotIn(strategic.STOCK, self.q['modifiers'])
        self.view('working')
        self.months(5)
        self.assertNotIn(QUALIFIED, self.a['modifiers'])
        self.w.force_effect('hull_start', 'Q')
        self.assertEqual(self.q['vars'][WORK], 5)
        self.months(1)
        self.assertEqual(self.a['modifiers'][QUALIFIED], -1)
        self.assertNotIn(PROJECT, self.q['modifiers'])
        self.assertNotIn(WORK, self.q['vars'])
        self.view('qualified')
        settled = deepcopy((self.a, self.q))
        self.months(4)
        self.w.force_effect('hull_start', 'Q')
        self.assertEqual((self.a, self.q), settled)
        for resource, cost in {'minerals': 2000, 'alloys': 1000, 'energy': 500}.items():
            self.assertEqual(self.a['resources'][resource], before[resource] - cost)

    def test_no_budget_no_result_and_paused_national_slot_cannot_be_duplicated(self):
        before = deepcopy((self.a, self.q))
        self.assertFalse(self.w.use('hull_start', 'Q'))
        self.w.force_effect('hull_start', 'Q')
        self.assertEqual((self.a, self.q), before)
        self.start()
        self.q['inactive'].add(strategic.YARD)
        self.assertTrue(self.w.use('unregister', 'Q'))
        self.reserve('P')
        self.assertFalse(self.w.use('hull_start', 'P'))
        self.w.force_effect('hull_start', 'P')
        self.assertIn(strategic.STOCK, self.p['modifiers'])
        self.assertNotIn(PROJECT, self.p['modifiers'])
        self.assertNotIn(QUALIFIED, self.a['modifiers'])

    def test_occupation_bombardment_or_inactive_site_pauses_without_catchup(self):
        self.start()
        self.months(1)
        paid = deepcopy(self.a['resources'])
        for key, value in [('controller', 'B'), ('bombarded', True), ('inactive', {strategic.YARD})]:
            old = deepcopy(self.q[key])
            self.q[key] = value
            self.months(3)
            self.view('paused')
            self.assertEqual(self.q['vars'][WORK], 1)
            self.assertEqual(self.a['resources'], paid)
            self.q[key] = old
        self.months(4)
        self.assertNotIn(QUALIFIED, self.a['modifiers'])
        self.months(1)
        self.assertIn(QUALIFIED, self.a['modifiers'])

    def test_transfer_and_destruction_clear_unfinished_work_without_inheritance(self):
        for mode in ('transfer_callback', 'monthly_fallback', 'destroy'):
            with self.subTest(mode=mode):
                w = self.world()
                self.start(w)
                self.months(5, w)
                q = w.planets['Q']
                before = {key: deepcopy(c['resources']) for key, c in w.countries.items()}
                if mode != 'destroy':
                    q.update(owner='B', controller='B')
                    w.force_effect('hull_monthly', 'Q')
                    self.assertNotIn(QUALIFIED, w.countries['B']['modifiers'])
                if mode == 'monthly_fallback':
                    self.months(1, w, 'B')
                else:
                    w.dispatch('artifact_civil_supply.3' if mode == 'destroy' else 'artifact_civil_supply.2', q)
                self.assertNotIn(PROJECT, q['modifiers'])
                self.assertNotIn(WORK, q['vars'])
                self.assertFalse(any(QUALIFIED in c['modifiers'] for c in w.countries.values()))
                self.assertEqual({key: c['resources'] for key, c in w.countries.items()}, before)

    def test_cancel_keeps_other_stock_and_completed_knowledge_stays_with_original_country(self):
        self.start()
        for action in ('reserve', 'strategic_reserve', 'reserve'):
            self.assertTrue(self.w.use(action, 'Q'))
        before = deepcopy(self.a['resources'])
        self.q['buildings'].remove(strategic.YARD)
        self.assertTrue(self.w.use('hull_cancel', 'Q'))
        self.w.force_effect('hull_cancel', 'Q')
        self.assertNotIn(PROJECT, self.q['modifiers'])
        self.assertIn(strategic.STOCK, self.q['modifiers'])
        self.assertIn('acs_supply_reserved', self.q['modifiers'])
        self.assertEqual(self.a['resources'], before)
        self.q['buildings'].add(strategic.YARD)
        self.assertTrue(self.w.use('hull_start', 'Q'))
        self.months(6)
        self.q.update(owner='B', controller='B')
        self.w.dispatch('artifact_civil_supply.2', self.q)
        self.assertIn(QUALIFIED, self.a['modifiers'])
        self.assertNotIn(QUALIFIED, self.w.countries['B']['modifiers'])

    def test_component_permissions_need_completed_trial_and_each_branch_research(self):
        for key in PARTS:
            self.assertFalse(self.w.component_country_ready(key))
        self.start()
        self.months(6)
        for key, body in PARTS.items():
            self.assertTrue(self.w.component_country_ready(key))
            self.assertFalse(self.w.component_country_ready(key, 'B'))
            prerequisites = {e.value for e in foundation.child(body, 'prerequisites')}
            for research in prerequisites:
                self.a['techs'].remove(research)
                self.assertFalse(self.w.component_country_ready(key), (key, research))
                self.a['techs'].add(research)
            # 新件只开放明确列出的普通舰型，不让个人唯一舰或将来E10舰型隐式继承。
            sizes = {e.value for e in foundation.child(body, 'size_restriction')}
            self.assertTrue(sizes <= {'corvette', 'frigate', 'destroyer', 'cruiser', 'battleship'})
        self.a['bio'] = True
        self.assertFalse(any(self.w.component_country_ready(k) for k in PARTS))


if __name__ == '__main__':
    unittest.main()
