"""执行D14正式条件与效果，检查实付、同星归属、单份维护和清理。

原生决议扣费、条件修正应用及军队战斗为外部契约；不模拟游戏或真实存读档。
作用域显式压栈，殖民地与承载行星使用不同索引，未知语法立即报错。
"""
from copy import deepcopy
import re
import unittest

import test_artifact_foundation_projects as base
from check_mod import parse, scalar

ROOT, child = base.ROOT, base.child
TECH = 'tech_artifact_civilization_joint_defense'
GARRISON = 'tech_artifact_planetary_garrison'
ORBITAL = 'tech_artifact_orbital_coordination'
MARKER = 'ajd_deployed'
LINK = 'artifact_orbital_observation_link'
CENTER, BRANCH, HIGH = ('building_artifact_community_service_center',
                        'building_artifact_sanctum', 'building_artifact_coordination_center')
text = (ROOT / 'mod/common/scripted_triggers/artifact_joint_defense_triggers.txt').read_text(encoding='utf-8')
text = re.sub(r'has_starbase_size\s*>=', 'has_starbase_size_ge =', text)
TRIGGERS = {**base.load('mod/common/scripted_triggers/artifact_garrison_triggers.txt'),
            **base.load('mod/common/scripted_triggers/artifact_crisis_intelligence_triggers.txt'),
            **{e.key:e.value for e in parse(text)}}
EFFECTS = {**base.load('mod/common/scripted_effects/artifact_garrison_effects.txt'),
           **base.load('mod/common/scripted_effects/artifact_joint_defense_effects.txt')}
DECISIONS = base.load('mod/common/decisions/artifact_joint_defense_decisions.txt')
EVENT = base.load('mod/events/artifact_garrison_events.txt')['carrier_event']
BUILDINGS = {}
for name in ('artifact_public_foundation_buildings', 'aemusa_buildings', 'artifact_civil_supply_buildings'):
    BUILDINGS.update(base.load('mod/common/buildings/' + name + '.txt'))
STATION = base.load('mod/common/starbase_buildings/artifact_orbital_observation_buildings.txt')[LINK]


def joint_block(entries):
    return any(e.key and e.key.startswith('artifact_joint_defense_') or
               isinstance(e.value, list) and joint_block(e.value) for e in entries)


