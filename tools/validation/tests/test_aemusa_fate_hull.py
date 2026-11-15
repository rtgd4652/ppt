"""读取P03正式脚本，回放终章资格与造舰边界；不把夹具当作原生设计器或排队验收。"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_strategic_hull as public
import test_aemusa_personal_research as personal
from check_mod import parse, scalar

foundation, finale = public.foundation, personal.finale
ROOT, child, load = foundation.ROOT, foundation.child, foundation.load
TECH = 'tech_aemusa_fate_hull_interface'
SIZE = 'aemusa_fate_escort'
TECHNOLOGY = load('mod/common/technology/aemusa_fate_hull_technology.txt')[TECH]
SHIP = load('mod/common/ship_sizes/aemusa_fate_escort.txt')[SIZE]
TRIGGERS = load('mod/common/scripted_triggers/aemusa_fate_hull_triggers.txt')
PARTS = public.components('aemusa_fate_escort_components.txt')
SECTIONS = {scalar(e.value, 'key'): e.value for e in parse(
    (ROOT / 'mod/common/section_templates/aemusa_fate_escort_sections.txt').read_text(encoding='utf-8'))}


def prerequisites_met(entries, known):
    # 同原版X舰首的OR列表，仅执行本包实际使用的研究依赖，不模拟自动配装评分。
    return all(any(x.value in known for x in e.value) if e.key == 'OR' else e.value in known
               for e in entries)


class World(public.World):
    def __init__(self, ledger):
        super().__init__()
        self.ledger = ledger

    def term(self, entry, obj, ctx, prev):
        if entry.key == 'aemusa_personal_research_eligible':
            result = obj is self.countries['A'] and self.ledger.condition(personal.PERSONAL[entry.key])
            return result == (entry.value == 'yes')
        return super().term(entry, obj, ctx, prev)

    def may_research(self):
        country = self.countries['A']
        return (prerequisites_met(child(TECHNOLOGY, 'prerequisites'), country['techs'])
                and self.condition(child(TECHNOLOGY, 'potential'), country, {}))

    def may_order(self, site):
        country = self.countries[site['owner']]
        return (prerequisites_met(child(SHIP, 'prerequisites'), country['techs'])
                and self.condition(child(SHIP, 'potential_country'), country, {})
                and self.condition(child(SHIP, 'potential_construction'), site, {})
                and self.condition(child(SHIP, 'possible_construction'), site, {}))

    def may_fit(self, body, size=SIZE, country='A', native_roles=()):
        return super().may_fit(body, size, country, native_roles)


class FateHullTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(finale.TRIGGERS, personal.PERSONAL))
        self.enterContext(patch.dict(foundation.TRIGGERS,
                                    {**public.supply.TRIGGERS, **public.TRIGGERS, **TRIGGERS}))
        ledger = personal.accepted()
        finale.step(ledger, 140)
        finale.step(ledger, 150)
        self.w = World(ledger)
        self.a, self.b = self.w.countries.values()
        self.a['techs'].update({TECH, personal.TECH, public.TECH, public.ENGINEERING, public.hull.TECH})
        self.a['modifiers'][public.hull.QUALIFIED] = -1
        self.p = self.w.planets['P']
        self.p['buildings'].add(public.YARD)
        self.p['modifiers'].update(acs_segmented_project=-1, acs_segmented_operational=-1)
        self.w.targets['acs_owner@P'] = self.w.ref(self.a)
        self.port = dict(kind='starbase', size='starbase_citadel', owner='A')

    def test_only_accepted_closed_story_with_p01_can_offer_research(self):
        self.assertTrue(self.w.may_research())
        self.a['techs'].remove(personal.TECH)
        self.assertFalse(self.w.may_research())
        self.a['techs'].add(personal.TECH)
        self.w.ledger = personal.accepted()
        self.assertFalse(self.w.may_research())
        for ending in ('player_refusal', 'aemusa_refusal'):
            ledger = finale.reach_player_choice('certainty' if ending == 'aemusa_refusal' else 'possibilities')
            if ending == 'player_refusal':
                finale.step(ledger, 71, 'refuse')
                finale.step(ledger, 100, 'accept')
            else:
                finale.step(ledger, 72, 'authorize')
                ledger.open('aemusa_finale.75')
                finale.step(ledger, 110, 'accept')
            self.w.ledger = ledger
            self.assertFalse(self.w.may_research(), ending)
            self.assertFalse(self.w.may_order(self.port), ending)

    def test_industry_and_public_qualification_gate_orders_not_existing_cores(self):
        before = deepcopy((self.a, self.p, self.w.ledger.flags))
        self.assertTrue(self.w.may_order(self.port))
        for key, bad in [('controller', 'B'), ('bombarded', True), ('inactive', {public.YARD}),
                         ('buildings', self.p['buildings'] - {public.YARD})]:
            with self.subTest(key=key):
                old = deepcopy(self.p[key])
                self.p[key] = bad
                self.assertFalse(self.w.may_order(self.port))
                self.assertTrue(all(self.w.may_fit(p) for p in PARTS.values()))
                self.p[key] = old
        for technology in (public.TECH,):
            self.a['techs'].remove(technology)
            self.assertFalse(self.w.may_order(self.port))
            self.assertTrue(all(self.w.may_fit(p) for p in PARTS.values()))
            self.a['techs'].add(technology)
        qualified = self.a['modifiers'].pop(public.hull.QUALIFIED)
        self.assertFalse(self.w.may_order(self.port))
        self.assertTrue(all(self.w.may_fit(p) for p in PARTS.values()))
        self.a['modifiers'][public.hull.QUALIFIED] = qualified
        self.assertEqual((self.a, self.p, self.w.ledger.flags), before)

    def test_yard_stage_is_checked_at_order_time(self):
        for level in ('starbase_starport', 'starbase_starhold', 'starbase_starfortress'):
            self.assertFalse(self.w.may_order({**self.port, 'size': level}))
        for stage in (0, 1, 2):
            self.assertFalse(self.w.may_order(dict(kind='megastructure', type=f'mega_shipyard_{stage}', owner='A')))
        for kind in ('mega_shipyard_3', 'mega_shipyard_restored'):
            self.assertTrue(self.w.may_order(dict(kind='megastructure', type=kind, owner='A')))

    def test_personal_cores_exclude_other_hulls_and_foreign_history(self):
        self.assertEqual({scalar(p, 'component_set') for p in PARTS.values()},
                         {e.value for e in SHIP if e.key == 'required_component_set'})
        self.assertTrue(all(self.w.may_fit(p) for p in PARTS.values()))
        for size in ('artifact_strategic_cruiser', 'battleship', 'aemusa_reality_flagship', 'destiny_lord'):
            self.assertFalse(any(self.w.may_fit(p, size) for p in PARTS.values()), size)
        self.b['techs'].update(self.a['techs'])
        self.assertFalse(any(self.w.may_fit(p, country='B') for p in PARTS.values()))
        self.a['bio'] = True
        self.assertFalse(self.w.may_order(self.port))
        self.assertFalse(any(self.w.may_fit(p) for p in PARTS.values()))

    def test_public_hull_does_not_depend_on_p03(self):
        self.a['techs'].remove(TECH)
        self.assertFalse(self.w.may_order(self.port))
        self.assertTrue(public.World.may_order(self.w, self.port))
        self.assertTrue(self.w.may_fit(public.PARTS['ARTIFACT_STRATEGIC_REACTOR'], public.SIZE))

    def test_regular_sections_exist_before_x_weapon_research(self):
        ready = [s for s in SECTIONS.values()
                 if prerequisites_met(child(s, 'prerequisites', []), self.a['techs'])]
        self.assertEqual({scalar(s, 'fits_on_slot') for s in ready}, {'bow', 'mid', 'stern'})
        self.assertEqual(len(ready), 3)
        self.assertEqual(sum(e.key == 'component_slot' for s in ready for e in s), 6)
        self.assertEqual(sum(int(scalar(s, 'large_utility_slots') or 0) for s in ready), 8)
        spinal = SECTIONS['AEMUSA_FATE_ESCORT_SPINAL_BOW']
        self.assertFalse(prerequisites_met(child(spinal, 'prerequisites'), self.a['techs']))
        self.a['techs'].add('tech_energy_lance_1')
        self.assertTrue(prerequisites_met(child(spinal, 'prerequisites'), self.a['techs']))
        for section in SECTIONS.values():
            self.assertEqual(scalar(section, 'ship_size'), SIZE)
            self.assertTrue(all('titanic' not in str(e.value) for e in section if e.key == 'component_slot'))


if __name__ == '__main__':
    unittest.main()
