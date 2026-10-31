"""执行A09正式脚本与既有月度/轨道消费者，检查两端、付款、归属与窗口。

复用已存在的作用域解释器，原生决议扣费、计时、显示和序列化仍是外部契约。
不创建游戏场景、不把变量深拷贝或夹具通过当作真实存读档/传感验证。
"""
from copy import deepcopy
import re
import unittest

import test_artifact_joint_defense as joint
from check_mod import parse, scalar

ROOT, child = joint.ROOT, joint.child
TECH = 'tech_artifact_cross_colony_calibration'
LONG = 'building_artifact_long_baseline_array'
OBS = 'building_artifact_baseline_observation_station'
ARCHIVE = 'aoc_calibration_archive'
TRIGGERS = {**joint.base.load('mod/common/scripted_triggers/artifact_civil_supply_triggers.txt'),
            **joint.base.load('mod/common/scripted_triggers/artifact_civil_engineering_triggers.txt'),
            **joint.base.load('mod/common/scripted_triggers/artifact_observation_calibration_triggers.txt')}
EFFECTS = {**joint.base.load('mod/common/scripted_effects/artifact_civil_supply_effects.txt'),
           **joint.base.load('mod/common/scripted_effects/artifact_observation_calibration_effects.txt')}
DECISIONS = joint.base.load('mod/common/decisions/artifact_observation_calibration_decisions.txt')
def events(path):
    return {scalar(e.value,'id'):e.value for e in parse((ROOT/path).read_text(encoding='utf-8')) if e.key.endswith('_event')}
CIV_EVENTS = events('mod/events/artifact_civil_supply_events.txt')
UI = events('mod/events/artifact_observation_calibration_events.txt')['artifact_observation_calibration.1']


class World(joint.World):
    def __init__(self):
        super().__init__()
        self.targets, self.local = {}, {}
        self.notifications = []
        for c in self.countries.values():
            c.update(ai=False,modifiers={},vars={})
            c['techs'] = {TECH,'tech_artifact_long_baseline_measurement','tech_artifact_seven_day_logistics',joint.ORBITAL}
            c['resources'] = dict(energy=5000,consumer_goods=2000,alloys=1000)
        self.q = self.add_planet('Q',system='T')
        for p,building in [(self.p,LONG),(self.q,OBS)]:
            p.update(vars={},bombarded=False)
            p['flags'].clear(); p['buildings'] = {building}
        self.a = self.countries['A']

    def colony(self, p):
        return dict(super().colony(p),carrier=p)

    def key(self, name, stack):
        stem,index = name.split('@')
        obj = self.resolve(index,stack) if index != 'this' else stack[-1]
        return stem+'@'+obj['kind']+':'+obj['id']

    def resolve(self, path, stack):
        if path.startswith('event_target:'):
            name = path[len('event_target:'):]
            return self.targets.get(self.key(name,stack)) if '@' in name else self.local.get(name)
        if path == 'this': return stack[-1]
        return super().resolve(path,stack)

    def term(self, e, stack):
        k,v,obj = e.key,e.value,stack[-1]
        if k in TRIGGERS: return self.condition(TRIGGERS[k],stack) == (v == 'yes')
        if k.startswith('event_target:') or k == 'carrier' or re.fullmatch(r'(prev)+',k):
            target = self.resolve(k,stack)
            return target is not None and self.condition(v,stack+[target])
        if k == 'is_ai': return obj['ai'] == (v == 'yes')
        if k == 'has_building': return v in obj['buildings']
        if k == 'is_same_value': return obj is self.resolve(v,stack)
        if k == 'has_orbital_bombardment': return obj['bombarded'] == (v == 'yes')
        if k == 'is_occupied_flag': return (obj['owner'] is not obj['controller']) == (v == 'yes')
        if k == 'any_owned_colony':
            return any(self.condition(v,stack+[self.colony(p)]) for p in self.planets.values()
                       if p['colony'] and p['owner'] is obj)
        if k == 'check_variable': return obj['vars'].get(scalar(v,'which'),0) >= float(scalar(v,'value_ge'))
        return super().term(e,stack)

    def execute(self, entries, stack):
        taken = None
        for e in entries:
            k,v,obj = e.key,e.value,stack[-1]
            if k in ('if','else_if','else'):
                if k == 'if': taken = False
                if not taken and (k == 'else' or self.condition(child(v,'limit'),stack)):
                    taken = True
                    self.execute([x for x in v if x.key != 'limit'],stack)
                continue
            taken = None
            if k in EFFECTS: self.execute(EFFECTS[k],stack)
            elif k in ('owner','carrier') or k.startswith('event_target:'):
                self.execute(v,stack+[self.resolve(k,stack)])
            elif k == 'save_event_target_as': self.local[v] = obj
            elif k == 'save_global_event_target_as': self.targets[self.key(v,stack)] = obj
            elif k == 'clear_global_event_target': self.targets.pop(self.key(v,stack),None)
            elif k == 'set_carrier_flag': obj['flags'].add(v)
            elif k == 'clear_variable': obj['vars'].pop(v,None)
            elif k in ('set_variable','change_variable'):
                name,value = scalar(v,'which'),float(scalar(v,'value'))
                obj['vars'][name] = value+(obj['vars'].get(name,0) if k == 'change_variable' else 0)
            elif k == 'every_owned_colony':
                for p in self.planets.values():
                    if not p['colony'] or p['owner'] is not obj: continue
                    current = stack+[self.colony(p)]
                    if self.condition(child(v,'limit'),current):
                        self.execute([x for x in v if x.key != 'limit'],current)
            elif k == 'country_event': self.notifications.append(scalar(v,'id'))
            else: super().execute([e],stack)

    def choose(self, name, planet=None):
        p = self.p if planet is None else planet
        d = DECISIONS['decision_artifact_observation_'+name]
        if not all(self.condition(child(d,key,[]),[p]) for key in ('potential','allow')): return False
        # 外部原生费用契约；正式效果中如另写资源扣除，严格解释器会失败。
        cost = child(child(d,'resources',[]),'cost',[])
        resources = p['owner']['resources']
        if any(resources.get(e.key,0) < float(e.value) for e in cost): return False
        for e in cost: resources[e.key] -= float(e.value)
        self.execute(child(d,'effect'),[p]); return True

    def pair(self):
        assert self.choose('register_source')
        assert self.choose('register_peer',self.q)

    def monthly(self):
        e = CIV_EVENTS['artifact_civil_supply.1']
        if self.condition(child(e,'trigger'),[self.a]): self.execute(child(e,'immediate'),[self.a])

    def finish(self):
        self.pair(); assert self.choose('start')
        for _ in range(6): self.monthly()

    def support(self, system='T'):
        station = self.systems[system]['starbase']
        values = dict(ship_sensor_range_add=0,ship_hyperlane_range_add=0)
        for e in joint.STATION:
            if e.key == 'triggered_station_modifier' and self.condition(child(e.value,'potential'),[station]):
                for key in values: values[key] += float(scalar(e.value,key) or 0)
        return values

    def elapsed(self, days):
        for obj in [*self.countries.values(),*self.planets.values()]:
            obj['modifiers'] = {k:(-1 if left < 0 else left-days) for k,left in obj['modifiers'].items()
                                if left < 0 or left > days}

    def status(self):
        return [scalar(e.value,'text') for e in UI if e.key == 'desc' and self.condition(child(e.value,'trigger'),[self.a])]


