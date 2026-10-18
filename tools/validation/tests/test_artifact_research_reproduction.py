"""执行正式R1/R2e脚本核对成果来源和跨星球复现；不模拟引擎就业或真实存读档。"""
from copy import deepcopy
import unittest

import test_artifact_foundation_projects as foundation

C10 = 'tech_artifact_public_reproduction_protocol'
E05 = 'tech_artifact_research_campus_integration'
ARCHIVE = 'building_artifact_memory_archive_room'
PARK = 'building_artifact_public_research_campus'
SPIRE = 'building_artifact_destiny_research_spire'
SAMPLE = 'artifact_public_sample_record'
MATERIALS = 'artifact_public_material_record'


class World(foundation.World):
    """复用原有严格作用域夹具，只增加本包实际使用的两种原生条件。"""

    def __init__(self):
        super().__init__()
        for country in self.countries.values():
            country['flags'] = set()
            country['techs'].update({C10, E05})

    def add_planet(self, key, owner='A'):
        planet = super().add_planet(key, owner)
        planet['inactive'] = set()
        return planet

    def term(self, entry, obj, ctx, prev):
        if entry.key == 'has_country_flag':
            assert obj['kind'] == 'country'
            return entry.value in obj['flags']
        if entry.key == 'has_active_building':
            assert obj['kind'] in ('planet', 'colony')
            return entry.value in obj['buildings'] - obj['inactive']
        return super().term(entry, obj, ctx, prev)

    def execute(self, entries, obj, ctx, prev=None):
        # 归档国家作用域只有单一flag，不能把未知效果忽略为成功。
        if any(e.key == 'set_country_flag' for e in entries):
            assert obj['kind'] == 'country'
            assert all(e.key == 'set_country_flag' for e in entries)
            obj['flags'].update(e.value for e in entries)
            return
        return super().execute(entries, obj, ctx, prev)

    def choose(self, mode, planet='P', ctx=None):
        kind = 'sample' if mode in ('sample_analysis', 'reproduce_sample') else 'workshop'
        ctx = self.open(kind, planet) if ctx is None else ctx
        event = 'artifact_foundation.' + ('10' if kind == 'sample' else '20')
        return self.pick(event, 'artifact_foundation.start_' + mode, planet, ctx)

    def pick(self, event, name, planet, ctx):
        if ctx is None:
            return False
        obj = self.planets[planet]
        option = next(e.value for e in foundation.EVENTS[event]
                      if e.key == 'option' and foundation.scalar(e.value, 'name') == name)
        if not (self.condition(foundation.child(option, 'trigger', []), obj, ctx)
                and self.condition(foundation.child(option, 'allow', []), obj, ctx)):
            return False
        self.execute(foundation.child(option, 'hidden_effect', []), obj, ctx)
        return True

    def archive(self, kind='sample', planet='P', ctx=None):
        ctx = self.open('sample' if kind == 'sample' else 'workshop', planet) if ctx is None else ctx
        return self.pick('artifact_foundation.30', 'artifact_research.archive_' + kind,
                         planet, ctx)

    def source(self, kind='sample'):
        mode = 'sample_analysis' if kind == 'sample' else 'materials_study'
        assert self.choose(mode)
        for _ in range(3):
            self.monthly()
        self.planets['P']['buildings'].add(ARCHIVE)
        return 'artifact_foundation_' + mode


