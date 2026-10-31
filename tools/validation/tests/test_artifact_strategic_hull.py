"""执行E10正式资格条件，检查工业失效与组件闭包；不模拟原生队列、自动设计或战斗。"""
from copy import deepcopy
import re
import unittest
from unittest.mock import patch

import test_artifact_hull_support as hull
from check_mod import parse, scalar

foundation, supply = hull.foundation, hull.supply
ROOT, child = foundation.ROOT, foundation.child
TECH = 'tech_artifact_strategic_hull_engineering'
SIZE = 'artifact_strategic_cruiser'
YARD = 'building_artifact_large_engineering_yard'
ENGINEERING = 'tech_artifact_segmented_large_engineering'
SHIP = foundation.load('mod/common/ship_sizes/artifact_strategic_cruiser.txt')[SIZE]
text = (ROOT / 'mod/common/scripted_triggers/artifact_strategic_hull_triggers.txt').read_text(encoding='utf-8')
# 解析器不保留比较符，和原夹具一致，显式保留本包使用的星港等级比较。
text = re.sub(r'has_starbase_size\s*>=', 'has_starbase_size_ge =', text)
TRIGGERS = {e.key: e.value for e in parse(text)}


def components(filename):
    return {scalar(e.value, 'key'): e.value for e in parse(
        (ROOT / 'mod/common/component_templates' / filename).read_text(encoding='utf-8'))}


PARTS = components('artifact_strategic_hull_components.txt')
SHARED = {**components('artifact_hull_support_components.txt'),
          **components('artifact_joint_operations_components.txt')}


class World(hull.World):
    def term(self, e, obj, ctx, prev):
        k, v = e.key, e.value
        if k == 'is_scope_type':
            return obj['kind'] == v
        if k == 'has_starbase_size_ge':
            assert obj['kind'] == 'starbase'
            levels = ['starbase_outpost', 'starbase_starport', 'starbase_starhold',
                      'starbase_starfortress', 'starbase_citadel']
            return levels.index(obj['size']) >= levels.index(v)
        if k == 'is_megastructure_type':
            assert obj['kind'] == 'megastructure'
            return obj['type'] == v
        if k == 'is_ship_size':
            return obj['size'] == v
        if k == 'from':
            return self.condition(v, self.countries[obj['owner']], ctx, obj)
        if k == 'is_eager_explorer_ship':
            return obj.get('eager', False) == (v == 'yes')
        if k in ('ship_uses_artillery_role', 'ship_uses_carrier_role'):
            # 原生助手是否命中由外部角色夹具给出，只检查本Mod新增的OR边界。
            return (k in obj.get('native_roles', set())) == (v == 'yes')
        return super().term(e, obj, ctx, prev)

    def may_order(self, site):
        country = self.countries[site['owner']]
        return (all(e.value in country['techs'] for e in child(SHIP, 'prerequisites'))
                and self.condition(child(SHIP, 'potential_country'), country, {})
                and self.condition(child(SHIP, 'potential_construction'), site, {})
                and self.condition(child(SHIP, 'possible_construction'), site, {}))

    def may_fit(self, body, size=SIZE, country='A', native_roles=()):
        ship = dict(kind='ship', size=size, owner=country, native_roles=set(native_roles))
        sizes = child(body, 'size_restriction')
        return ((not sizes or size in {e.value for e in sizes})
                and all(e.value in self.countries[country]['techs'] for e in child(body, 'prerequisites', []))
                and self.condition(child(body, 'potential'), ship, {}))


class StrategicHullTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(foundation.TRIGGERS, {**supply.TRIGGERS, **TRIGGERS}))
        self.w = World()
        self.a, self.b = self.w.countries.values()
        self.a['techs'].update({TECH, ENGINEERING, hull.TECH})
        self.a['modifiers'][hull.QUALIFIED] = -1
        self.p = self.w.planets['P']
        self.p['buildings'].add(YARD)
        self.p['modifiers'].update(acs_segmented_project=-1, acs_segmented_operational=-1)
        self.w.targets['acs_owner@P'] = self.w.ref(self.a)
        self.port = dict(kind='starbase', size='starbase_citadel', owner='A')

    def test_research_and_country_qualification_are_both_required(self):
        self.assertTrue(self.w.may_order(self.port))
        before = deepcopy((self.a, self.p))
        self.a['techs'].remove(TECH)
        self.assertFalse(self.w.may_order(self.port))
        self.a['techs'].add(TECH)
        self.a['modifiers'].pop(hull.QUALIFIED)
        self.assertFalse(self.w.may_order(self.port))
        self.assertFalse(any(self.w.may_fit(p) for p in PARTS.values()))
        self.a['modifiers'][hull.QUALIFIED] = -1
        self.a['species'] = 'HUM'
        self.assertFalse(self.w.may_order(self.port))
        self.a['species'] = 'ARTIFACT_USER'
        self.a['bio'] = True
        self.assertFalse(self.w.may_order(self.port))
        self.a.pop('bio')
        self.assertEqual((self.a, self.p), before)

    def test_industry_loss_and_transfer_block_new_orders_but_keep_known_core_design(self):
        self.assertTrue(self.w.may_order(self.port))
        for key, bad in [('controller', 'B'), ('bombarded', True), ('inactive', {YARD}),
                         ('buildings', self.p['buildings'] - {YARD})]:
            with self.subTest(key=key):
                old = deepcopy(self.p[key])
                self.p[key] = bad
                self.assertFalse(self.w.may_order(self.port))
                self.assertTrue(self.w.may_fit(PARTS['ARTIFACT_STRATEGIC_REACTOR']))
                self.p[key] = old
                self.assertTrue(self.w.may_order(self.port))
        self.p.update(owner='B', controller='B')
        self.b['techs'].update(self.a['techs'])
        self.b['modifiers'][hull.QUALIFIED] = -1
        self.assertFalse(self.w.may_order(self.port))
        self.assertFalse(self.w.may_order({**self.port, 'owner': 'B'}))
        self.assertIn(hull.QUALIFIED, self.a['modifiers'])
        self.assertTrue(self.w.may_fit(PARTS['ARTIFACT_STRATEGIC_REACTOR']))

    def test_only_completed_capital_yards_and_megashipyards_accept_orders(self):
        for level in ('starbase_starport', 'starbase_starhold', 'starbase_starfortress'):
            self.assertFalse(self.w.may_order({**self.port, 'size': level}))
        for kind in ('mega_shipyard_0', 'mega_shipyard_1', 'mega_shipyard_2'):
            self.assertFalse(self.w.may_order(dict(kind='megastructure', type=kind, owner='A')))
        for kind in ('mega_shipyard_3', 'mega_shipyard_restored'):
            self.assertTrue(self.w.may_order(dict(kind='megastructure', type=kind, owner='A')))
        self.a['modifiers'].clear()
        self.assertFalse(self.w.may_order(dict(kind='megastructure', type='mega_shipyard_3', owner='A')))

    def test_base_cores_work_without_optional_research_and_upgrades_keep_their_gates(self):
        ready = {k for k, p in PARTS.items() if self.w.may_fit(p)}
        self.assertEqual(ready, {'ARTIFACT_STRATEGIC_REACTOR', 'ARTIFACT_STRATEGIC_THRUSTER',
                                'ARTIFACT_STRATEGIC_COMPUTER_ARTILLERY', 'ARTIFACT_STRATEGIC_COMPUTER_CARRIER'})
        self.assertEqual({scalar(PARTS[k], 'component_set') for k in ready},
                         {'power_core', 'thruster_components', 'combat_computers'})
        for key, research in [('ARTIFACT_STRATEGIC_TERMINAL_REACTOR', hull.BRANCHES['reactor']),
                              ('ARTIFACT_STRATEGIC_TERMINAL_THRUSTER', hull.BRANCHES['thruster']),
                              ('ARTIFACT_TERMINAL_HYPER_DRIVE', hull.BRANCHES['ftl'])]:
            body = PARTS[key] if key in PARTS else SHARED[key]
            self.assertFalse(self.w.may_fit(body))
            self.a['techs'].add(research)
            self.assertTrue(self.w.may_fit(body))
            self.a['techs'].remove(research)
            self.assertFalse(self.w.may_fit(body))

    def test_explicit_adaptation_preserves_native_roles_and_excludes_personal_hulls(self):
        self.a['techs'].update({*hull.BRANCHES.values(), 'tech_artifact_joint_combat_core'})
        for role in ('ARTILLERY', 'CARRIER'):
            part = SHARED['ARTIFACT_JOINT_COMPUTER_' + role]
            helper = 'ship_uses_' + role.lower() + '_role'
            self.assertTrue(self.w.may_fit(part))
            self.assertTrue(self.w.may_fit(part, 'battleship', native_roles={helper}))
            self.assertFalse(self.w.may_fit(part, 'aemusa_reality_flagship'))
            self.assertFalse(self.w.may_fit(part, 'destiny_lord'))
        for key in ('ARTIFACT_TERMINAL_LOAD_FRAME', 'ARTIFACT_TERMINAL_HYPER_DRIVE'):
            self.assertTrue(self.w.may_fit(SHARED[key]))
            for size in ('aemusa_reality_flagship', 'destiny_lord', 'science'):
                self.assertFalse(self.w.may_fit(SHARED[key], size))
        for part in PARTS.values():
            self.assertTrue(self.w.may_fit(part))
            self.assertFalse(self.w.may_fit(part, 'battleship'))
            self.assertFalse(self.w.may_fit(part, 'destiny_lord'))


if __name__ == '__main__':
    unittest.main()