class ObservationCalibrationTests(unittest.TestCase):
    def test_fixed_remote_pair_pays_once_and_six_months_archive_once(self):
        w = World(); self.assertTrue(w.choose('register_source'))
        r = w.add_planet('R'); r.update(vars={},bombarded=False); r['flags'].clear(); r['buildings'] = {OBS}
        self.assertFalse(w.choose('register_peer',r))
        self.assertFalse(w.choose('register_source'))
        self.assertTrue(w.choose('register_peer',w.q))
        self.assertIs(w.targets['aoc_source@country:A'],w.p)
        self.assertIs(w.targets['aoc_peer@country:A'],w.q)
        w.a['resources'] = dict(energy=600,consumer_goods=300,alloys=100)
        w.p['modifiers']['acs_supply_reserved'] = -1
        self.assertTrue(w.choose('start')); self.assertFalse(w.choose('start'))
        self.assertEqual(w.a['resources'],dict(energy=0,consumer_goods=0,alloys=0))
        for _ in range(5): w.monthly()
        self.assertNotIn(ARCHIVE,w.a['modifiers']); self.assertEqual(w.a['vars']['aoc_work'],5)
        w.monthly(); self.assertIn(ARCHIVE,w.a['modifiers'])
        self.assertNotIn('aoc_tracking',w.a['modifiers'])
        self.assertNotIn('aoc_source@country:A',w.targets)
        self.assertNotIn('aoc_peer@country:A',w.targets)
        self.assertIn('acs_supply_reserved',w.p['modifiers'])
        self.assertNotIn('acs_observation_source',w.p['modifiers'])
        self.assertEqual(w.notifications,['artifact_observation_calibration.1'])
        w.monthly(); self.assertEqual(len(w.notifications),1)
        self.assertFalse(w.choose('register_source'))

    def test_control_facility_or_bombardment_pauses_and_status_never_advances(self):
        w = World(); self.assertEqual(w.status(),['aoc.intro'])
        w.pair(); self.assertEqual(w.status(),['aoc.pairing'])
        self.assertTrue(w.choose('start')); w.monthly()
        self.assertEqual(w.status(),['aoc.working'])
        pairs = [(lambda: w.q.update(controller=w.countries['B']),lambda: w.q.update(controller=w.a)),
            (lambda: w.p['inactive'].add(LONG),lambda: w.p['inactive'].clear()),
            (lambda: w.q.update(bombarded=True),lambda: w.q.update(bombarded=False))]
        for stop,resume in pairs:
            stop(); before = w.a['vars']['aoc_work']; w.monthly()
            self.assertEqual(w.a['vars']['aoc_work'],before)
            self.assertEqual(w.status(),['aoc.paused'])
            resources = deepcopy(w.a['resources']); self.assertTrue(w.choose('status'))
            self.assertEqual(w.a['vars']['aoc_work'],before); self.assertEqual(w.a['resources'],resources)
            resume(); w.monthly(); self.assertEqual(w.a['vars']['aoc_work'],before+1)

    def test_transfer_or_destroy_cancels_even_when_no_owned_managed_colonies_remain(self):
        for destroyed in (False,True):
            with self.subTest(destroyed=destroyed):
                w = World(); w.pair(); self.assertTrue(w.choose('start')); w.monthly()
                before = deepcopy(w.a['resources'])
                if destroyed:
                    w.execute(child(CIV_EVENTS['artifact_civil_supply.3'],'immediate'),[w.p])
                    w.p['colony'] = False
                else:
                    for p in (w.p,w.q):
                        p.update(owner=w.countries['B'],controller=w.countries['B'])
                        w.execute(child(CIV_EVENTS['artifact_civil_supply.2'],'immediate'),[p])
                w.monthly()
                self.assertNotIn('aoc_tracking',w.a['modifiers'])
                self.assertNotIn('aoc_calibrating',w.a['modifiers'])
                self.assertNotIn(ARCHIVE,w.countries['B']['modifiers'])
                self.assertEqual(w.a['resources'],before)

    def test_insufficient_native_fees_and_cancellation_preserve_other_work(self):
        for key,amount in [('energy',599),('consumer_goods',299),('alloys',99)]:
            w = World(); w.pair(); w.a['resources'][key] = amount
            before = deepcopy(w.a['resources']); self.assertFalse(w.choose('start'))
            self.assertEqual(w.a['resources'],before)
            self.assertNotIn('aoc_calibrating',w.a['modifiers'])
        w = World(); w.pair(); self.assertTrue(w.choose('start'))
        w.q['modifiers']['acs_supply_reserved'] = -1
        before = deepcopy(w.a['resources']); self.assertTrue(w.choose('cancel'))
        self.assertEqual(w.a['resources'],before)
        self.assertNotIn('aoc_tracking',w.a['modifiers'])
        self.assertIn('acs_supply_reserved',w.q['modifiers'])
        self.assertFalse(w.choose('cancel'))

    def test_archive_unlocks_paid_local_support_without_array_or_colony_stacking(self):
        w = World(); self.assertEqual(w.support(),dict(ship_sensor_range_add=0,ship_hyperlane_range_add=0))
        self.assertEqual(w.support('S'),dict(ship_sensor_range_add=1,ship_hyperlane_range_add=2))
        self.assertFalse(w.choose('apply',w.q)); w.finish()
        self.assertEqual(w.status(),['aoc.archived'])
        self.assertEqual(w.support(),dict(ship_sensor_range_add=0,ship_hyperlane_range_add=0))
        w.a['resources'] = dict(energy=300,consumer_goods=100,alloys=0)
        self.assertTrue(w.choose('apply',w.q)); self.assertFalse(w.choose('apply',w.q))
        self.assertEqual(w.a['resources'],dict(energy=0,consumer_goods=0,alloys=0))
        expected = dict(ship_sensor_range_add=1,ship_hyperlane_range_add=2)
        self.assertEqual(w.support(),expected)
        r = w.add_planet('R',system='T'); r.update(vars={},bombarded=False); r['flags'].clear(); r['buildings'] = {OBS}
        w.a['resources'].update(energy=300,consumer_goods=100)
        self.assertTrue(w.choose('apply',r)); self.assertEqual(w.support(),expected)
        # 完整阵列后来出现也只命中同一块原生修正，不形成第二份支持。
        w.q['buildings'].add(LONG); self.assertEqual(w.support(),expected)

    def test_local_window_pauses_expires_and_cannot_be_inherited(self):
        w = World(); w.finish(); self.assertTrue(w.choose('apply',w.q))
        w.q['inactive'].add(OBS); w.elapsed(20)
        self.assertEqual(w.support(),dict(ship_sensor_range_add=0,ship_hyperlane_range_add=0))
        self.assertEqual(w.q['modifiers']['acs_observation_window'],340)
        w.q['inactive'].clear(); self.assertEqual(w.support()['ship_sensor_range_add'],1)
        w.elapsed(340); self.assertNotIn('acs_observation_window',w.q['modifiers'])
        self.assertEqual(w.support()['ship_sensor_range_add'],0)
        self.assertIn(ARCHIVE,w.a['modifiers']); self.assertTrue(w.choose('apply',w.q))
        w.q.update(owner=w.countries['B'],controller=w.countries['B'])
        w.systems['T']['starbase'].update(owner=w.countries['B'],controller=w.countries['B'])
        w.countries['B']['modifiers'][ARCHIVE] = -1
        # 即使新国家已有自己的档案，也不能接管前任付费窗口。
        self.assertEqual(w.support()['ship_sensor_range_add'],0)
        w.execute(child(CIV_EVENTS['artifact_civil_supply.2'],'immediate'),[w.q])
        self.assertNotIn('acs_observation_window',w.q['modifiers'])
        self.assertIn(ARCHIVE,w.a['modifiers'])


if __name__ == '__main__':
    unittest.main()
