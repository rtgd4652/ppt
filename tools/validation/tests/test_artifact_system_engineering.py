"""执行E11正式脚本及原E09/D13消费者，核对异星系、实付和清理。

复用已有严格作用域栈，保留殖民地/行星不同身份。原生建筑施工、界面、
费用显示、巨构容量及存读档为外部契约，本包不创建或运行游戏场景。
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_observation_calibration as calibration

base, child = calibration.joint.base, calibration.child
load = base.load
TECH = 'tech_artifact_interstellar_engineering_coordination'
E09 = 'tech_artifact_segmented_large_engineering'
D13 = 'tech_artifact_terminal_hull_support'
B14 = 'tech_artifact_strategic_engineering_supply'
YARD = 'building_artifact_engineering_supply_yard'
LARGE = 'building_artifact_large_engineering_yard'
DEPOT = 'building_artifact_distribution_depot'
TERMINAL = 'building_artifact_intercolony_terminal'
ROLE = 'acs_remote_engineering_receiver'
STOCK = 'acs_strategic_supply_reserved'
TRIGGERS = load('mod/common/scripted_triggers/artifact_system_engineering_triggers.txt')
EFFECTS = load('mod/common/scripted_effects/artifact_system_engineering_effects.txt')
DECISIONS = load('mod/common/decisions/artifact_system_engineering_decisions.txt')
OLD = load('mod/common/decisions/artifact_civil_supply_decisions.txt')
BUILDING = load('mod/common/buildings/artifact_segmented_engineering_buildings.txt')[LARGE]


class World(calibration.World):
    def __init__(self):
        super().__init__()
        for country in self.countries.values():
            country['techs'].update({TECH, E09, D13, B14,
                *load('mod/common/technology/artifact_civil_supply_technology.txt')})
            country['resources'] = dict(energy=50000, minerals=50000, alloys=50000,
                                        consumer_goods=50000, unity=50000)
        for p in self.planets.values():
            p['buildings'] = {YARD, DEPOT, TERMINAL}
        self.q['buildings'].add(LARGE)

    def add_planet(self, key, country='A', system='S'):
        p = super().add_planet(key, country, system)
        p.update(vars={}, bombarded=False)
        return p

    def term(self, e, stack):
        if e.key == 'has_resource':
            obj = stack[-1]; assert obj['kind'] == 'country'
            return obj['resources'][base.scalar(e.value, 'type')] >= float(base.scalar(e.value, 'amount_ge'))
        return super().term(e, stack)

    def execute(self, entries, stack):
        if not any(e.key in ('random_owned_colony', 'add_resource') for e in entries):
            return super().execute(entries, stack)
        assert not any(e.key in ('else', 'else_if') for e in entries)
        obj = stack[-1]; assert obj['kind'] == 'country'
        for e in entries:
            if e.key == 'add_resource':
                for resource in e.value: obj['resources'][resource.key] += float(resource.value)
            elif e.key == 'random_owned_colony':
                targets = [p for p in self.planets.values() if p['colony'] and p['owner'] is obj
                    and self.condition(child(e.value, 'limit'), stack+[self.colony(p)])]
                # 正常登记保证全国唯一，避免确定性夹具掩盖模糊目标。
                assert len(targets) == 1, '交付必须恰有一个合格工程目标'
                self.execute([x for x in e.value if x.key != 'limit'], stack+[self.colony(targets[0])])
            else:
                super().execute([e], stack)

    def use(self, action, p=None, old=False):
        p = self.p if p is None else p
        d = OLD['decision_artifact_civil_'+action] if old else DECISIONS['decision_artifact_system_engineering_'+action]
        if not all(self.condition(child(d, key, []), [p]) for key in ('potential', 'allow')):
            return False
        self.execute(child(d, 'effect'), [p]); return True

    def force(self, action, p=None):
        self.execute(EFFECTS['artifact_system_engineering_'+action], [self.p if p is None else p])

    def prepare(self):
        assert self.use('register_receiver', old=True)
        assert self.use('reserve', old=True)
        assert self.use('strategic_reserve', old=True)
        assert self.use('register', self.q)

    def move(self, p, system):
        p['solar_system']['colonies'].remove(p)
        p['solar_system'] = self.systems[system]
        self.systems[system]['colonies'].append(p)

    def state(self):
        # 投影为非循环账本；不把深拷贝当存读档。
        return deepcopy((self.a['resources'],
            {p['id']:(p['modifiers'],p['flags'],p['vars']) for p in self.planets.values()},
            {key:(obj['kind'],obj['id']) for key,obj in self.targets.items()}))

    def capacity(self):
        block = child(BUILDING, 'triggered_country_modifier')
        return sum(float(base.scalar(block, 'country_megastructure_build_cap_add'))
            for p in self.planets.values() if p['owner'] is self.a and LARGE in p['buildings']-p['inactive']
            and self.condition(child(block, 'potential'), [self.colony(p)]))


class SystemEngineeringTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(calibration.TRIGGERS, TRIGGERS))
        self.enterContext(patch.dict(calibration.EFFECTS, EFFECTS))

    def test_registration_is_free_unique_and_checks_country_and_different_system(self):
        w = World(); before = w.state()
        self.assertFalse(w.use('register', w.q)); self.assertEqual(w.state(), before)
        self.assertTrue(w.use('register_receiver', old=True))
        before_resources = deepcopy(w.a['resources'])
        w.move(w.q, 'S'); self.assertFalse(w.use('register', w.q))
        w.move(w.q, 'T')
        # 异国接收端在目标星系不应被误认成本国始发地。
        foreign = w.add_planet('R', country='B', system='T')
        foreign['modifiers']['acs_link_receiver'] = -1
        self.assertTrue(w.use('register', w.q)); self.assertFalse(w.use('register', w.q))
        extra = w.add_planet('X', system='T'); extra['buildings'] = {YARD, DEPOT, TERMINAL}
        self.assertFalse(w.use('register', extra))
        self.assertIn('acs_link_receiver', w.p['modifiers'])
        self.assertNotIn('acs_link_receiver', w.q['modifiers'])
        self.assertEqual(w.a['resources'], before_resources)

    def test_real_pack_moves_once_and_completes_existing_segmented_project(self):
        w = World(); before = deepcopy(w.a['resources']); w.prepare()
        self.assertTrue(w.use('dispatch')); self.assertNotIn(STOCK, w.p['modifiers'])
        self.assertIn(STOCK, w.q['modifiers']); paid = w.state()
        self.assertFalse(w.use('dispatch')); w.force('dispatch'); self.assertEqual(w.state(), paid)
        # 在目标端不能凭空再集成备料，也不能从工程角色接力发运。
        self.assertFalse(w.use('strategic_reserve', w.q, old=True))
        self.assertFalse(w.use('dispatch', w.q))
        self.assertTrue(w.use('segmented_start', w.q, old=True))
        self.assertNotIn(STOCK, w.q['modifiers'])
        for _ in range(3): w.monthly()
        self.assertTrue(w.use('segmented_assemble', w.q, old=True))
        for _ in range(4): w.monthly()
        self.assertTrue(w.use('segmented_commission', w.q, old=True))
        for _ in range(2): w.monthly()
        self.assertEqual(w.capacity(), 1)
        expected = {**before, 'minerals':before['minerals']-3000, 'alloys':before['alloys']-2500,
                    'energy':before['energy']-2000, 'consumer_goods':before['consumer_goods']-300}
        self.assertEqual(w.a['resources'], expected)
        self.assertTrue(w.use('unregister', w.q)); self.assertEqual(w.capacity(), 1)

    def test_delivered_pack_supports_hull_trial_without_live_origin(self):
        w = World(); w.prepare(); self.assertTrue(w.use('dispatch'))
        self.assertTrue(w.use('hull_start', w.q, old=True)); self.assertNotIn(STOCK, w.q['modifiers'])
        # 材料已到货，始发接收端退出不应令试验凭空停工。
        self.assertTrue(w.use('unregister', old=True)); w.p['inactive'].add(YARD)
        for _ in range(6): w.monthly()
        self.assertIn('acs_hull_qualified', w.a['modifiers'])
        w.q['owner'] = w.q['controller'] = w.countries['B']
        e = calibration.CIV_EVENTS['artifact_civil_supply.2']
        w.execute(child(e, 'immediate'), [w.q])
        self.assertNotIn(ROLE, w.q['modifiers'])
        self.assertIn('acs_hull_qualified', w.a['modifiers'])
        self.assertNotIn('acs_hull_qualified', w.countries['B']['modifiers'])

    def test_failed_delivery_preserves_fee_and_origin_stock(self):
        w = World(); w.prepare()
        for stop, resume in (
            (lambda: w.a['resources'].update(energy=499), lambda: w.a['resources'].update(energy=49000)),
            (lambda: w.q.update(controller=w.countries['B']), lambda: w.q.update(controller=w.a)),
            (lambda: w.q['inactive'].add(TERMINAL), lambda: w.q['inactive'].clear()),
            (lambda: w.q.update(bombarded=True), lambda: w.q.update(bombarded=False)),
            (lambda: w.a['techs'].remove(TECH), lambda: w.a['techs'].add(TECH)),
            (lambda: w.move(w.q, 'S'), lambda: w.move(w.q, 'T')),
            (lambda: w.q.update(owner=w.countries['B'],controller=w.countries['B']),
             lambda: w.q.update(owner=w.a,controller=w.a)),
        ):
            stop(); before = w.state()
            self.assertFalse(w.use('dispatch')); w.force('dispatch'); self.assertEqual(w.state(), before)
            self.assertIn(STOCK, w.p['modifiers']); resume()
        self.assertTrue(w.use('dispatch'))

    def test_cancelled_role_pauses_resumes_then_transfer_cleans_project(self):
        w = World(); w.prepare(); self.assertTrue(w.use('dispatch'))
        self.assertTrue(w.use('segmented_start', w.q, old=True)); w.monthly(); w.monthly()
        paid = deepcopy(w.a['resources'])
        self.assertTrue(w.use('unregister', w.q)); w.monthly()
        self.assertEqual(w.q['vars']['acs_segmented_work'], 2)
        self.assertTrue(w.use('register', w.q)); w.monthly()
        self.assertIn('acs_segmented_prepared', w.q['modifiers'])
        self.assertEqual(w.a['resources'], paid)
        w.q['owner'] = w.q['controller'] = w.countries['B']
        w.execute(child(calibration.CIV_EVENTS['artifact_civil_supply.2'], 'immediate'), [w.q])
        self.assertNotIn(ROLE, w.q['modifiers']); self.assertNotIn('acs_segmented_project', w.q['modifiers'])
        self.assertNotIn('acs_segmented_work', w.q['vars'])
        self.assertEqual(w.a['resources'], paid)

    def test_stock_after_unregistration_refunds_once_and_destruction_loses_stock(self):
        for outcome in ('refund', 'destroy'):
            with self.subTest(outcome=outcome):
                w = World(); w.prepare(); self.assertTrue(w.use('dispatch'))
                paid = deepcopy(w.a['resources'])
                if outcome == 'refund':
                    self.assertTrue(w.use('unregister', w.q)); self.assertIn(STOCK, w.q['modifiers'])
                    self.assertTrue(w.use('strategic_release', w.q, old=True))
                    self.assertFalse(w.use('strategic_release', w.q, old=True))
                    self.assertEqual(w.a['resources'], {**paid,'minerals':paid['minerals']+1600,'alloys':paid['alloys']+800})
                else:
                    w.execute(child(calibration.CIV_EVENTS['artifact_civil_supply.3'], 'immediate'), [w.q])
                    self.assertNotIn(ROLE, w.q['modifiers']); self.assertNotIn(STOCK, w.q['modifiers'])
                    self.assertEqual(w.a['resources'], paid)


if __name__ == '__main__':
    unittest.main()