class ResearchReproductionTests(unittest.TestCase):
    def test_only_live_completed_source_and_active_archive_can_record(self):
        world = World()
        self.assertFalse(world.archive())
        source = world.source()
        planet = world.planets['P']
        before = deepcopy(world.countries['A']['resources'])
        for change, restore in (
            (lambda: planet['inactive'].add(ARCHIVE), lambda: planet['inactive'].clear()),
            (lambda: planet.update(controller='B'), lambda: planet.update(controller='A')),
            (lambda: planet.update(bombarded=True), lambda: planet.update(bombarded=False)),
            (lambda: world.countries['A']['techs'].remove(C10),
             lambda: world.countries['A']['techs'].add(C10)),
        ):
            change()
            self.assertFalse(world.archive())
            restore()
        self.assertTrue(world.archive())
        self.assertFalse(world.archive())
        self.assertEqual(world.countries['A']['flags'], {SAMPLE})
        self.assertEqual(world.countries['A']['resources'], before)
        self.assertEqual(planet['modifiers'][source], 720)
        world.elapsed(720)
        self.assertIn(SAMPLE, world.countries['A']['flags'])
        self.assertFalse(world.archive())

    def test_paid_reproduction_uses_record_on_another_colony_and_completes_once(self):
        for kind in ('sample', 'materials'):
            with self.subTest(kind=kind):
                world = World()
                result = world.source(kind)
                self.assertTrue(world.archive(kind))
                destination = world.add_planet('Q')
                destination['buildings'] = {PARK}  # 无原样本库、原工坊或当地档案楼。
                before = deepcopy(world.countries['A']['resources'])
                mode = 'reproduce_' + kind
                self.assertTrue(world.choose(mode, 'Q'))
                self.assertEqual(world.countries['A']['resources']['energy'], before['energy'] - 300)
                self.assertEqual(world.countries['A']['resources']['consumer_goods'], before['consumer_goods'] - 150)
                ctx = world.open('sample' if kind == 'sample' else 'workshop', 'Q')
                for _ in range(3):
                    self.assertFalse(world.choose(mode, 'Q', ctx))
                self.assertEqual(destination['vars']['arf_r1_progress'], 0)
                for _ in range(5):
                    world.monthly()
                self.assertEqual(destination['vars']['arf_r1_progress'], 5)
                self.assertNotIn(result, destination['modifiers'])
                world.monthly()
                self.assertEqual(destination['modifiers'], {result: 720})
                world.elapsed(1)
                world.execute(foundation.EFFECTS['artifact_foundation_complete'], destination, {})
                self.assertEqual(destination['modifiers'][result], 719)
                self.assertFalse(world.choose(mode, 'Q'))
                world.elapsed(719)
                self.assertTrue(world.choose(mode, 'Q'))
                self.assertEqual(world.countries['A']['resources']['energy'], before['energy'] - 600)
                self.assertEqual(world.countries['A']['resources']['consumer_goods'], before['consumer_goods'] - 300)

    def test_no_record_wrong_research_missing_site_or_resources_never_pay(self):
        for reason in ('record', 'research', 'site', 'energy', 'consumer_goods'):
            with self.subTest(reason=reason):
                world = World()
                planet = world.add_planet('Q')
                planet['buildings'] = {PARK}
                world.countries['A']['flags'].add(SAMPLE)
                if reason == 'record':
                    world.countries['A']['flags'].clear()
                elif reason == 'research':
                    world.countries['A']['techs'].discard(E05)
                elif reason == 'site':
                    planet['buildings'].clear()
                else:
                    world.countries['A']['resources'][reason] = 0
                before = deepcopy(world.countries['A']['resources'])
                self.assertFalse(world.choose('reproduce_sample', 'Q'))
                self.assertEqual(world.countries['A']['resources'], before)
                self.assertEqual(planet['flags'], set())

    def test_occupation_disabling_or_research_loss_pause_and_upgrade_continues(self):
        world = World()
        world.source()
        world.archive()
        planet = world.add_planet('Q')
        planet['buildings'] = {PARK}
        world.choose('reproduce_sample', 'Q')
        world.monthly()
        before = deepcopy(world.countries['A']['resources'])
        for field, value, restored in (
            ('inactive', {PARK}, set()), ('controller', 'B', 'A'),
            ('bombarded', True, False), ('buildings', set(), {PARK}),
        ):
            planet[field] = value
            world.monthly()
            self.assertEqual(planet['vars']['arf_r1_progress'], 1)
            planet[field] = restored
        world.countries['A']['techs'].discard(E05)
        world.monthly()
        self.assertEqual(planet['vars']['arf_r1_progress'], 1)
        world.countries['A']['techs'].add(E05)
        planet['buildings'] = {SPIRE}
        for _ in range(5):
            world.monthly()
        self.assertEqual(planet['modifiers'], {'artifact_foundation_sample_analysis': 720})
        self.assertEqual(world.countries['A']['resources'], before)

    def test_transfer_aborts_local_project_without_transferring_country_knowledge(self):
        world = World()
        world.source()
        world.archive()
        planet = world.add_planet('Q')
        planet['buildings'] = {PARK}
        ctx = world.open('sample', 'Q')
        world.choose('reproduce_sample', 'Q', ctx)
        world.monthly()
        planet['owner'] = planet['controller'] = 'B'
        before_a = deepcopy(world.countries['A']['resources'])
        before_b = deepcopy(world.countries['B']['resources'])
        world.dispatch('artifact_foundation.2', planet)
        self.assertNotIn('arf_r1_active', planet['flags'])
        self.assertNotIn('arf_r1_mode_reproduce_sample', planet['flags'])
        self.assertIn(SAMPLE, world.countries['A']['flags'])
        self.assertNotIn(SAMPLE, world.countries['B']['flags'])
        self.assertFalse(world.choose('reproduce_sample', 'Q', ctx))
        self.assertFalse(world.choose('reproduce_sample', 'Q'))
        self.assertEqual(world.countries['A']['resources'], before_a)
        self.assertEqual(world.countries['B']['resources'], before_b)

    def test_park_upgrade_and_targeted_spire_capacity_contract(self):
        load = foundation.load
        low = load('mod/common/buildings/artifact_public_research_buildings.txt')[PARK]
        high = load('mod/common/buildings/aemusa_buildings.txt')[SPIRE]
        self.assertEqual(foundation.scalar(low, 'can_build'), 'yes')
        self.assertEqual(foundation.scalar(high, 'can_build'), 'yes')
        self.assertEqual([e.value or e.key for e in foundation.child(low, 'upgrades')], [SPIRE])
        self.assertEqual(foundation.scalar(foundation.child(low, 'triggered_planet_modifier'),
                                         'job_artifact_destiny_researcher_add'), '400')
        self.assertEqual(foundation.scalar(foundation.child(high, 'planet_modifier'),
                                         'job_artifact_destiny_researcher_add'), '800')
        self.assertEqual(foundation.scalar(foundation.child(high, 'planet_modifier'),
                                         'planet_jobs_produces_mult'), '0.10')
        self.assertEqual(foundation.scalar(high, 'base_buildtime'), '720')
        self.assertNotIn('empire_limit', {e.key for e in high})
        world = World()
        site = world.planets['P']
        site['buildings'] = {PARK, SPIRE}
        self.assertFalse(world.condition(foundation.child(low, 'allow'), site, {}))
        potential = foundation.child(foundation.child(low, 'triggered_planet_modifier'), 'potential')
        self.assertFalse(world.condition(potential, site, {}))
        site['inactive'].add(SPIRE)
        self.assertTrue(world.condition(potential, site, {}))


if __name__ == '__main__':
    unittest.main()
