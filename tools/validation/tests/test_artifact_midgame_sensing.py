"""执行R2c真实资格条件，区分国家、星港、星系与殖民地；不模拟引擎视野和读档。"""
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_mod import parse, scalar

ROOT = Path(__file__).resolve().parents[3]
LOW = 'building_artifact_long_baseline_array'
HIGH = 'building_artifact_phase_warning_array'
MEASURE = 'tech_artifact_long_baseline_measurement'
WARNING = 'tech_artifact_phase_disturbance_warning'
ORBITAL = 'tech_artifact_orbital_coordination'


def load(relative):
    return {e.key: e.value for e in parse((ROOT / relative).read_text(encoding='utf-8-sig'))}


def block(entries, key):
    return next(e.value for e in entries if e.key == key)


BUILDINGS = load('mod/common/buildings/artifact_midgame_sensing_buildings.txt')
RELAY = load('mod/common/starbase_buildings/artifact_orbital_observation_buildings.txt')['artifact_orbital_observation_link']
SIGNAL_TRIGGERS = load('mod/common/scripted_triggers/artifact_crisis_intelligence_triggers.txt')


def condition(entries, scope, history=()):
    # 所有转换显式压栈，不能把国家与星港合并成同一伪对象掩盖prev错误。
    def target(value):
        if value == 'owner':
            return scope.get('owner')
        if re.fullmatch(r'(prev)+', value):
            return history[-(len(value) // 4)]
        raise AssertionError(('unsupported target', value))

    def term(entry):
        key, value = entry.key, entry.value
        if key in SIGNAL_TRIGGERS:
            return condition(SIGNAL_TRIGGERS[key], scope, history) == (value == 'yes')
        if key == 'AND':
            return condition(value, scope, history)
        if key == 'carrier':
            assert scope['kind'] == 'colony'
            return condition(value, scope['carrier'], history + (scope,))
        if key == 'has_modifier':
            assert scope['kind'] == 'planet'
            return value in scope['modifiers']
        if key == 'NOT':
            assert len(value) == 1
            return not term(value[0])
        if key == 'NOR':
            return not any(term(e) for e in value)
        if key == 'OR':
            return any(term(e) for e in value)
        if key == 'exists':
            return target(value) is not None
        if key in ('owner', 'solar_system', 'owner_main_species'):
            next_scope = scope[{'owner': 'owner', 'solar_system': 'system',
                                'owner_main_species': 'species'}[key]]
            return condition(value, next_scope, history + (scope,))
        if re.fullmatch(r'(prev)+', key):
            return condition(value, target(key), history + (scope,))
        if key == 'has_technology':
            assert scope['kind'] == 'country'
            return value in scope['techs']
        if key == 'is_species_class':
            assert scope['kind'] == 'species'
            return scope['class'] == value
        if key in ('is_owned_by', 'is_controlled_by'):
            assert scope['kind'] in ('colony', 'starbase')
            return scope['owner' if key == 'is_owned_by' else 'controller'] is target(value)
        if key == 'is_occupied_flag':
            assert scope['kind'] == 'colony'
            return scope['occupied'] == (value == 'yes')
        if key in ('any_system_planet_colony', 'any_owned_colony'):
            assert scope['kind'] == ('system' if key == 'any_system_planet_colony' else 'country')
            return any(condition(value, colony, history + (scope,)) for colony in scope['colonies'])
        if key in ('has_active_building', 'has_building', 'has_building_construction'):
            assert scope['kind'] == 'colony'
            if key == 'has_building_construction':
                return value in scope['queued']
            active = scope['buildings'] - scope['inactive']
            return value in (active if key == 'has_active_building' else scope['buildings'])
        raise AssertionError(('unsupported condition', key))
    return all(term(entry) for entry in entries)


def applied_modifiers(entries, field, scope):
    return [entry.value for entry in entries if entry.key == field
            and condition(block(entry.value, 'potential'), scope)]


def total(modifiers, key):
    return sum(float(scalar(modifier, key) or 0) for modifier in modifiers)


class SensingTests(unittest.TestCase):
    def setUp(self):
        self.country = dict(kind='country', species=dict(kind='species', **{'class': 'ARTIFACT_USER'}),
                            techs={MEASURE, WARNING, ORBITAL}, colonies=[])
        self.foreign = dict(kind='country', species=dict(kind='species', **{'class': 'ARTIFACT_USER'}),
                            techs={MEASURE, WARNING, ORBITAL}, colonies=[])
        self.system = dict(kind='system', colonies=[])
        self.site = dict(kind='colony', owner=self.country, controller=self.country,
                         occupied=False, buildings={LOW}, inactive=set(), queued=set())
        # 旧阵列场景没有F02窗口；显式保持载体身份。正向监听由F02完整栈检查覆盖。
        self.site['carrier'] = dict(kind='planet', modifiers=set())
        self.country['colonies'].append(self.site)
        self.system['colonies'].append(self.site)
        self.base = dict(kind='starbase', owner=self.country, controller=self.country,
                         system=self.system)

    def support(self):
        return applied_modifiers(RELAY, 'triggered_station_modifier', self.base)

    def test_baseline_country_support_requires_active_controlled_public_source(self):
        modifier = block(BUILDINGS[LOW], 'triggered_country_modifier')
        enabled = lambda: condition(block(modifier, 'potential'), self.site)
        self.assertTrue(enabled())
        self.site['inactive'].add(LOW)  # 停用或损坏由同一原生活跃判定排除。
        self.assertFalse(enabled())
        self.site['inactive'].clear()
        self.assertTrue(enabled())
        self.site['controller'] = self.foreign
        self.assertFalse(enabled())
        self.site['controller'] = self.country
        self.country['techs'].remove(MEASURE)
        self.assertFalse(enabled())
        self.country['techs'].add(MEASURE)
        self.country['species']['class'] = 'HUM'
        self.assertFalse(enabled())
        self.site['owner'] = None
        self.assertFalse(enabled())

    def test_orbital_support_requires_same_system_and_same_owner(self):
        self.assertEqual(total(self.support(), 'ship_sensor_range_add'), 1)
        # 同一文明种族的另一国家也不能提供本国资料。
        foreign_site = dict(self.site, owner=self.foreign, controller=self.foreign,
                            buildings={HIGH})
        self.system['colonies'].append(foreign_site)
        self.site['inactive'].add(LOW)
        self.assertEqual(self.support(), [])
        self.site['inactive'].clear()
        self.system['colonies'].remove(self.site)  # 本国来源移到另一星系不满足。
        self.assertEqual(self.support(), [])
        self.system['colonies'].append(self.site)
        self.site['occupied'] = True
        self.assertEqual(self.support(), [])
        self.site['occupied'] = False
        self.base['controller'] = self.foreign
        self.assertEqual(self.support(), [])
        self.base['controller'] = self.country
        self.assertEqual(total(self.support(), 'ship_hyperlane_range_add'), 2)
        self.country['techs'].remove(ORBITAL)
        self.assertEqual(self.support(), [])

    def test_upgrade_retains_baseline_then_applies_warning_once(self):
        self.site['queued'].add(HIGH)
        self.assertTrue(condition(block(BUILDINGS[LOW], 'potential'), self.site))
        self.assertFalse(condition(block(BUILDINGS[LOW], 'allow'), self.site))
        self.assertEqual(total(self.support(), 'ship_sensor_range_add'), 1)
        self.assertEqual(total(self.support(), 'ship_cloaking_detection_add'), 0)
        self.site['queued'].clear()
        self.site['buildings'] = {HIGH}
        self.assertEqual(total(self.support(), 'ship_sensor_range_add'), 1)
        self.assertEqual(total(self.support(), 'ship_cloaking_detection_add'), 1)
        country_mods = sum((applied_modifiers(building, 'triggered_country_modifier', self.site)
                            for building in BUILDINGS.values()), [])
        self.assertEqual(total(country_mods, 'ship_sensor_range_add'), 1)
        self.assertEqual(total(country_mods, 'ship_hyperlane_range_add'), 2)
        self.site['inactive'].add(HIGH)
        self.assertEqual(self.support(), [])
        self.site['inactive'].clear()
        self.country['techs'].remove(WARNING)
        self.assertEqual(total(self.support(), 'ship_cloaking_detection_add'), 0)

    def test_new_baseline_blocked_by_high_stage_on_another_colony(self):
        other = dict(self.site, buildings={HIGH}, queued=set(), inactive={HIGH})
        self.country['colonies'].append(other)
        self.assertFalse(condition(block(BUILDINGS[LOW], 'allow'), self.site))
        other['buildings'] = set()
        other['queued'] = {HIGH}
        self.assertFalse(condition(block(BUILDINGS[LOW], 'allow'), self.site))
        other['queued'].clear()
        self.assertTrue(condition(block(BUILDINGS[LOW], 'allow'), self.site))


if __name__ == '__main__':
    unittest.main()
