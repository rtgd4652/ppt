"""执行R2b真实条件，区分行星与国家；不模拟引擎就业、动态更新或读档。"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_mod import parse, scalar

ROOT = Path(__file__).resolve().parents[3]


def load(relative):
    return {e.key: e.value for e in parse((ROOT / relative).read_text(encoding='utf-8-sig'))}


def block(entries, key):
    return next((e.value for e in entries if e.key == key), [])


OLD = load('mod/common/buildings/aemusa_buildings.txt')
NEW = load('mod/common/buildings/artifact_midgame_observation_energy_buildings.txt')
OBS = 'building_artifact_black_gate_observatory'
SAMPLE = 'building_artifact_sample_repository'
LOW = 'building_artifact_phase_power_test_station'
HIGH = 'building_artifact_phase_reactor'
MULTI = 'tech_artifact_multi_source_comparison'
ENERGY = 'tech_artifact_phase_energy'


def condition(entries, scope):
    # 未支持的语法或作用域立即失败，不把owner与当地现场合并成同一对象。
    def term(entry):
        key, value = entry.key, entry.value
        if key == 'NOR':
            return not any(term(e) for e in value)
        if key == 'exists':
            assert scope['kind'] == 'colony' and value == 'owner'
            return scope['owner'] is not None
        if key == 'owner':
            assert scope['kind'] == 'colony'
            return condition(value, scope['owner'])
        if key == 'owner_main_species':
            assert scope['kind'] == 'country'
            return condition(value, scope)
        if key == 'is_species_class':
            assert scope['kind'] == 'country'
            return scope['species'] == value
        if key == 'has_technology':
            assert scope['kind'] == 'country'
            return value in scope['techs']
        if key in ('has_active_building', 'has_building', 'has_building_construction'):
            assert scope['kind'] == 'colony'
            if key == 'has_building_construction':
                return value in scope['queued']
            if key == 'has_active_building':
                return value in scope['buildings'] - scope['inactive']
            return value in scope['buildings']
        raise AssertionError(('unsupported condition', key))
    return all(term(entry) for entry in entries)


class ObservationEnergyTests(unittest.TestCase):
    def setUp(self):
        self.country = dict(kind='country', species='ARTIFACT_USER', techs=set())
        self.site = dict(kind='colony', owner=self.country,
                         buildings={OBS}, inactive=set(), queued=set())
        self.bonuses = [e.value for e in OLD[OBS] if e.key == 'triggered_planet_modifier']
        self.multi = next(b for b in self.bonuses
                          if scalar(b, 'planet_jobs_physics_research_produces_mult') is not None)

    def enabled(self):
        return condition(block(self.multi, 'potential'), self.site)

    def test_two_sources_must_be_active_on_same_colony(self):
        self.country['techs'].add(MULTI)
        other_site = dict(self.site, buildings={SAMPLE})
        self.assertIn(SAMPLE, other_site['buildings'])
        self.assertFalse(self.enabled())  # 别处的样本库不满足当地条件。
        self.site['buildings'].add(SAMPLE)
        self.assertTrue(self.enabled())
        for source in (OBS, SAMPLE):
            with self.subTest(source=source):
                self.site['inactive'].add(source)
                self.assertFalse(self.enabled())
                self.site['inactive'].clear()
                self.assertTrue(self.enabled())
                self.site['buildings'].remove(source)
                self.assertFalse(self.enabled())
                self.site['buildings'].add(source)
        self.country['techs'].clear()
        self.assertFalse(self.enabled())

    def test_new_comparison_keeps_existing_economy_bonus_independent(self):
        self.site['buildings'].add(SAMPLE)
        self.country['techs'].add('tech_artifact_tarot_economy')
        self.assertFalse(self.enabled())
        self.country['techs'].add(MULTI)
        self.assertTrue(self.enabled())
        applied = [b for b in self.bonuses if condition(block(b, 'potential'), self.site)]
        self.assertEqual(sum(float(scalar(b, 'job_artifact_tarot_analyst_add') or 0)
                             for b in applied), 2)
        self.assertEqual(sum(float(scalar(b, 'planet_jobs_physics_research_produces_mult') or 0)
                             for b in applied), 0.1)
        self.assertEqual(sum(float(scalar(b, 'planet_jobs_engineering_research_produces_mult') or 0)
                             for b in applied), 0.05)
        self.country['species'] = 'HUM'
        self.assertFalse(self.enabled())
        self.site['owner'] = None
        self.assertFalse(self.enabled())

    def test_upgrade_preserves_parent_and_original_direct_build_qualification(self):
        low, high = NEW[LOW], OLD[HIGH]
        self.assertTrue(condition(block(low, 'allow'), self.site))
        self.site['buildings'].add(LOW)
        self.site['queued'].add(HIGH)
        self.assertTrue(condition(block(low, 'potential'), self.site))
        self.assertFalse(condition(block(low, 'allow'), self.site))
        self.site['queued'].clear()
        self.site['buildings'].add(HIGH)
        self.assertFalse(condition(block(low, 'allow'), self.site))
        self.assertFalse(condition(block(high, 'allow'), self.site))
        self.country['techs'] = {ENERGY}  # 旧高级站不要求新B09或低级站。
        self.assertTrue(condition(block(high, 'allow'), self.site))
        self.assertEqual(scalar(high, 'can_build'), 'yes')
        self.assertEqual(scalar(block(low, 'planet_modifier'),
                                'job_artifact_phase_technician_add'), '200')
        self.assertEqual(scalar(block(high, 'planet_modifier'),
                                'job_artifact_phase_technician_add'), '800')
        self.country['species'] = 'HUM'
        self.assertFalse(condition(block(low, 'potential'), self.site))


if __name__ == '__main__':
    unittest.main()
