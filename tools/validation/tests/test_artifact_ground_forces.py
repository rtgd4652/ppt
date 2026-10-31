"""读取正式R3c条件，检查驻防名额和维护边界；不模拟引擎生成陆军或存读档。"""
from copy import deepcopy
import unittest
import test_artifact_city_planning as city
from check_mod import scalar

TECH = 'tech_artifact_planetary_garrison'
FLAG = 'artifact_garrison_enabled'
CENTER = 'building_artifact_community_service_center'
BRANCH = 'building_artifact_sanctum'
DECISIONS = city.load('mod/common/decisions/artifact_garrison_decisions.txt')
EFFECTS = city.load('mod/common/scripted_effects/artifact_garrison_effects.txt')
ARMY = city.load('mod/common/armies/artifact_ground_forces_armies.txt')['artifact_precision_landing_army']


class GroundForcesTests(unittest.TestCase):
    def setUp(self):
        self.country = dict(kind='country', species='ARTIFACT_USER', techs={TECH},
                            resources={'minerals':1000, 'energy':1000})
        self.site = dict(kind='planet', scope_id=3, owner=self.country, controller=self.country,
                         buildings={CENTER}, inactive=set(), markers=set(), queued=set(),
                         carrier_flags=set(), bombarded=False, garrison_owners={})

    def evaluate_effect(self, entries):
        for e in entries:
            if e.key in EFFECTS:
                self.evaluate_effect(EFFECTS[e.key])
            elif e.key == 'if':
                if city.condition(city.block(e.value,'limit'),self.site):
                    self.evaluate_effect([x for x in e.value if x.key != 'limit'])
            elif e.key == 'hidden_effect':self.evaluate_effect(e.value)
            elif e.key == 'custom_tooltip':pass
            elif e.key == 'remove_carrier_flag':self.site['carrier_flags'].discard(e.value)
            elif e.key == 'remove_modifier':self.site['markers'].discard(e.value)
            elif e.key == 'set_carrier_flag':self.site['carrier_flags'].add(e.value)
            elif e.key == 'clear_global_event_target':
                self.assertEqual(e.value,'artifact_garrison_owner@this')
                self.site['garrison_owners'].pop(('planet', self.site['scope_id']), None)
            elif e.key == 'owner':
                self.assertEqual([(x.key,x.value) for x in e.value],
                    [('save_global_event_target_as','artifact_garrison_owner@prev')])
                self.site['garrison_owners'][('planet', self.site['scope_id'])]=self.site['owner']
            else:raise AssertionError(('unsupported effect',e.key))

    def choose(self, name='enable'):
        decision=DECISIONS['decision_artifact_'+name+'_garrison']
        if not (city.condition(city.block(decision,'potential'),self.site)
                and city.condition(city.block(decision,'allow'),self.site)):return False
        costs=city.block(city.block(decision,'resources'),'cost')
        if any(self.site['owner']['resources'].get(e.key,0)<float(e.value) for e in costs):return False
        for e in costs:self.site['owner']['resources'][e.key]-=float(e.value)
        self.evaluate_effect(city.block(decision,'effect'));return True

    def result(self):
        count=0;extra={}
        # 对照实际存档：首都殖民地0承载于行星3，建筑从殖民地求值。
        building_site=dict(self.site,kind='colony',scope_id=0,carrier=self.site)
        for key in (CENTER,BRANCH):
            b=city.BUILDINGS[key]
            for e in b:
                if e.key=='triggered_planet_modifier' and city.condition(city.block(e.value,'potential'),building_site):
                    count+=float(scalar(e.value,'planet_defense_armies_add') or 0)
            self.assertEqual(sum(e.key=='resources' for e in b),1)
            for u in city.block(b,'resources'):
                if u.key=='upkeep' and city.block(u.value,'trigger') and city.condition(city.block(u.value,'trigger'),building_site):
                    for r in u.value:
                        if r.key!='trigger':extra[r.key]=extra.get(r.key,0)+float(r.value)
        return count,extra

    def test_paid_deployment_is_single_and_clear_only_removes_its_state(self):
        self.assertTrue(self.choose());self.assertEqual(self.country['resources'],{'minerals':700,'energy':850})
        self.assertFalse(self.choose());self.assertEqual(self.result(),(2,{'energy':4,'consumer_goods':1}))
        before=deepcopy(self.country['resources'])
        self.site['carrier_flags'].add('unrelated_project')
        self.evaluate_effect(EFFECTS['artifact_garrison_deploy'])
        self.assertEqual(self.country['resources'],before)
        self.assertTrue(self.choose('disable'));self.assertEqual(self.result(),(0,{}))
        self.assertEqual(self.site['carrier_flags'],{'unrelated_project'})
        self.assertEqual(self.country['resources'],before)

    def test_both_facilities_do_not_duplicate_and_source_loss_stops_cost_and_capacity(self):
        self.assertTrue(self.choose());expected=self.result()
        self.site['buildings'].add(BRANCH);self.assertEqual(self.result(),expected)
        self.site['inactive'].add(BRANCH);self.assertEqual(self.result(),expected)
        self.site['inactive'].add(CENTER);self.assertEqual(self.result(),(0,{}))
        self.site['inactive'].clear();self.assertEqual(self.result(),expected)
        self.site['buildings'].clear();self.assertEqual(self.result(),(0,{}))
        self.assertTrue(self.choose('disable'))

    def test_occupation_qualification_and_transfer_do_not_give_free_new_owner_armies(self):
        self.assertTrue(self.choose());self.site['controller']=None;self.assertEqual(self.result(),(0,{}))
        self.site['controller']=self.country;self.assertEqual(self.result()[0],2)
        self.country['techs'].clear();self.assertEqual(self.result(),(0,{}));self.country['techs'].add(TECH)
        other=dict(kind='country',species='ARTIFACT_USER',techs={TECH},resources={'minerals':500,'energy':500})
        self.site.update(owner=other,controller=other);self.assertEqual(self.result(),(0,{}))
        self.evaluate_effect(EFFECTS['artifact_garrison_clear'])
        self.site.update(owner=self.country,controller=self.country);self.assertEqual(self.result(),(0,{}))
        self.assertTrue(self.choose())

    def test_insufficient_resources_invalid_source_or_bombardment_cannot_start(self):
        self.site['bombarded']=True;self.assertFalse(self.choose());self.site['bombarded']=False
        self.country['resources']['minerals']=299;self.assertFalse(self.choose())
        self.country['resources']['minerals']=1000;self.site['inactive']={CENTER};self.assertFalse(self.choose())
        self.assertFalse(self.site['garrison_owners']);self.assertNotIn(FLAG,self.site['carrier_flags'])

    def test_building_colony_index_is_not_the_decision_carrier_index(self):
        self.assertTrue(self.choose())
        colony=dict(self.site,kind='colony',scope_id=0,carrier=self.site)
        # 缺少显式planet跳转时会错查owner0，重现名额和维护同时失效的问题。
        self.assertFalse(city.condition(city.GARRISON_TRIGGERS['artifact_garrison_operational'],colony))
        self.assertEqual(self.result(),(2,{'energy':4,'consumer_goods':1}))
        self.site['garrison_owners'][('colony',0)]=self.country
        self.site['garrison_owners'].pop(('planet',3))
        self.assertEqual(self.result(),(0,{}))

    def test_landing_tradeoff_and_native_cleanup_without_monthly_spawn_loop(self):
        self.assertLess(float(scalar(ARMY,'damage')),1.05)
        self.assertEqual(float(scalar(ARMY,'collateral_damage')),0.2)
        self.assertEqual(scalar(ARMY,'time'),'120')
        self.assertNotIn('defensive',{e.key for e in ARMY})
        actions=city.load('mod/common/on_actions/artifact_garrison_on_actions.txt')
        self.assertEqual(set(actions),{'on_colony_transfer','on_colony_ownerless','on_colony_destroyed'})
        for body in actions.values():self.assertIn('artifact_garrison.1',[e.value for e in city.block(body,'events')])
        event=city.load('mod/events/artifact_garrison_events.txt')['carrier_event']
        self.assertEqual([(e.key,e.value) for e in city.block(event,'immediate')],[('artifact_garrison_clear','yes')])


if __name__=='__main__':unittest.main()
