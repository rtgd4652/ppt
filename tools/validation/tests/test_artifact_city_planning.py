"""读取R2d真实脚本检查当地付费与状态边界；不模拟原生回调、升级或存读档。"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_mod import parse, scalar

ROOT = Path(__file__).resolve().parents[3]
LOW = 'building_artifact_city_calculation_room'
HIGH = 'building_artifact_fate_calculus_institute'
CENTER = 'building_artifact_community_service_center'
TECH = 'tech_artifact_city_functional_zoning'
REFUGE = 'tech_artifact_refuge_organization'
PREFIX = 'artifact_city_plan_'


def load(path):
    return {e.key: e.value for e in parse((ROOT / path).read_text(encoding='utf-8-sig'))}


def block(entries, key):
    return next((e.value for e in entries if e.key == key), [])


BUILDINGS = load('mod/common/buildings/artifact_city_planning_buildings.txt')
BUILDINGS.update(load('mod/common/buildings/aemusa_buildings.txt'))
BUILDINGS.update(load('mod/common/buildings/artifact_public_foundation_buildings.txt'))
DECISIONS = load('mod/common/decisions/artifact_city_planning_decisions.txt')
MARKERS = load('mod/common/static_modifiers/artifact_city_planning_modifiers.txt')
EVENTS = load('mod/events/artifact_city_planning_events.txt')
ACTIONS = load('mod/common/on_actions/artifact_city_planning_on_actions.txt')
GARRISON_TRIGGERS = load('mod/common/scripted_triggers/artifact_garrison_triggers.txt')


def condition(entries, scope):
    # 严格区分国家与殖民地；未知语法立即失败，防止把未实现条件当作通过。
    def term(entry):
        key, value = entry.key, entry.value
        if key in GARRISON_TRIGGERS:
            return condition(GARRISON_TRIGGERS[key], scope) == (value == 'yes')
        if key in ('OR', 'NOR', 'NOT'):
            if key == 'NOT':
                assert len(value) == 1
            result = any(term(e) for e in value)
            return result if key == 'OR' else not result
        if key == 'custom_tooltip':
            return condition([e for e in value if e.key != 'fail_text'], scope)
        if key == 'owner':
            assert scope['kind'] in ('colony', 'planet')
            return condition(value, scope['owner'])
        if key == 'planet':
            # 建筑求值的殖民地索引不同于其承载行星；显式跳转才改变@this。
            assert scope['kind'] in ('colony', 'planet')
            carrier = scope if scope['kind'] == 'planet' else scope.get(
                'carrier', dict(scope, kind='planet'))
            return condition(value, carrier)
        if key == 'owner_main_species':
            assert scope['kind'] == 'country'
            return condition(value, scope)
        if key == 'is_species_class':
            assert scope['kind'] == 'country'
            return scope['species'] == value
        if key == 'has_technology':
            assert scope['kind'] == 'country'
            return value in scope['techs']
        assert scope['kind'] in ('colony', 'planet'), key
        if key == 'exists':
            if value == 'event_target:artifact_garrison_owner@this':
                return scope.get('garrison_owners', {}).get(
                    (scope['kind'], scope.get('scope_id'))) is not None
            assert value == 'owner'
            return scope['owner'] is not None
        if key == 'carrier_is_type':
            assert value == 'planet'
            return scope['kind'] in ('colony', 'planet')
        if key == 'has_carrier_flag':
            return value in scope.get('carrier_flags', set())
        if key == 'is_owned_by':
            assert value == 'event_target:artifact_garrison_owner@this'
            return scope['owner'] is scope.get('garrison_owners', {}).get(
                (scope['kind'], scope.get('scope_id')))
        if key == 'is_colony':
            return value == 'yes'
        if key == 'is_controlled_by':
            assert value == 'owner'
            return scope['controller'] is scope['owner']
        if key == 'has_modifier':
            return value in scope['markers']
        if key == 'has_orbital_bombardment':
            return scope['bombarded'] == (value == 'yes')
        if key == 'has_building_construction':
            return value in scope['queued']
        if key == 'has_building':
            return value in scope['buildings']
        if key == 'has_active_building':
            return value in scope['buildings'] - scope['inactive']
        raise AssertionError(('unsupported condition', key))
    return all(term(e) for e in entries)


def effect(entries, site):
    for entry in entries:
        if entry.key == 'add_modifier':
            assert scalar(entry.value, 'days') == '-1'
            site['markers'].add(scalar(entry.value, 'modifier'))
        elif entry.key == 'remove_modifier':
            site['markers'].discard(entry.value)
        else:
            raise AssertionError(('unsupported effect', entry.key))


class CityPlanningTests(unittest.TestCase):
    def setUp(self):
        self.country = dict(kind='country', species='ARTIFACT_USER', techs={TECH, REFUGE},
                            resources={'energy': 1000, 'unity': 400})
        self.site = dict(kind='colony', owner=self.country, controller=self.country,
                         buildings={LOW}, inactive=set(), queued=set(), markers=set(),
                         bombarded=False)

    def available(self, choice):
        decision = DECISIONS['decision_' + PREFIX + choice]
        return (condition(block(decision, 'potential'), self.site)
                and condition(block(decision, 'allow'), self.site))

    def choose(self, choice):
        if not self.available(choice):
            return False
        decision = DECISIONS['decision_' + PREFIX + choice]
        costs = block(block(decision, 'resources'), 'cost')
        if any(self.country['resources'][e.key] < float(e.value) for e in costs):
            return False
        for entry in costs:
            self.country['resources'][entry.key] -= float(entry.value)
        effect(block(decision, 'effect'), self.site)
        return True

    def bonus(self, modifier):
        return sum(float(scalar(entry.value, modifier) or 0)
                   for key in self.site['buildings'] - self.site['inactive']
                   for entry in BUILDINGS[key]
                   if entry.key == 'triggered_planet_modifier'
                   and condition(block(entry.value, 'potential'), self.site))

    def test_fee_exclusion_and_cancel_have_no_refund(self):
        self.assertTrue(self.choose('research'))
        self.assertEqual(self.country['resources'], {'energy': 700, 'unity': 300})
        for choice in ('research', 'production', 'services'):
            self.assertFalse(self.choose(choice))
        self.site['buildings'].clear()  # 无设施仍可主动取消已有方向。
        self.assertTrue(self.choose('cancel'))
        self.assertEqual(self.country['resources'], {'energy': 700, 'unity': 300})
        self.assertEqual(self.site['markers'], set())
        self.site['buildings'].add(LOW)
        self.assertTrue(self.choose('services'))
        self.assertEqual(self.country['resources'], {'energy': 400, 'unity': 200})
        self.assertEqual(self.bonus('planet_stability_add'), 3)
        for entries in MARKERS.values():
            self.assertEqual({e.key for e in entries}, {'icon', 'icon_frame'})

    def test_inactive_occupied_or_unqualified_sources_suspend_without_repayment(self):
        self.choose('research')
        for field, invalid, restored in (
            ('inactive', {LOW}, set()), ('controller', None, self.country),
            ('buildings', set(), {LOW}),
        ):
            self.site[field] = invalid
            self.assertEqual(self.bonus('planet_jobs_physics_research_produces_mult'), 0)
            self.assertEqual(self.site['markers'], {PREFIX + 'research'})
            self.site[field] = restored
            self.assertEqual(self.bonus('planet_jobs_physics_research_produces_mult'), 0.05)
        self.country['techs'].remove(TECH)
        self.assertEqual(self.bonus('planet_jobs_physics_research_produces_mult'), 0)
        self.country['techs'].add(TECH)
        self.assertEqual(self.country['resources'], {'energy': 700, 'unity': 300})

    def test_upgrade_keeps_choice_and_high_building_supplies_only_one_bonus(self):
        self.choose('research')
        self.site['queued'].add(HIGH)
        self.assertTrue(condition(block(BUILDINGS[LOW], 'potential'), self.site))
        self.assertFalse(condition(block(BUILDINGS[LOW], 'allow'), self.site))
        self.assertEqual(self.bonus('planet_jobs_physics_research_produces_mult'), 0.05)
        self.site['queued'].clear()
        self.site['buildings'].add(HIGH)  # 兼容遗留两级并存，不能叠成10%。
        self.assertEqual(self.bonus('planet_jobs_physics_research_produces_mult'), 0.05)
        self.site['buildings'].remove(LOW)
        self.assertEqual(self.bonus('planet_jobs_physics_research_produces_mult'), 0.05)
        self.assertEqual(self.site['markers'], {PREFIX + 'research'})
        self.country['techs'] = {'tech_artifact_destiny_economy'}
        self.assertEqual(scalar(BUILDINGS[HIGH], 'can_build'), 'yes')
        self.assertTrue(condition(block(BUILDINGS[HIGH], 'allow'), self.site))
        self.assertEqual(scalar(block(BUILDINGS[HIGH], 'planet_modifier'),
                                'job_artifact_tarot_analyst_add'), '6')

    def test_transfer_clears_only_local_planning_markers(self):
        self.choose('production')
        self.site['markers'].update({'artifact_emergency_prepared', 'artifact_sample_recorded'})
        self.assertEqual([e.value for e in block(ACTIONS['on_colony_transfer'], 'events')],
                         ['artifact_city_planning.1'])
        event = EVENTS['carrier_event']
        self.assertEqual(scalar(event, 'id'), 'artifact_city_planning.1')
        new_owner = dict(kind='country', species='HUM', techs=set())
        self.site['owner'] = new_owner
        self.site['controller'] = new_owner
        self.assertTrue(condition(block(event, 'trigger'), self.site))
        effect(block(event, 'immediate'), self.site)
        self.assertEqual(self.site['markers'],
                         {'artifact_emergency_prepared', 'artifact_sample_recorded'})
        self.assertEqual(self.country['resources'], {'energy': 700, 'unity': 300})
        self.assertFalse(condition(block(event, 'trigger'), self.site))

    def test_disaster_support_requires_bombardment_and_controlled_active_center(self):
        self.site['buildings'] = {CENTER}
        self.assertEqual(self.bonus('planet_stability_add'), 0)
        self.site['bombarded'] = True
        self.assertEqual(self.bonus('planet_stability_add'), 5)
        self.assertEqual(self.bonus('pop_amenities_usage_mult'), -0.1)
        self.site['inactive'].add(CENTER)
        self.assertEqual(self.bonus('planet_stability_add'), 0)
        self.site['inactive'].clear()
        self.site['controller'] = None
        self.assertEqual(self.bonus('planet_stability_add'), 0)
        self.site['controller'] = self.country
        self.country['techs'].remove(REFUGE)
        self.assertEqual(self.bonus('planet_stability_add'), 0)
        self.assertEqual(self.site['markers'], set())


if __name__ == '__main__':
    unittest.main()
