"""执行F03中心、实付准备与现场舰船效果；不模拟原生建造/战斗/读档。

F02/A12完成知识与D14既有驻防为已单独验证的接口输入，准备和部署走正式决议。
扩展严格作用域栈支持国家/行星/舰队/舰船；未知原生语法仍失败。
"""
from copy import deepcopy
import re
import unittest
from unittest.mock import patch

import test_artifact_crisis_intelligence as intelligence

calibration, child, load = intelligence.calibration, intelligence.child, intelligence.load
scalar = intelligence.scalar
TECH='tech_artifact_public_countermeasure_plan'
THEORY='tech_artifact_public_artifact_theory'
QUALIFIED='apt_public_engineering_methods'
BUILDING='building_artifact_crisis_joint_defense_center'
STOCK='acc_countermeasure_ready'
COOLDOWN='acc_recharging'
HIT='acc_projection_disrupted'
FLAG='aemusa_ms_anchor_projection'
TRIGGERS={**load('mod/common/scripted_triggers/artifact_public_theory_triggers.txt'),
          **load('mod/common/scripted_triggers/artifact_public_countermeasure_triggers.txt')}
EFFECTS=load('mod/common/scripted_effects/artifact_public_countermeasure_effects.txt')
DECISIONS=load('mod/common/decisions/artifact_public_countermeasure_decisions.txt')
BLUEPRINT=load('mod/common/buildings/artifact_public_countermeasure_buildings.txt')[BUILDING]
MODIFIERS=load('mod/common/static_modifiers/artifact_public_countermeasure_modifiers.txt')


class World(intelligence.World):
    def __init__(self):
        super().__init__()
        for c in self.countries.values():
            c['type']='default';c['hostile']=set()
            c['techs'].update({TECH,THEORY,calibration.joint.TECH,calibration.joint.GARRISON})
            c['resources']=dict(energy=50000,minerals=50000,alloys=50000,consumer_goods=50000,rare_crystals=50000)
        self.a['modifiers'].update({intelligence.ARCHIVE:-1,QUALIFIED:-1})
        self.p['buildings']={BUILDING,calibration.joint.HIGH}
        self.p['flags'].add('artifact_garrison_enabled');self.p['modifiers']['ajd_deployed']=-1
        self.targets['artifact_garrison_owner@planet:P']=self.a
        self.countries['B'].update(type='aemusa_convergence',hostile={'A'})
        self.countries['C']=dict(kind='country',id='C',type='default',hostile={'A'},techs=set(),
            resources={},modifiers={},flags=set(),vars={},species='HUM',ai=True)
        for s in self.systems.values():s['fleets']=[]
        self.fleets=[]
        self.actor=self.fleet('A','S')
        self.enemy=self.fleet('B','S',projection=True)

    def fleet(self,country,system,projection=False,ship_class='shipclass_military'):
        c=self.countries[country]
        f=dict(kind='fleet',id='fleet'+str(len(self.fleets)),owner=c,controller=c,
            solar_system=self.systems[system],civilian=False,cloaked=False,disabled=False,
            flags={FLAG} if projection else set(),ships=[])
        f['ships'].append(dict(kind='ship',ship_class=ship_class,disabled=False,modifiers={}))
        self.fleets.append(f);self.systems[system]['fleets'].append(f);return f

    def term(self,e,stack):
        k,v,obj=e.key,e.value,stack[-1]
        if k=='controller':
            target=self.resolve(k,stack)
            return target is not None and self.condition(v,stack+[target])
        if k=='is_country_type':assert obj['kind']=='country';return obj['type']==v
        if k=='has_fleet_flag':assert obj['kind']=='fleet';return v in obj['flags']
        if k in ('is_civilian','is_cloaked','is_disabled'):
            return obj[{'is_civilian':'civilian','is_cloaked':'cloaked','is_disabled':'disabled'}[k]]==(v=='yes')
        if k=='is_ship_class':assert obj['kind']=='ship';return obj['ship_class']==v
        if k=='is_hostile':return self.resolve(v,stack)['id'] in obj['hostile']
        if k=='any_owned_fleet':
            assert obj['kind']=='country'
            return any(self.condition(v,stack+[f]) for f in self.fleets if f['owner'] is obj)
        if k in ('any_fleet_in_system','any_owned_ship'):
            return any(self.condition(v,stack+[x]) for x in obj['fleets' if k=='any_fleet_in_system' else 'ships'])
        return super().term(e,stack)

    def execute(self,entries,stack):
        taken=None
        for e in entries:
            k,v,obj=e.key,e.value,stack[-1]
            if k in ('if','else_if','else'):
                if k=='if':taken=False
                if not taken and (k=='else' or self.condition(child(v,'limit'),stack)):
                    taken=True;self.execute([x for x in v if x.key!='limit'],stack)
                continue
            taken=None
            if k in ('solar_system','controller') or re.fullmatch(r'(prev)+',k):
                target=self.resolve(k,stack);assert target is not None
                self.execute(v,stack+[target])
            elif k=='random_owned_fleet':
                targets=[f for f in self.fleets if f['owner'] is obj
                         and self.condition(child(v,'limit'),stack+[f])]
                assert targets,'消费前后现场资格必须保持有效'
                self.execute([x for x in v if x.key!='limit'],stack+[targets[0]])
            elif k in ('every_fleet_in_system','every_owned_ship'):
                for x in obj['fleets' if k=='every_fleet_in_system' else 'ships']:
                    if self.condition(child(v,'limit'),stack+[x]):
                        self.execute([n for n in v if n.key!='limit'],stack+[x])
            else:super().execute([e],stack)

    def use(self,action,p=None):
        p=self.p if p is None else p
        d=DECISIONS['decision_artifact_public_countermeasure_'+action]
        if not all(self.condition(child(d,k,[]),[p]) for k in ('potential','allow')):return False
        resources,cost=p['owner']['resources'],child(child(d,'resources',[]),'cost',[])
        if any(resources.get(e.key,0)<float(e.value) for e in cost):return False
        for e in cost:resources[e.key]-=float(e.value)
        self.execute(child(d,'effect'),[p]);return True

    def force(self,action,p=None):self.execute(EFFECTS['artifact_public_countermeasure_'+action],[self.p if p is None else p])

    def elapsed(self,days):
        super().elapsed(days)
        for f in self.fleets:
            for s in f['ships']:
                s['modifiers']={k:(-1 if n<0 else n-days) for k,n in s['modifiers'].items() if n<0 or n>days}

    def state(self):
        return deepcopy((self.a['resources'],{p['id']:(p['modifiers'],p['flags'],p['vars']) for p in self.planets.values()},
            {c['id']:c['modifiers'] for c in self.countries.values()},
            [[s['modifiers'] for s in f['ships']] for f in self.fleets]))


class PublicCountermeasureTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(calibration.TRIGGERS,{**intelligence.review.TRIGGERS,**TRIGGERS}))
        self.enterContext(patch.dict(calibration.EFFECTS,EFFECTS))

    def test_real_knowledge_and_live_joint_defense_required_before_any_fee(self):
        for reason in ('signal','theory','research','garrison','orbital','disabled'):
            w=World()
            if reason=='signal':w.a['modifiers'].pop(intelligence.ARCHIVE)
            elif reason=='theory':w.a['modifiers'].pop(QUALIFIED)
            elif reason=='research':w.a['techs'].remove(TECH)
            elif reason=='garrison':w.p['flags'].discard('artifact_garrison_enabled')
            elif reason=='orbital':w.systems['S']['starbase']['buildings'].clear()
            else:w.p['inactive'].add(BUILDING)
            before=w.state();self.assertFalse(w.use('prepare'));w.force('prepare')
            self.assertEqual(w.state(),before)
        w=World();self.assertTrue(w.condition(child(BLUEPRINT,'allow'),[w.p]))
        self.assertEqual(scalar(child(BLUEPRINT,'empire_limit'),'base'),'1')
        self.assertEqual([e.value for e in child(BLUEPRINT,'prerequisites')],[TECH])

    def test_exact_prepare_once_paused_stock_still_unique_discard_preserves_other_stock(self):
        w=World();w.a['resources'].update(energy=800,alloys=500,rare_crystals=100)
        self.assertTrue(w.use('prepare'))
        self.assertEqual((w.a['resources']['energy'],w.a['resources']['alloys'],w.a['resources']['rare_crystals']),(0,0,0))
        paid=w.state();self.assertFalse(w.use('prepare'));w.force('prepare');self.assertEqual(w.state(),paid)
        w.p['inactive'].add(BUILDING)
        # 遗留多中心场景也不能绕过暂停库存的国家占位。
        q=w.q;q['buildings']=set(w.p['buildings']);q['flags'].add('artifact_garrison_enabled')
        q['modifiers']['ajd_deployed']=-1;w.targets['artifact_garrison_owner@planet:Q']=w.a
        w.a['resources'].update(energy=800,alloys=500,rare_crystals=100)
        self.assertFalse(w.use('prepare',q))
        w.p['modifiers']['acs_supply_reserved']=-1
        before=deepcopy(w.a['resources']);self.assertTrue(w.use('discard'))
        self.assertNotIn(STOCK,w.p['modifiers']);self.assertIn('acs_supply_reserved',w.p['modifiers'])
        self.assertEqual(w.a['resources'],before);self.assertFalse(w.use('discard'))

    def test_real_field_presence_target_filters_and_scope_without_ui_root(self):
        w=World();self.assertTrue(w.use('prepare'))
        regular=w.fleet('C','S',projection=True) # 标记相同但国家类型不是本危机。
        unmarked=w.fleet('B','S');away=w.fleet('B','T',projection=True)
        cloaked=w.fleet('B','S',projection=True);cloaked['cloaked']=True
        civilian=w.fleet('B','S',projection=True,ship_class='shipclass_transport');civilian['civilian']=True
        disabled=w.fleet('B','S',projection=True);disabled['ships'][0]['disabled']=True
        before=deepcopy(w.a['resources']);sources=w.source_state()
        self.assertTrue(w.condition(TRIGGERS['artifact_public_countermeasure_field_fleet_ready'],[{},w.actor]))
        self.assertTrue(w.use('deploy'));self.assertNotIn(STOCK,w.p['modifiers'])
        self.assertEqual(w.enemy['ships'][0]['modifiers'],{HIT:90});self.assertEqual(w.a['modifiers'][COOLDOWN],180)
        for f in [w.actor,regular,unmarked,away,cloaked,civilian,disabled]:self.assertEqual(f['ships'][0]['modifiers'],{})
        self.assertEqual(w.a['resources'],before);self.assertEqual(w.source_state(),sources)
        self.assertEqual(scalar(MODIFIERS[HIT],'ship_weapon_damage'),'-0.20')
        self.assertEqual(scalar(MODIFIERS[HIT],'ship_fire_rate_mult'),'-0.10')

    def test_country_cooldown_no_refresh_no_late_hits_and_normal_redeployment(self):
        w=World();self.assertTrue(w.use('prepare'));self.assertTrue(w.use('deploy'));w.elapsed(40)
        late=w.fleet('B','S',projection=True)
        self.assertTrue(w.use('prepare')) # 可提前备料，但另一舰队也不能绕过共享冷却。
        w.fleet('A','S');paid=w.state()
        self.assertFalse(w.use('deploy'));w.force('deploy');self.assertEqual(w.state(),paid)
        self.assertEqual(w.enemy['ships'][0]['modifiers'][HIT],50);self.assertEqual(late['ships'][0]['modifiers'],{})
        # 已命中舰船离开星系仍保留剩余时间。
        w.systems['S']['fleets'].remove(w.enemy);w.enemy['solar_system']=w.systems['T'];w.systems['T']['fleets'].append(w.enemy)
        w.elapsed(50);self.assertNotIn(HIT,w.enemy['ships'][0]['modifiers'])
        w.elapsed(90);self.assertNotIn(COOLDOWN,w.a['modifiers'])
        self.assertTrue(w.use('deploy'));self.assertEqual(late['ships'][0]['modifiers'],{HIT:90})
        self.assertEqual(w.enemy['ships'][0]['modifiers'],{})

    def test_unavailable_center_or_no_field_preserves_pack_but_bombardment_can_defend(self):
        w=World();self.assertTrue(w.use('prepare'))
        for stop,resume in (
            (lambda:w.p['inactive'].add(BUILDING),lambda:w.p['inactive'].clear()),
            (lambda:w.p.update(controller=w.countries['B']),lambda:w.p.update(controller=w.a)),
            (lambda:w.p['modifiers'].pop('ajd_deployed'),lambda:w.p['modifiers'].update(ajd_deployed=-1)),
            (lambda:w.actor.update(controller=w.countries['C']),lambda:w.actor.update(controller=w.a)),
            (lambda:w.actor.update(cloaked=True),lambda:w.actor.update(cloaked=False)),
            (lambda:w.countries['B']['hostile'].clear(),lambda:w.countries['B']['hostile'].add('A')),
        ):
            stop();before=w.state();self.assertFalse(w.use('deploy'));w.force('deploy');self.assertEqual(w.state(),before);resume()
        w.p['bombarded']=True
        self.assertTrue(w.use('deploy'))
        self.assertFalse(w.use('prepare'))

    def test_transfer_destroy_clear_unspent_stock_not_fired_effect_or_country_records(self):
        for event in ['2','3']:
            w=World();self.assertTrue(w.use('prepare'));self.assertTrue(w.use('deploy'));self.assertTrue(w.use('prepare'))
            paid=deepcopy(w.a['resources']);sources=w.source_state()
            if event=='2':w.p['owner']=w.p['controller']=w.countries['B']
            w.execute(child(calibration.CIV_EVENTS['artifact_civil_supply.'+event],'immediate'),[w.p])
            self.assertNotIn(STOCK,w.p['modifiers']);self.assertEqual(w.a['modifiers'][COOLDOWN],180)
            self.assertEqual(w.enemy['ships'][0]['modifiers'],{HIT:90})
            self.assertIn(QUALIFIED,w.a['modifiers']);self.assertIn(intelligence.ARCHIVE,w.a['modifiers'])
            self.assertNotIn(QUALIFIED,w.countries['B']['modifiers'])
            self.assertEqual(w.a['resources'],paid);self.assertEqual(w.source_state(),sources)


if __name__=='__main__':unittest.main()
