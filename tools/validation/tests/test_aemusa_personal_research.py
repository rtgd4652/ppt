"""回放真实终章和已有 R1 项目，核对 P01 资格、只读比较、门槛及实际扣费。"""
from copy import deepcopy
import re
import unittest
from unittest.mock import patch

import test_artifact_foundation_projects as workshop
import test_milestone2_finale_state as finale
from check_mod import parse, scalar

ROOT, child = workshop.ROOT, workshop.child
TECH = 'tech_aemusa_possibility_branch_modeling'
TECHNOLOGY = workshop.load('mod/common/technology/aemusa_personal_research_technology.txt')[TECH]
PERSONAL = workshop.load('mod/common/scripted_triggers/aemusa_personal_research_triggers.txt')
SCREEN = 'artifact_foundation.21'
STATUS = {
    scalar(e.value, 'name'): e.value for e in parse(
        (ROOT / 'mod/common/scripted_loc/aemusa_personal_branch_model_loc.txt').read_text(encoding='utf-8'))
}
NAMES = {
    'basic_construction': 'GetAemusaBasicConstructionAvailability',
    'precision_construction': 'GetAemusaPrecisionConstructionAvailability',
    'materials_study': 'GetAemusaMaterialsStudyAvailability',
}


def accepted():
    ledger = finale.reach_player_choice()
    finale.step(ledger, 72, 'authorize')
    ledger.open('aemusa_finale.75')
    finale.step(ledger, 80, 'listen')
    for number in (90, 120, 130):
        finale.step(ledger, number)
    return ledger


def option(event, name):
    return next(e.value for e in workshop.EVENTS[event] if e.key == 'option' and scalar(e.value, 'name') == name)


class Workshop(workshop.World):
    def __init__(self, ledger):
        super().__init__()
        self.ledger = ledger
        self.a = self.countries['A']
        self.p = self.planets['P']
        self.a['techs'].add(TECH)

    def term(self, entry, obj, ctx, prev):
        if entry.key == 'aemusa_personal_research_eligible':
            # 只有 A 拥有本例的真实故事账本；新主人即使持有科技也不继承原主人的历史。
            result = obj is self.a and self.ledger.condition(PERSONAL[entry.key])
            return result == (entry.value == 'yes')
        return super().term(entry, obj, ctx, prev)

    def select(self, event, name, ctx):
        button = option(event, name)
        if not self.condition(child(button, 'trigger', []), self.p, ctx):
            return False
        self.execute(child(button, 'hidden_effect', []), self.p, ctx)
        return True

    def possible(self, mode, ctx):
        entry = STATUS[NAMES[mode]]
        assert scalar(entry, 'random') == 'no' and scalar(entry, 'default') == 'aemusa_p01.unavailable'
        indicator = child(entry, 'text')
        assert scalar(indicator, 'localization_key') == 'aemusa_p01.ready'
        return self.condition(child(indicator, 'trigger'), self.p, ctx)


class PersonalResearchTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(finale.TRIGGERS, PERSONAL))

    def test_research_opens_at_formal_story_closure_and_survives_epilogue(self):
        gate = child(TECHNOLOGY, 'potential')
        ledger = accepted()
        self.assertFalse(ledger.condition(gate))
        finale.step(ledger, 140)
        finale.step(ledger, 150)
        self.assertTrue(ledger.condition(gate))
        for number in (160, 170, 180):
            finale.step(ledger, number)
        self.assertTrue(ledger.condition(gate))
        for flag in ('aemusa_ms_decision_player_authorized', 'aemusa_ms_decision_aemusa_accepted',
                     'aemusa_ms_country_settlement_fate_sovereign_done', 'aemusa_ms_country_fate_sovereign_authority_active',
                     'aemusa_ms_country_ending_fate_sovereign_settled', 'aemusa_ms_country_settlement_chapter_16_done'):
            ledger.flags.remove(flag)
            self.assertFalse(ledger.condition(gate), flag)
            ledger.flags.add(flag)

    def test_both_formal_refusals_and_pre_authorization_stay_outside_the_personal_route(self):
        gate = child(TECHNOLOGY, 'potential')
        for ending in ('player_refusal', 'aemusa_refusal'):
            ledger = finale.reach_player_choice('certainty' if ending == 'aemusa_refusal' else 'possibilities')
            self.assertFalse(ledger.condition(gate))
            if ending == 'player_refusal':
                finale.step(ledger, 71, 'refuse')
                finale.step(ledger, 100, 'accept')
            else:
                finale.step(ledger, 72, 'authorize')
                ledger.open('aemusa_finale.75')
                finale.step(ledger, 110, 'accept')
            self.assertFalse(ledger.condition(gate))
            self.assertEqual(finale.route(ledger), 'aemusa_finale.200')

    def workshop(self):
        ledger = accepted()
        finale.step(ledger, 140)
        finale.step(ledger, 150)
        return Workshop(ledger)

    def test_existing_window_can_compare_return_and_charge_the_original_branch_once(self):
        w = self.workshop()
        ctx = w.open('workshop')
        before = deepcopy((w.countries, w.planets, w.targets))
        for _ in range(2):
            self.assertTrue(w.select('artifact_foundation.20', 'aemusa_p01.open', ctx))
            self.assertEqual(w.last_event, SCREEN)
            self.assertTrue(all(w.possible(mode, ctx) for mode in NAMES))
            self.assertTrue(w.select(SCREEN, 'aemusa_p01.back', ctx))
            self.assertEqual(w.last_event, 'artifact_foundation.20')
        self.assertEqual(before, (w.countries, w.planets, w.targets))
        self.assertTrue(w.choose('precision_construction', ctx=ctx))
        paid = deepcopy(w.a['resources'])
        self.assertTrue(w.select('artifact_foundation.30', 'aemusa_p01.open', ctx))
        self.assertFalse(any(w.possible(mode, ctx) for mode in NAMES))
        self.assertTrue(w.select(SCREEN, 'aemusa_p01.back', ctx))
        self.assertEqual(w.last_event, 'artifact_foundation.30')
        self.assertFalse(w.choose('precision_construction', ctx=ctx))
        self.assertEqual(w.a['resources'], paid)

    def test_screen_tracks_actual_funding_research_site_and_owner(self):
        w = self.workshop()
        ctx = w.open('workshop')
        w.a['resources'].update(minerals=300, energy=150, consumer_goods=0, alloys=0)
        self.assertEqual([mode for mode in NAMES if w.possible(mode, ctx)], ['basic_construction'])
        w.a['techs'].discard('tech_artifact_modular_colony_construction')
        w.a['techs'].discard('tech_artifact_resonance_material_screening')
        self.assertIsNotNone(w.open('workshop'))
        self.assertFalse(any(w.possible(mode, ctx) for mode in NAMES))
        w.a['techs'].add('tech_artifact_modular_colony_construction')
        w.p['bombarded'] = True
        self.assertFalse(w.possible('basic_construction', ctx))
        w.p['bombarded'] = False
        w.p['buildings'].clear()
        self.assertFalse(w.possible('basic_construction', ctx))
        w.p['buildings'].add('building_artifact_relic_workshop')
        self.assertTrue(w.possible('basic_construction', ctx))
        w.a['species'] = 'HUM'
        archived = w.open('workshop')
        self.assertEqual(w.last_event, SCREEN)
        self.assertFalse(any(w.possible(mode, archived) for mode in NAMES))
        self.assertFalse(w.select(SCREEN, 'aemusa_p01.back', archived))
        self.assertFalse(w.choose('basic_construction', ctx=archived))
        w.a['species'] = 'ARTIFACT_USER'
        w.p['owner'] = w.p['controller'] = 'B'
        w.countries['B']['techs'].add(TECH)
        self.assertFalse(w.dispatch(SCREEN, w.p, ctx))
        self.assertFalse(w.possible('basic_construction', ctx))
        self.assertFalse(w.select('artifact_foundation.20', 'aemusa_p01.open', w.open('workshop')))

    def test_displayed_cost_matches_actual_cost_at_exact_and_one_short_balances(self):
        files = ('artifact_foundation_projects_l_simp_chinese.yml', 'aemusa_personal_research_l_simp_chinese.yml')
        strings = {}
        for name in files:
            text = (ROOT/'mod/localisation/simp_chinese'/name).read_text(encoding='utf-8-sig')
            strings.update(re.findall(r'^\s*([\w.]+):\d*\s+"(.*)"', text, re.M))
        resource_names = {'矿物': 'minerals', '能源': 'energy', '合金': 'alloys', '消费品': 'consumer_goods'}
        for mode in NAMES:
            offer = 'artifact_foundation.offer_' + mode
            self.assertIn('$' + offer + '$', strings['aemusa_p01.compare'])
            self.assertIn('[Root.' + NAMES[mode] + ']', strings['aemusa_p01.compare'])
            cost_key = re.search(r'\$(artifact_foundation\.cost_\w+)\$', strings[offer])[1]
            displayed = {resource_names[label]: workshop.WORKSHOP_COSTS[name] for name, label in
                         re.findall(r'\$@(\w+)\$(矿物|能源|合金|消费品)', strings[cost_key])}
            self.assertEqual(displayed, workshop.MODE_SPECS[mode]['cost'])
            w = self.workshop()
            w.a['resources'].update(displayed)
            ctx = w.open('workshop')
            for resource in displayed:
                w.a['resources'][resource] -= 1
                self.assertFalse(w.possible(mode, ctx))
                self.assertFalse(w.choose(mode, ctx=ctx))
                w.a['resources'][resource] += 1
            self.assertTrue(w.possible(mode, ctx))
            before = dict(w.a['resources'])
            self.assertTrue(w.choose(mode, ctx=ctx))
            self.assertEqual({key: before[key] - now for key, now in w.a['resources'].items() if now != before[key]},
                             displayed)


if __name__ == '__main__':
    unittest.main()