class World:
    def __init__(self):
        self.countries = {key: dict(kind='country', id=key, species='ARTIFACT_USER',
            techs={TECH, GARRISON, ORBITAL}, resources={'energy':500, 'alloys':300, 'consumer_goods':200})
            for key in ('A','B')}
        self.systems = {key: dict(kind='system', id=key, colonies=[]) for key in ('S','T')}
        self.origins = {}
        self.planets = {}
        for system in self.systems.values():
            system['starbase'] = dict(kind='starbase', owner=self.countries['A'], controller=self.countries['A'],
                solar_system=system, normal=True, size='starbase_starport', buildings={LINK})
        self.p = self.add_planet('P')
        self.station = self.systems['S']['starbase']

    def add_planet(self, key, country='A', system='S'):
        p = dict(kind='planet', id=key, owner=self.countries[country], controller=self.countries[country],
            solar_system=self.systems[system], buildings={CENTER}, inactive=set(),
            flags={'artifact_garrison_enabled'}, modifiers={}, colony=True)
        self.planets[key] = p
        self.systems[system]['colonies'].append(p)
        self.origins[('planet',key)] = self.countries[country]
        return p

    def colony(self, planet):
        return dict(planet, kind='colony', id='colony:'+planet['id'], planet=planet)

    def resolve(self, path, stack):
        if path == 'event_target:artifact_garrison_owner@this':
            obj = stack[-1]
            return self.origins.get((obj['kind'],obj['id']))
        parts = path.split('.')
        if parts[0] == 'root':
            obj, parts = stack[0], parts[1:]
        elif re.fullmatch(r'(prev)+', parts[0]):
            obj, parts = stack[-1-len(parts[0])//4], parts[1:]
        else:
            obj = stack[-1]
        for key in parts:
            obj = obj.get(key) if obj is not None else None
        return obj

    def condition(self, entries, stack):
        return all(self.term(e,stack) for e in entries)

    def term(self, e, stack):
        k,v,obj = e.key,e.value,stack[-1]
        if k in TRIGGERS:
            return self.condition(TRIGGERS[k],stack) == (v == 'yes')
        if k in ('NOT','NOR','OR'):
            if k == 'NOT': assert len(v) == 1
            result = any(self.term(x,stack) for x in v)
            return result if k == 'OR' else not result
        if k in ('AND','custom_tooltip'): return self.condition(v,stack)
        if k == 'fail_text': return True
        if k == 'exists': return self.resolve(v,stack) is not None
        if k in ('owner','planet','solar_system','starbase'):
            target = self.resolve(k,stack)
            return target is not None and self.condition(v,stack+[target])
        if k == 'owner_main_species': return self.condition(v,stack)
        if k == 'is_species_class': return obj['species'] == v
        if k == 'has_technology': return v in obj['techs']
        if k == 'carrier_is_type': return obj['kind'] in ('colony','planet') and v == 'planet'
        if k == 'is_colony': return obj['colony'] == (v == 'yes')
        if k == 'has_modifier': return v in obj['modifiers']
        if k == 'has_carrier_flag': return v in obj['flags']
        if k == 'has_active_building': return v in obj['buildings'] - obj['inactive']
        if k == 'has_starbase_building': return v in obj['buildings']
        if k == 'has_starbase_size_ge':
            levels = ['starbase_outpost','starbase_starport','starbase_starhold','starbase_starfortress','starbase_citadel']
            return levels.index(obj['size']) >= levels.index(v)
        if k == 'is_normal_starbase': return obj['normal'] == (v == 'yes')
        if k in ('is_owned_by','is_controlled_by'):
            return obj['owner' if k == 'is_owned_by' else 'controller'] is self.resolve(v,stack)
        if k == 'any_system_planet_colony':
            return any(self.condition(v,stack+[self.colony(p)]) for p in obj['colonies'])
        raise AssertionError(('unknown trigger',k))

    def execute(self, entries, stack):
        obj = stack[-1]
        for e in entries:
            k,v = e.key,e.value
            if k in EFFECTS: self.execute(EFFECTS[k],stack)
            elif k == 'if':
                if self.condition(child(v,'limit'),stack):
                    self.execute([x for x in v if x.key != 'limit'],stack)
            elif k == 'hidden_effect': self.execute(v,stack)
            elif k == 'custom_tooltip': pass
            elif k == 'add_modifier': obj['modifiers'][scalar(v,'modifier')] = int(scalar(v,'days'))
            elif k == 'remove_modifier': obj['modifiers'].pop(v,None)
            elif k == 'remove_carrier_flag': obj['flags'].discard(v)
            elif k == 'clear_global_event_target':
                assert v == 'artifact_garrison_owner@this'
                self.origins.pop((obj['kind'],obj['id']),None)
            else: raise AssertionError(('unknown effect',k))

    def choose(self, name='enable', planet=None):
        p = self.p if planet is None else planet
        d = DECISIONS['decision_artifact_'+name+'_joint_defense']
        if not all(self.condition(child(d,key,[]),[p]) for key in ('potential','allow')): return False
        # 原生决议费用契约由外部夹具代表；效果不应再次扣费。
        cost = child(child(d,'resources',[]),'cost',[])
        resources = p['owner']['resources']
        if any(resources.get(e.key,0) < float(e.value) for e in cost): return False
        for e in cost: resources[e.key] -= float(e.value)
        self.execute(child(d,'effect'),[p])
        return True

    def land(self, planet=None):
        p = self.p if planet is None else planet
        result = dict(army_defense_damage_mult=0, army_defense_health_mult=0, planet_defense_armies_add=0)
        upkeep = {}
        for name in p['buildings'] - p['inactive']:
            body = BUILDINGS[name]
            for e in body:
                if e.key == 'triggered_planet_modifier' and (joint_block(e.value) or scalar(e.value,'planet_defense_armies_add')):
                    if self.condition(child(e.value,'potential'),[self.colony(p)]):
                        for key in result: result[key] += float(scalar(e.value,key) or 0)
            for e in child(body,'resources'):
                if e.key == 'upkeep' and joint_block(e.value) and self.condition(child(e.value,'trigger'),[self.colony(p)]):
                    for value in e.value:
                        if value.key != 'trigger': upkeep[value.key] = upkeep.get(value.key,0)+float(value.value)
        return result,upkeep

    def orbital(self, station=None):
        station = self.station if station is None else station
        result = dict(ship_fire_rate_mult=0,ship_tracking_add=0)
        for e in STATION:
            if e.key == 'triggered_station_modifier' and joint_block(e.value) and self.condition(child(e.value,'potential'),[station]):
                for key in result: result[key] += float(scalar(e.value,key) or 0)
        return result


class JointDefenseTests(unittest.TestCase):
    def test_exact_payment_upgrade_priority_and_no_new_army_slots(self):
        w = World(); self.assertTrue(w.choose())
        self.assertEqual(w.countries['A']['resources'],dict(energy=0,alloys=0,consumer_goods=0))
        expected = (dict(army_defense_damage_mult=.25,army_defense_health_mult=.25,planet_defense_armies_add=2),dict(energy=4,alloys=1))
        self.assertEqual(w.land(),expected)
        self.assertEqual(w.orbital(),dict(ship_fire_rate_mult=.15,ship_tracking_add=10))
        self.assertFalse(w.choose())
        w.p['buildings'].add(BRANCH); self.assertEqual(w.land(),expected)
        w.p['buildings'].add(HIGH); self.assertEqual(w.land(),expected)
        self.assertEqual(w.p['modifiers'][MARKER],-1)

    def test_missing_funds_garrison_or_same_country_interface_prevents_payment(self):
        mutations = [lambda w: w.countries['A']['resources'].update(alloys=299),
            lambda w: w.countries['A']['resources'].update(consumer_goods=199),
            lambda w: w.countries['A']['resources'].update(energy=499),
            lambda w: w.countries['A']['techs'].remove(TECH),
            lambda w: w.p['flags'].clear(),
            lambda w: w.p['inactive'].add(CENTER),
            lambda w: w.p.update(controller=w.countries['B']),
            lambda w: w.station['buildings'].clear(),
            lambda w: w.station.update(controller=w.countries['B']),
            lambda w: w.station.update(owner=w.countries['B'],controller=w.countries['B']),
            lambda w: w.systems['S'].update(starbase=None)]
        for i,mutate in enumerate(mutations):
            with self.subTest(case=i):
                w = World(); mutate(w); before = deepcopy(w.countries['A']['resources'])
                self.assertFalse(w.choose()); self.assertEqual(w.countries['A']['resources'],before)
                self.assertNotIn(MARKER,w.p['modifiers'])

    def test_pause_and_restore_share_bonus_and_upkeep_guard(self):
        w = World(); self.assertTrue(w.choose()); expected = w.land()
        pairs = [(lambda: w.p['inactive'].add(CENTER),lambda: w.p['inactive'].clear()),
            (lambda: w.p.update(controller=w.countries['B']),lambda: w.p.update(controller=w.countries['A'])),
            (lambda: w.station.update(controller=w.countries['B']),lambda: w.station.update(controller=w.countries['A'])),
            (lambda: w.station['buildings'].clear(),lambda: w.station['buildings'].add(LINK)),
            (lambda: w.countries['A']['techs'].remove(TECH),lambda: w.countries['A']['techs'].add(TECH))]
        for stop,resume in pairs:
            stop()
            self.assertEqual(w.land()[0]['army_defense_damage_mult'],0)
            self.assertEqual(w.land()[1],{})
            self.assertEqual(w.orbital(),dict(ship_fire_rate_mult=0,ship_tracking_add=0))
            self.assertIn(MARKER,w.p['modifiers'])
            resume(); self.assertEqual(w.land(),expected)
        # 正在轰炸不会把已部署的防务当成不安全工程暂停。
        w.p['bombarded'] = True; self.assertEqual(w.land(),expected)

    def test_withdrawal_and_existing_transfer_cleanup_do_not_refund_or_inherit(self):
        w = World(); self.assertTrue(w.choose()); w.p['modifiers']['other_project'] = -1
        before = deepcopy(w.countries['A']['resources'])
        self.assertTrue(w.choose('disable'))
        self.assertEqual(w.p['modifiers'],{'other_project':-1})
        self.assertIn('artifact_garrison_enabled',w.p['flags'])
        self.assertEqual(w.countries['A']['resources'],before)
        w.countries['A']['resources'].update(energy=500,alloys=300,consumer_goods=200)
        self.assertTrue(w.choose())
        w.p.update(owner=w.countries['B'],controller=w.countries['B'])
        self.assertEqual(w.land()[1],{})
        # 原生回调本身仍由引擎负责；这里执行被登记的正式清理事件效果。
        self.assertTrue(w.condition(child(EVENT,'trigger'),[w.p]))
        w.execute(child(EVENT,'immediate'),[w.p])
        self.assertNotIn(MARKER,w.p['modifiers'])
        self.assertNotIn('artifact_garrison_enabled',w.p['flags'])
        self.assertNotIn(('planet','P'),w.origins)
        self.assertEqual(w.p['modifiers'],{'other_project':-1})

    def test_each_colony_pays_but_starbase_bonus_never_stacks(self):
        w = World(); q = w.add_planet('Q')
        w.countries['A']['resources'].update(energy=1000,alloys=600,consumer_goods=400)
        self.assertTrue(w.choose()); first = w.orbital()
        self.assertTrue(w.choose(planet=q)); self.assertEqual(w.orbital(),first)
        self.assertEqual(w.land()[1],dict(energy=4,alloys=1))
        self.assertEqual(w.land(q)[1],dict(energy=4,alloys=1))
        self.assertTrue(w.choose('disable')); self.assertEqual(w.orbital(),first)
        self.assertTrue(w.choose('disable',q)); self.assertEqual(w.orbital(),dict(ship_fire_rate_mult=0,ship_tracking_add=0))

    def test_real_carrier_index_and_system_ownership_are_required(self):
        w = World(); self.assertTrue(w.choose())
        self.assertFalse(w.condition(TRIGGERS['artifact_joint_defense_operational'],[w.colony(w.p)]))
        # 无关ROOT不改变两条PREV链解析到的真实行星/星港。
        self.assertTrue(w.condition(TRIGGERS['artifact_joint_defense_has_orbital_link'],[{},w.p]))
        self.assertTrue(w.condition(TRIGGERS['artifact_joint_defense_station_active'],[{},w.station]))
        w.systems['S']['colonies'].remove(w.p)
        w.systems['T']['colonies'].append(w.p); w.p['solar_system'] = w.systems['T']
        self.assertEqual(w.orbital(),dict(ship_fire_rate_mult=0,ship_tracking_add=0))
        foreign = w.add_planet('foreign','B'); foreign['modifiers'][MARKER] = -1
        self.assertEqual(w.orbital(),dict(ship_fire_rate_mult=0,ship_tracking_add=0))
        self.assertEqual(w.orbital(w.systems['T']['starbase']),dict(ship_fire_rate_mult=.15,ship_tracking_add=10))


if __name__ == '__main__':
    unittest.main()
