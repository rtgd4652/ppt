"""执行R2a实际建筑条件；原生就业、区划回调和真实读档仍需游戏验证。"""
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


BUILDINGS = load('mod/common/buildings/artifact_midgame_resource_buildings.txt')
OLD_BUILDINGS = load('mod/common/buildings/aemusa_buildings.txt')
HIGH = 'building_artifact_phase_mine'
LOW = 'building_artifact_vein_mapping_station'
RECYCLE = 'building_artifact_byproduct_recycling_plant'


def condition(entries, site):
    def term(entry):
        key, value = entry.key, entry.value
        if key == 'OR':
            return any(term(e) for e in value)
        if key == 'NOR':
            return not any(term(e) for e in value)
        if key in ('owner', 'owner_main_species'):
            return condition(value, site)
        if key == 'exists':
            if value != 'owner':
                raise AssertionError(('unsupported object', value))
            return site['owner_exists']
        if key == 'is_species_class':
            return site['species'] == value
        if key == 'has_district':
            return value in site['districts']
        if key == 'has_building':
            return value in site['buildings']
        if key == 'has_active_building':
            return value in site['buildings'] - site['inactive']
        if key == 'has_building_construction':
            return value in site['queued']
        if key == 'has_technology':
            return value in site['techs']
        raise AssertionError(('unsupported trigger', key))
    return all(term(e) for e in entries)


class MidgameResourceTests(unittest.TestCase):
    def setUp(self):
        self.site = dict(owner_exists=True, species='ARTIFACT_USER',
                         districts={'district_mining'}, buildings=set(),
                         inactive=set(), queued=set(), techs=set())

    def test_upgrade_queue_keeps_parent_and_old_direct_build_gate(self):
        low, high = BUILDINGS[LOW], OLD_BUILDINGS[HIGH]
        self.assertTrue(condition(block(low, 'allow'), self.site))
        self.site['buildings'].add(LOW)
        self.site['queued'].add(HIGH)
        self.assertTrue(condition(block(low, 'potential'), self.site))
        self.assertFalse(condition(block(low, 'allow'), self.site))
        self.site['districts'].clear()
        self.assertTrue(condition(block(low, 'potential'), self.site))
        self.assertFalse(condition(block(high, 'allow'), self.site))
        self.site['techs'].add('tech_artifact_phase_extraction')
        self.assertTrue(condition(block(high, 'allow'), self.site))
        self.assertEqual(scalar(high, 'can_build'), 'yes')
        self.assertGreater(float(scalar(block(high, 'planet_modifier'), 'job_artifact_phase_miner_add')),
                           float(scalar(block(low, 'planet_modifier'), 'job_artifact_vein_surveyor_add')))

    def test_recycling_loses_and_restores_jobs_with_real_source(self):
        building = BUILDINGS[RECYCLE]
        production = block(building, 'triggered_planet_modifier')
        source = block(production, 'potential')
        self.assertTrue(condition(block(building, 'allow'), self.site))
        self.assertTrue(condition(source, self.site))
        self.site['districts'].clear()
        self.site['buildings'].add(RECYCLE)
        self.assertFalse(condition(source, self.site))  # 回收厂不能以自身作为原料来源。
        self.assertEqual(scalar(block(block(building, 'resources'), 'upkeep'), 'energy'), '4')
        workshop = 'building_artifact_relic_workshop'
        self.site['buildings'].add(workshop)
        self.site['inactive'].add(workshop)
        self.assertFalse(condition(source, self.site))
        self.site['inactive'].clear()
        self.assertTrue(condition(source, self.site))
        self.assertEqual(scalar(production, 'job_artifact_recycling_technician_add'), '200')
        self.assertEqual(block(building, 'planet_modifier'), [])  # 不保留无条件回收岗位。

    def test_foreign_owner_cannot_enter_and_site_is_not_existence_gate(self):
        for building in BUILDINGS.values():
            with self.subTest(building=scalar(building, 'icon')):
                self.assertTrue(condition(block(building, 'potential'), self.site))
                self.site['districts'].clear()
                self.site['queued'].add(HIGH)
                self.assertTrue(condition(block(building, 'potential'), self.site))
                self.site['species'] = 'HUM'
                self.assertFalse(condition(block(building, 'potential'), self.site))
                self.site['species'] = 'ARTIFACT_USER'
                self.site['owner_exists'] = False
                self.assertFalse(condition(block(building, 'potential'), self.site))
                self.site['owner_exists'] = True


if __name__ == '__main__':
    unittest.main()
