"""用原工坊及真实终章账本核对在途改选。弹窗登记按原生 has_active_event 的国家作用域建模。"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_aemusa_personal_research as personal
import test_artifact_foundation_projects as workshop
from check_mod import scalar

child = workshop.child
QUOTE = 'artifact_foundation.22'
STATUS = 'artifact_foundation.30'
TECH = 'tech_aemusa_selected_plan_reconfiguration'
BASIC, PRECISION = 'basic_construction', 'precision_construction'
PROGRESS, WORK = 'arf_r1_progress', 'arf_r1_required_work'
PENDING, CHANGED = 'arf_p02_quote_open', 'arf_p02_replanned'
TECHNOLOGY = workshop.load('mod/common/technology/aemusa_personal_research_technology.txt')[TECH]
EFFECTS = workshop.load('mod/common/scripted_effects/aemusa_personal_research_effects.txt')
VALUES = workshop.load('mod/common/script_values/aemusa_personal_workshop_values.txt')


class ReplanWorld(workshop.World):
    def __init__(self, story):
        super().__init__()
        self.a, self.b = self.countries['A'], self.countries['B']
        self.p = self.planets['P']
        self.histories = {'A': story}
        self.open_quotes = {}
        for country in self.countries.values():
            country['techs'].update({personal.TECH, TECH})
            country['resources']['unity'] = 500

    def number(self, value, obj):
        if isinstance(value, str) and value.startswith('value:'):
            definition = VALUES[value.removeprefix('value:')]
            assert [e.key for e in definition] == ['base', 'subtract', 'min']
            first, subtraction, lower_bound = [float(e.value) for e in definition]
            return max(lower_bound, first - subtraction)
        return super().number(value, obj)

    def term(self, e, obj, ctx, prev):
        if e.key == 'aemusa_personal_research_eligible':
            story = self.histories.get(obj['id'])
            allowed = story is not None and story.condition(personal.PERSONAL[e.key])
            return allowed == (e.value == 'yes')
        if e.key == 'has_active_event':
            assert obj['kind'] == 'country' and [x.value for x in e.value] == [QUOTE]
            return obj['id'] in self.open_quotes
        if e.key == 'is_variable_set':
            return e.value in obj['vars']
        if e.key == 'resource_stockpile_compare':
            resource = scalar(e.value, 'resource')
            return obj['resources'][resource] >= self.number(scalar(e.value, 'value_ge'), obj)
        if e.key == 'check_variable_arithmetic':
            remaining = self.number(scalar(e.value, 'which'), obj) - self.number(scalar(e.value, 'subtract'), obj)
            return remaining >= self.number(scalar(e.value, 'value_ge'), obj)
        return super().term(e, obj, ctx, prev)

    def dispatch(self, event, obj, ctx=None):
        opened = super().dispatch(event, obj, ctx)
        if opened and event == QUOTE:
            assert obj['owner'] not in self.open_quotes
            self.open_quotes[obj['owner']] = obj['id']
        return opened

    def click(self, event, name, planet, ctx):
        holder = ctx['arf_r1_ui_owner'][1]
        if event == QUOTE and self.open_quotes.get(holder) != planet['id']:
            return False
        button = personal.option(event, name)
        if not all(self.condition(child(button, part, []), planet, ctx) for part in ('trigger', 'allow')):
            return False
        self.execute(child(button, 'hidden_effect', []), planet, ctx)
        if event == QUOTE:
            self.execute(child(workshop.EVENTS[QUOTE], 'after'), planet, ctx)
            del self.open_quotes[holder]
        return True

    def review(self, planet='P'):
        ctx = self.open('workshop', planet)
        assert self.last_event == STATUS and self.click(STATUS, 'aemusa_p02.review', self.planets[planet], ctx)
        assert self.last_event == QUOTE
        return ctx

    def receipt(self, ctx):
        definition = personal.STATUS['GetAemusaConstructionPaid']
        assert scalar(definition, 'random') == 'no'
        for entry in definition:
            if entry.key == 'text' and self.condition(child(entry.value, 'trigger'), self.p, ctx):
                return scalar(entry.value, 'localization_key')
        return scalar(definition, 'default')


class ReconfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = personal.accepted()
        personal.finale.step(cls.story, 140)
        personal.finale.step(cls.story, 150)

    def setUp(self):
        self.enterContext(patch.dict(workshop.EFFECTS, EFFECTS))
        self.enterContext(patch.dict(personal.finale.TRIGGERS, personal.PERSONAL))
        self.w = ReplanWorld(self.story)

    def test_personal_research_and_authority_gate_only_live_construction(self):
        self.assertEqual(scalar(TECHNOLOGY, 'area'), 'society')
        self.assertEqual(scalar(TECHNOLOGY, 'tier'), '5')
        self.assertEqual([e.value for e in child(TECHNOLOGY, 'prerequisites')], [personal.TECH])
        self.assertTrue(self.story.condition(child(TECHNOLOGY, 'potential')))
        self.assertFalse(personal.accepted().condition(child(TECHNOLOGY, 'potential')))
        w = self.w
        self.assertTrue(w.choose('materials_study'))
        ctx = w.open('workshop')
        self.assertFalse(w.click(STATUS, 'aemusa_p02.review', w.p, ctx))
        w.execute(workshop.EFFECTS['artifact_foundation_abort'], w.p, ctx)
        self.assertTrue(w.choose(BASIC))
        ctx = w.open('workshop')
        for technology in (personal.TECH, TECH):
            w.a['techs'].remove(technology)
            self.assertFalse(w.click(STATUS, 'aemusa_p02.review', w.p, ctx))
            w.a['techs'].add(technology)
        w.histories.clear()
        self.assertFalse(w.click(STATUS, 'aemusa_p02.review', w.p, ctx))

    def test_upgrade_pays_difference_keeps_work_and_only_the_original_monthly_event_finishes(self):
        w = self.w
        initial = dict(w.a['resources'])
        # 旧存档可以在普通工程已经付费、已做工后才取得 P02。
        w.a['techs'].remove(TECH)
        self.assertTrue(w.choose(BASIC))
        w.monthly()
        w.monthly()
        w.a['techs'].add(TECH)
        unissued = w.open('workshop')
        self.assertFalse(w.dispatch(QUOTE, w.p, unissued))
        before = deepcopy((w.a['resources'], w.p['vars'], w.targets))
        ctx = w.review()
        self.assertEqual(before, (w.a['resources'], w.p['vars'], w.targets))
        self.assertEqual(w.receipt(ctx), 'artifact_foundation.cost_basic')
        self.assertTrue(w.click(QUOTE, 'aemusa_p02.upgrade', w.p, ctx))
        self.assertEqual(w.p['vars'][PROGRESS], 2)
        self.assertEqual(w.p['vars'][WORK], 4)
        self.assertIn('arf_r1_paid', w.p['flags'])
        self.assertIn(CHANGED, w.p['flags'])
        self.assertNotIn(PENDING, w.p['flags'])
        self.assertEqual(w.receipt(ctx), 'aemusa_p02.replanned_paid')
        self.assertEqual({k: initial[k] - v for k, v in w.a['resources'].items() if v != initial[k]},
                         {'minerals': 450, 'energy': 200, 'alloys': 50, 'unity': 50})
        w = deepcopy(w)  # 回放存留的项目状态，实机读档另验。
        paid = dict(w.a['resources'])
        for mode in ('upgrade', 'simplify'):
            w.execute(EFFECTS['aemusa_p02_' + mode + '_construction'], w.p, ctx)
        self.assertEqual(paid, w.a['resources'])
        self.assertFalse(w.click(STATUS, 'aemusa_p02.review', w.p, ctx))
        self.assertFalse(w.p['modifiers'])
        w.monthly()
        self.assertFalse(w.p['modifiers'])
        w.monthly()
        self.assertEqual(w.p['modifiers'], {'artifact_foundation_precision_construction': 720})
        w.monthly()
        self.assertEqual(w.a['resources'], paid)
        self.assertEqual(w.p['modifiers'], {'artifact_foundation_precision_construction': 720})

    def test_simplification_never_refunds_or_finishes_while_the_order_is_open(self):
        for finished in range(4):
            with self.subTest(finished=finished):
                w = ReplanWorld(self.story)
                self.assertTrue(w.choose(PRECISION))
                for _ in range(finished):
                    w.monthly()
                paid = dict(w.a['resources'])
                ctx = w.review()
                self.assertEqual(w.receipt(ctx), 'artifact_foundation.cost_precision')
                self.assertTrue(w.click(QUOTE, 'aemusa_p02.simplify', w.p, ctx))
                self.assertEqual(w.receipt(ctx), 'aemusa_p02.replanned_paid')
                target = max(3, finished + 1)
                self.assertEqual((w.p['vars'][PROGRESS], w.p['vars'][WORK]), (finished, target))
                self.assertEqual(w.a['resources'], dict(paid, unity=paid['unity'] - 50))
                for _ in range(target - finished):
                    self.assertFalse(w.p['modifiers'])
                    w.monthly()
                self.assertEqual(w.p['modifiers'], {'artifact_foundation_basic_construction': 720})

    def test_confirmation_rechecks_every_cost_technology_and_actual_site(self):
        w = self.w
        self.assertTrue(w.choose(BASIC))
        ctx = w.review()
        due = {'minerals': 150, 'energy': 50, 'alloys': 50, 'unity': 50}
        for resource, name in (('minerals', 'GetAemusaUpgradeMinerals'), ('energy', 'GetAemusaUpgradeEnergy')):
            self.assertEqual(w.number(scalar(personal.STATUS[name], 'value'), w.p), due[resource])
        w.a['resources'].update(due)
        for resource in due:
            w.a['resources'][resource] -= 1
            before = deepcopy((w.a['resources'], w.p))
            self.assertFalse(w.click(QUOTE, 'aemusa_p02.upgrade', w.p, ctx))
            w.execute(EFFECTS['aemusa_p02_upgrade_construction'], w.p, ctx)
            self.assertEqual((w.a['resources'], w.p), before)
            w.a['resources'][resource] += 1
        for field, blocked in (('controller', 'B'), ('bombarded', True), ('buildings', set())):
            original = w.p[field]
            w.p[field] = blocked
            self.assertFalse(w.click(QUOTE, 'aemusa_p02.upgrade', w.p, ctx))
            w.p[field] = original
        w.a['techs'].remove('tech_artifact_resonance_material_screening')
        self.assertFalse(w.click(QUOTE, 'aemusa_p02.upgrade', w.p, ctx))
        w.a['techs'].add('tech_artifact_resonance_material_screening')
        self.assertTrue(w.click(QUOTE, 'aemusa_p02.upgrade', w.p, ctx))
        self.assertTrue(all(w.a['resources'][r] == 0 for r in due))

    def test_quote_expires_when_the_promised_month_of_earlier_delivery_disappears(self):
        w = self.w
        self.assertTrue(w.choose(PRECISION))
        w.monthly()
        w.monthly()
        quote = w.review()
        paid = dict(w.a['resources'])
        w.monthly()
        self.assertFalse(w.click(QUOTE, 'aemusa_p02.simplify', w.p, quote))
        self.assertEqual(paid, w.a['resources'])
        self.assertTrue(w.click(QUOTE, 'aemusa_p02.close', w.p, quote))
        fresh = w.review()
        self.assertTrue(w.click(QUOTE, 'aemusa_p02.simplify', w.p, fresh))
        self.assertEqual((w.p['vars'][PROGRESS], w.p['vars'][WORK]), (3, 4))

    def test_stale_quote_cannot_commit_a_new_project_of_the_same_type(self):
        w = self.w
        self.assertTrue(w.choose(BASIC))
        abandoned = w.review()
        w.execute(workshop.EFFECTS['artifact_foundation_abort'], w.p, abandoned)
        self.assertTrue(w.choose(BASIC))
        fresh = w.open('workshop')
        before = deepcopy((w.a['resources'], w.p))
        self.assertFalse(w.click(STATUS, 'aemusa_p02.review', w.p, fresh))
        self.assertFalse(w.click(QUOTE, 'aemusa_p02.upgrade', w.p, abandoned))
        w.execute(EFFECTS['aemusa_p02_upgrade_construction'], w.p, abandoned)
        self.assertEqual((w.a['resources'], w.p), before)
        self.assertTrue(w.click(QUOTE, 'aemusa_p02.close', w.p, abandoned))
        self.assertTrue(w.click(STATUS, 'aemusa_p02.review', w.p, fresh))
        for _ in range(4):
            w.monthly()
        self.assertFalse(w.click(QUOTE, 'aemusa_p02.upgrade', w.p, fresh))
        self.assertEqual(w.p['modifiers'], {'artifact_foundation_basic_construction': 720})

    def test_old_owner_cannot_charge_or_cancel_an_independent_new_owners_order(self):
        w = self.w
        self.assertTrue(w.choose(BASIC))
        old = w.review()
        w.p['owner'] = w.p['controller'] = 'B'
        w.dispatch('artifact_foundation.2', w.p)
        w.histories['B'] = deepcopy(self.story)
        self.assertTrue(w.choose(BASIC))
        new = w.review()
        before = dict(w.b['resources'])
        self.assertFalse(w.click(QUOTE, 'aemusa_p02.upgrade', w.p, old))
        w.execute(EFFECTS['aemusa_p02_upgrade_construction'], w.p, old)
        self.assertTrue(w.click(QUOTE, 'aemusa_p02.close', w.p, old))
        self.assertEqual(before, w.b['resources'])
        self.assertIn(PENDING, w.p['flags'])
        self.assertTrue(w.click(QUOTE, 'aemusa_p02.upgrade', w.p, new))


if __name__ == '__main__':
    unittest.main()
