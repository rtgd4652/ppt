"""读取R2f条件修正，检查风险与资格边界；不把夹具称为引擎或实际读档验证。"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

import test_artifact_city_planning as city

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_mod import scalar

STATION = 'building_artifact_environment_buffer_station'
TECH = 'tech_artifact_environment_buffering'
BUILDING = city.load('mod/common/buildings/artifact_environment_buildings.txt')[STATION]


class EnvironmentBufferTests(unittest.TestCase):
    def setUp(self):
        self.country = dict(kind='country', species='ARTIFACT_USER', techs={TECH})
        self.site = dict(kind='colony', owner=self.country, controller=self.country,
                         buildings={STATION}, inactive=set(), markers=set(), queued=set())

    def bonuses(self):
        result = {}
        for entry in BUILDING:
            if entry.key != 'triggered_planet_modifier':
                continue
            if city.condition(city.block(entry.value, 'potential'), self.site):
                for modifier in entry.value:
                    if modifier.key != 'potential':
                        result[modifier.key] = result.get(modifier.key, 0) + float(modifier.value)
        return result

    def test_only_whitelisted_local_sources_allow_construction_and_benefit(self):
        for source in (None, 'bleak_planet', 'dangerous_wildlife', 'irradiated_wasteland'):
            with self.subTest(source=source):
                self.site['markers'] = {source} if source else set()
                self.assertFalse(city.condition(city.block(BUILDING, 'allow'), self.site))
                self.assertEqual(self.bonuses(), {})
        for source in ('hazardous_weather', 'weak_magnetic_field', 'irradiated_planet'):
            self.site['markers'] = {source}
            self.assertTrue(city.condition(city.block(BUILDING, 'allow'), self.site))
            self.assertTrue(self.bonuses())

    def test_compensation_leaves_half_each_selected_penalty_without_other_gains(self):
        # 从本机原版4.5.2核对的风险基准；升级游戏时不默默接受变化。
        native = {
            'hazardous_weather': {'pop_environment_tolerance': -0.1, 'pop_happiness': -0.05},
            'weak_magnetic_field': {'pop_environment_tolerance': -0.05, 'logistic_growth_mult': -0.05},
            'irradiated_planet': {'pop_environment_tolerance': -0.1,
                'biological_pop_happiness': -0.2, 'lithoid_pop_happiness': -0.2,
                'planet_jobs_food_produces_mult': -0.5},
        }
        for source, penalties in native.items():
            with self.subTest(source=source):
                self.site['markers'] = {source}
                before = deepcopy(self.site)
                gains = self.bonuses()
                self.assertEqual(gains.keys(), penalties.keys())
                for modifier, penalty in penalties.items():
                    self.assertAlmostEqual(penalty + gains[modifier], penalty / 2)
                self.assertEqual(self.site, before)  # 来源与资格检查不改写状态。

    def test_compound_sources_are_additive_and_removing_one_only_loses_its_buffer(self):
        self.site['markers'] = {'hazardous_weather', 'weak_magnetic_field', 'irradiated_planet'}
        all_sources = self.bonuses()
        self.assertAlmostEqual(all_sources['pop_environment_tolerance'], 0.125)
        self.site['markers'].remove('hazardous_weather')
        remaining = self.bonuses()
        self.assertAlmostEqual(remaining['pop_environment_tolerance'], 0.075)
        self.assertNotIn('pop_happiness', remaining)
        self.assertEqual(remaining['planet_jobs_food_produces_mult'], 0.25)
        self.site['markers'].clear()
        self.assertEqual(self.bonuses(), {})

    def test_inactive_ruined_removed_occupied_or_unqualified_source_stops_and_recovers(self):
        self.site['markers'] = {'hazardous_weather'}
        expected = self.bonuses()
        for field, invalid, restored in (
            ('inactive', {STATION}, set()), ('buildings', set(), {STATION}),
            ('controller', None, self.country),
        ):
            with self.subTest(field=field):
                self.site[field] = invalid
                self.assertEqual(self.bonuses(), {})
                self.site[field] = restored
                self.assertEqual(self.bonuses(), expected)
        for field, invalid, restored in (
            ('techs', set(), {TECH}), ('species', 'HUM', 'ARTIFACT_USER'),
        ):
            self.country[field] = invalid
            self.assertEqual(self.bonuses(), {})
            self.country[field] = restored
            self.assertEqual(self.bonuses(), expected)
        # 转让只使用新所有者资格，无旧国家收益残留。
        recipient = dict(kind='country', species='ARTIFACT_USER', techs=set())
        self.site.update(owner=recipient, controller=recipient)
        self.assertEqual(self.bonuses(), {})
        recipient['techs'].add(TECH)
        self.assertEqual(self.bonuses(), expected)

    def test_single_station_uses_native_upkeep_and_has_no_permanent_effect(self):
        self.assertEqual(scalar(BUILDING, 'planet_limit'), '1')
        upkeep = city.block(city.block(BUILDING, 'resources'), 'upkeep')
        self.assertEqual({e.key: float(e.value) for e in upkeep},
                         {'energy': 8, 'consumer_goods': 2, 'exotic_gases': 1})
        self.assertFalse({'planet_modifier', 'on_built', 'on_destroy'} & {e.key for e in BUILDING})


if __name__ == '__main__':
    unittest.main()
