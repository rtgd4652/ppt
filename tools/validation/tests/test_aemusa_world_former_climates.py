"""执行 P04 行星决议、绑定报价及原 F08 结算；只为引擎的调用国家、窗口和库存提供叶接口。"""
from copy import deepcopy
import re
import unittest
from unittest.mock import patch

import test_aemusa_personal_research as personal
import test_artifact_postcrisis_megastructure as shared
from test_postcrisis_handover import displayed
from check_mod import parse, scalar

ROOT, child = shared.ROOT, shared.child
TECH = 'tech_aemusa_possibility_engineering_interface'
EVENT_ID = 'aemusa_personal_climate.1'
PRICES = {e.key: int(e.value) for e in parse(
    (ROOT / 'mod/common/scripted_variables/aemusa_personal_world_former_costs.txt').read_text(encoding='utf-8'))}


def load(path):
    text = (ROOT / path).read_text(encoding='utf-8')
    text = re.sub(r'@apm_p04_\w+', lambda m: str(PRICES[m[0]]), text)
    text = re.sub(r'\bamount\s*>=', 'amount_ge =', text)
    return {e.key: e.value for e in parse(text)}


TECHNOLOGY = load('mod/common/technology/aemusa_personal_research_technology.txt')[TECH]
DECISION = load('mod/common/decisions/aemusa_personal_world_former_decisions.txt')['decision_aemusa_choose_world_former_climate']
TRIGGERS = load('mod/common/scripted_triggers/aemusa_personal_world_former_triggers.txt')
EFFECTS = load('mod/common/scripted_effects/aemusa_personal_world_former_effects.txt')
EVENT = shared.calibration.events('mod/events/aemusa_personal_climate_events.txt')[EVENT_ID]


class World(shared.World):
    def __init__(self, history):
        super().__init__()
        self.issued = []
        self.histories = {self.a['id']: history}
        self.a['techs'].update({personal.TECH, TECH})
        for c in self.countries.values():
            c['resources'].update(energy=9000, rare_crystals=900, exotic_gases=900)

    def resolve(self, path, stack):
        obj = super().resolve(path, stack)
        # 原巨构已毁时，旧事件本地目标过期，即使同名新实体建在同一星球。
        if obj and obj['kind'] == 'megastructure' and not any(obj is m for m in self.megas):
            return None
        return obj

    def term(self, e, stack):
        if e.key == 'aemusa_personal_research_eligible':
            history = self.histories.get(stack[-1]['id'])
            legitimate = history is not None and history.condition(personal.PERSONAL[e.key])
            return legitimate == (e.value == 'yes')
        if e.key == 'has_resource':
            return stack[-1]['resources'][scalar(e.value, 'type')] >= float(scalar(e.value, 'amount_ge'))
        return super().term(e, stack)

    def execute(self, entries, stack):
        if not any(e.key in ('from', 'solar_system', 'add_resource', 'country_event') for e in entries):
            return super().execute(entries, stack)
        for e in entries:
            if e.key in ('from', 'solar_system'):
                self.execute(e.value, stack + [self.resolve(e.key, stack)])
            elif e.key == 'add_resource':
                assert stack[-1]['kind'] == 'country'
                multiplier = float(scalar(e.value, 'mult') or 1)
                for value in e.value:
                    if value.key != 'mult':
                        stack[-1]['resources'][value.key] += multiplier * float(value.value)
            elif e.key == 'country_event':
                self.issued.append((scalar(e.value, 'id'), stack[-1], dict(self.local)))
            else:
                super().execute([e], stack)

    def quote(self, world, applicant=None):
        self.native_from = self.a if applicant is None else applicant
        self.local = {}
        if not self.condition(child(DECISION, 'potential'), [world]):
            return None
        self.execute(child(DECISION, 'effect'), [world])
        event, actor, targets = self.issued.pop()
        assert event == EVENT_ID and self.condition(child(EVENT, 'trigger'), [actor])
        return actor, targets

    def choose(self, quote, name):
        actor, self.local = quote
        button = next(e.value for e in EVENT if e.key == 'option' and scalar(e.value, 'name') == 'aemusa_p04.' + name)
        if not self.condition(child(button, 'allow', []), [actor]):
            return False
        self.execute(child(button, 'hidden_effect', []), [actor])
        return True

    def add_second_platform(self):
        target = self.add_planet('Other', system='S')
        target.update({k: deepcopy(self.target[k]) for k in
                       ('owner', 'controller', 'colony', 'pc', 'size', 'deposits', 'flags', 'moon', 'anomaly',
                        'terraforming', 'colonizing', 'surveyed')})
        other = dict(self.mega, id='DifferentPlatform', planet=target, solar_system=self.systems['S'], flags=set())
        self.megas.append(other)
        return target, other


class ClimateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = personal.accepted()
        personal.finale.step(cls.history, 140)
        personal.finale.step(cls.history, 150)

    def setUp(self):
        self.enterContext(patch.dict(personal.finale.TRIGGERS, personal.PERSONAL))
        self.enterContext(patch.dict(shared.TRIGGERS, {**personal.PERSONAL, **TRIGGERS}))
        self.enterContext(patch.dict(shared.EFFECTS, EFFECTS))
        self.w = World(self.history)

    def test_decision_preview_does_not_dereference_an_uncaptured_planet(self):
        w = self.w
        action = child(child(child(DECISION, 'effect'), 'hidden_effect'), 'if')
        selection = child(child(child(action, 'from'), 'random_owned_megastructure'), 'limit')
        native_term = w.term

        def reject_missing_target(entry, stack):
            # 对应实机悬停时的Undefined event target；exists查询自身仍允许返回False。
            if entry.key == 'is_same_value' and entry.value == 'event_target:apm_p04_planet':
                self.assertIsNotNone(w.resolve(entry.value, stack), '预览解引用了尚未捕获的星球')
            return native_term(entry, stack)

        with patch.object(w, 'term', side_effect=reject_missing_target):
            self.assertFalse(w.condition(selection, [w.target, w.a, w.mega]))
            w.local['apm_p04_planet'] = w.target
            self.assertTrue(w.condition(selection, [w.target, w.a, w.mega]))
            other, _ = w.add_second_platform()
            w.local['apm_p04_planet'] = other
            self.assertFalse(w.condition(selection, [w.target, w.a, w.mega]))

    def test_personal_technology_and_public_knowledge_are_both_required_for_the_decision(self):
        self.assertEqual(scalar(TECHNOLOGY, 'area'), 'physics')
        self.assertEqual(scalar(TECHNOLOGY, 'tier'), '5')
        self.assertEqual([e.value for e in child(TECHNOLOGY, 'prerequisites')], [personal.TECH])
        self.assertTrue(self.history.condition(child(TECHNOLOGY, 'potential')))
        self.assertFalse(personal.accepted().condition(child(TECHNOLOGY, 'potential')))
        w = self.w
        self.assertEqual(displayed('WorldFormer', lambda conditions: w.condition(conditions, [w.a])),
                         'aemusa_p04.handover_ready')
        for tech in (personal.TECH, TECH, shared.F06, shared.TECH):
            w.a['techs'].remove(tech)
            self.assertIsNone(w.quote(w.target))
            w.a['techs'].add(tech)
        w.a['modifiers'].pop(shared.RECORD)
        self.assertIsNone(w.quote(w.target))
        w.a['modifiers'][shared.RECORD] = -1
        refusal = personal.finale.reach_player_choice()
        personal.finale.step(refusal, 71, 'refuse')
        personal.finale.step(refusal, 100, 'accept')
        w.histories[w.a['id']] = refusal
        self.assertIsNone(w.quote(w.target))
        self.assertEqual(displayed('WorldFormer', lambda conditions: w.condition(conditions, [w.a])),
                         'aph.handover.platform_ready')
        before = dict(w.a['resources'])
        self.assertTrue(w.use())
        self.assertEqual(w.target['pc'], 'pc_continental')
        self.assertEqual(w.a['resources'], before)

    def test_dry_and_cold_results_charge_exactly_once_with_original_platform_receipts(self):
        cases = [('arid', 'rare_crystals', {'d_searing_desert', 'd_ore_rich_caverns', 'd_marvelous_oasis'}),
                 ('arctic', 'exotic_gases', {'d_geothermal_vent', 'd_rich_mountain', 'd_lichen_fields'})]
        for climate, material, terrain in cases:
            with self.subTest(climate=climate):
                w = World(self.history)
                w.target['flags'].update({'apm_platform_site', 'has_megastructure', 'unrelated'})
                w.a['resources'].update(energy=1500)
                w.a['resources'][material] = 100
                before = dict(w.a['resources'])
                first = w.quote(w.target)
                stale = w.quote(w.target)
                self.assertEqual(w.a['resources'], before)
                for key in ('energy', material):
                    w.a['resources'][key] -= 1
                    balance = dict(w.a['resources'])
                    self.assertFalse(w.choose(first, climate))
                    w.execute(EFFECTS['aemusa_p04_form_' + climate + '_world'], [w.a])
                    self.assertEqual(w.a['resources'], balance)
                    self.assertEqual(w.target['pc'], 'pc_barren')
                    w.a['resources'][key] += 1
                self.assertTrue(w.choose(first, climate))
                self.assertEqual(w.a['resources'], dict(before, energy=0, **{material: 0}))
                self.assertEqual((w.target['pc'], w.target['deposits']), ('pc_' + climate, terrain))
                self.assertEqual(w.target['flags'], {'apm_world_formed', 'unrelated'})
                self.assertIn('apm_world_formed', w.mega['flags'])
                self.assertIsNone(w.target['owner'])
                self.assertFalse(w.target['colony'])
                self.assertFalse(w.choose(stale, 'arctic' if climate == 'arid' else 'arid'))
                self.assertFalse(w.use())

    def test_multiple_owned_platforms_remain_bound_to_the_world_each_window_named(self):
        w = self.w
        second_world, second_platform = w.add_second_platform()
        first = w.quote(w.target)
        second = w.quote(second_world)
        self.assertIs(second[1]['apm_p04_planet'], second_world)
        self.assertIs(second[1]['apm_p04_platform'], second_platform)
        self.assertEqual(scalar(EVENT, 'location'), 'event_target:apm_p04_planet')
        self.assertTrue(w.choose(second, 'arctic'))
        self.assertEqual(w.target['pc'], 'pc_barren')
        self.assertEqual(w.mega['flags'], set())
        self.assertTrue(w.choose(first, 'arid'))
        self.assertEqual(second_world['pc'], 'pc_arctic')

    def test_stale_or_foreign_quotes_do_not_charge_or_select_another_valid_platform(self):
        for change in ('occupation', 'ownership', 'base_only', 'replaced', 'moved', 'other_system',
                       'deposit', 'old_anchor', 'no_knowledge'):
            with self.subTest(change=change):
                w = World(self.history)
                other, _ = w.add_second_platform()
                quote = w.quote(w.target)
                before = dict(w.a['resources'])
                if change == 'occupation':
                    w.systems['T']['starbase']['controller'] = w.countries['B']
                elif change == 'ownership':
                    w.mega['owner'] = w.countries['B']
                elif change == 'base_only':
                    w.mega['type'] = shared.BASE
                elif change == 'replaced':
                    w.megas[0] = dict(w.mega, flags=set())
                elif change == 'moved':
                    w.mega['planet'] = other
                elif change == 'other_system':
                    w.mega['solar_system'] = w.target['solar_system'] = w.systems['S']
                elif change == 'deposit':
                    w.target['deposits'].add('some_later_deposit')
                elif change == 'old_anchor':
                    w.target['flags'].add('aemusa_ms_anchor_used')
                else:
                    w.a['techs'].discard(TECH)
                self.assertFalse(w.choose(quote, 'arid'))
                w.execute(EFFECTS['aemusa_p04_form_arid_world'], [w.a])
                self.assertEqual(w.a['resources'], before)
                self.assertEqual((w.target['pc'], other['pc']), ('pc_barren', 'pc_barren'))

    def test_free_activation_wins_over_an_older_paid_quote_and_cancel_has_no_effect(self):
        w = self.w
        quote = w.quote(w.target)
        before = dict(w.a['resources'])
        self.assertTrue(w.choose(quote, 'close'))
        self.assertFalse(w.target['flags'])
        self.assertEqual(w.a['resources'], before)
        quote = w.quote(w.target)
        self.assertTrue(w.use())
        self.assertFalse(w.choose(quote, 'arctic'))
        self.assertEqual(w.a['resources'], before)
        self.assertEqual(w.target['deposits'], {'d_rushing_waterfalls', 'd_rich_mountain', 'd_fertile_lands'})

    def test_transfer_requires_the_new_owners_own_quote_and_only_charges_that_owner(self):
        w = self.w
        before = dict(w.a['resources'])
        _, previous = w.quote(w.target)
        new = w.countries['B']
        w.mega['owner'] = w.systems['T']['owner'] = new
        w.systems['T']['starbase']['owner'] = w.systems['T']['starbase']['controller'] = new
        self.assertIsNone(w.quote(w.target, new))
        new['flags'].update(shared.VICTORY)
        new['techs'].update({TECH, personal.TECH})
        new['modifiers'][shared.RECORD] = -1
        w.histories[new['id']] = self.history
        balance = dict(new['resources'])
        self.assertFalse(w.choose((new, previous), 'arid'))
        self.assertFalse(w.choose((w.a, previous), 'arid'))
        self.assertEqual(new['resources'], balance)
        self.assertTrue(w.choose(w.quote(w.target, new), 'arid'))
        self.assertEqual(w.a['resources'], before)
        self.assertEqual(new['resources']['energy'], balance['energy'] - 1500)
        self.assertEqual(new['resources']['rare_crystals'], balance['rare_crystals'] - 100)


if __name__ == '__main__':
    unittest.main()
