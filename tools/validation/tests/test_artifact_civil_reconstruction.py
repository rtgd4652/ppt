"""执行F05正式决议/ACS月度，核对真实损伤、费用、暂停和清理。

不模拟自然荒废度恢复、建筑维修、原生日期/读档；损伤是外部现场输入。
严格执行作用域和比较，不把费用/计时夹具作为游戏内证据。
"""
from copy import deepcopy
import re
import unittest
from unittest.mock import patch

import test_artifact_engineering_redundancy as redundancy

calibration,base,child=redundancy.calibration,redundancy.base,redundancy.child
load,scalar=base.load,base.scalar
TECH='tech_artifact_civilization_joint_recovery'
BUILDING='building_artifact_post_disaster_reconstruction_workshop'
PROJECT='acr_rebuild_project'
DONE='acr_rebuild_done'
WORK='acr_rebuild_work'

def load_recovery(path):
    # 解析器丢弃比较号，夹具显式保留正式脚本用到的>=和<，不放宽未知条件。
    s=(base.ROOT/path).read_text(encoding='utf-8')
    s=re.sub(r'\bplanet_devastation\s*(>=|<)\s*([\d.]+)',lambda m:'planet_devastation_'+('ge' if m[1]=='>=' else 'lt')+' = '+m[2],s)
    s=re.sub(r'\b(value|amount)\s*>=\s*([\w.-]+)',r'\1_ge = \2',s)
    return {e.key:e.value for e in base.parse(s) if e.key}

TRIGGERS=load_recovery('mod/common/scripted_triggers/artifact_civil_reconstruction_triggers.txt')
EFFECTS=load_recovery('mod/common/scripted_effects/artifact_civil_reconstruction_effects.txt')
DECISIONS=load('mod/common/decisions/artifact_civil_reconstruction_decisions.txt')
UI=calibration.events('mod/events/artifact_civil_reconstruction_events.txt')['artifact_civil_reconstruction.1']


class World(redundancy.World):
    def __init__(self):
        super().__init__()
        for c in self.countries.values():c['techs'].add(TECH)
        for p in self.planets.values():p['devastation']=0
        self.q['buildings'].add(BUILDING);self.q['devastation']=50
        self.healing=[]

    def term(self,e,stack):
        if e.key in ('planet_devastation_ge','planet_devastation_lt'):
            obj=stack[-1];assert obj['kind'] in ('planet','colony') and 'devastation' in obj
            return obj['devastation']>=float(e.value) if e.key.endswith('_ge') else obj['devastation']<float(e.value)
        return super().term(e,stack)

    def execute(self,entries,stack):
        # 保持父解释器的if/else整块语义，只在直接包含新原生效果的叶块扩展。
        if not any(e.key in ('add_planet_devastation','carrier_event') for e in entries):
            return super().execute(entries,stack)
        for e in entries:
            if e.key=='add_planet_devastation':
                obj=stack[-1];assert obj['kind']=='planet' and float(e.value)==-5 and obj['devastation']>=5
                obj['devastation']+=float(e.value);self.healing.append((obj['id'],float(e.value)))
            elif e.key=='carrier_event':
                assert stack[-1]['kind']=='planet' and scalar(e.value,'id')=='artifact_civil_reconstruction.1'
                self.notifications.append(scalar(e.value,'id'))
            else:super().execute([e],stack)

    def use(self,action,p=None,old=False):
        p=self.q if p is None else p
        if old:return super().use(action,p,old=True)
        d=DECISIONS['decision_artifact_civil_reconstruction_'+action]
        if not all(self.condition(child(d,k,[]),[p]) for k in ('potential','allow')):return False
        assert child(d,'resources') is None,'固定面额由效果支付，不能另收原生费用'
        self.execute(child(d,'effect'),[p]);return True

    def force(self,action):self.execute(EFFECTS['artifact_civil_reconstruction_'+action],[self.q])

    def prepare(self):assert self.use('reserve',old=True)

    def page(self):
        return [scalar(e.value,'text') for e in UI if e.key=='desc' and self.condition(child(e.value,'trigger'),[self.q])]

    def state(self):return deepcopy((super().state(),{k:p['devastation'] for k,p in self.planets.items()}))


class CivilReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(calibration.TRIGGERS,{**TRIGGERS,**redundancy.TRIGGERS,**redundancy.theory.TRIGGERS}))
        self.enterContext(patch.dict(calibration.EFFECTS,EFFECTS))

    def test_exact_real_stock_and_fee_once_then_repeat_or_view_cannot_advance(self):
        w=World();before=deepcopy(w.a['resources']);w.prepare()
        w.a['resources'].update(energy=500,consumer_goods=200)
        self.assertTrue(w.use('start'));self.assertEqual(w.a['resources']['energy'],0);self.assertEqual(w.a['resources']['consumer_goods'],0)
        self.assertEqual(w.a['resources']['minerals'],before['minerals']-500);self.assertEqual(w.a['resources']['alloys'],before['alloys']-100)
        self.assertNotIn('acs_supply_reserved',w.q['modifiers']);self.assertEqual(w.q['vars'][WORK],0)
        paid=w.state();self.assertFalse(w.use('start'));w.force('start');self.assertTrue(w.use('status'))
        self.assertEqual(w.page(),['acr.working']);self.assertEqual(w.state(),paid);self.assertEqual(w.healing,[])
        self.assertFalse(w.use('refund',old=True))

    def test_insufficient_resource_damage_or_site_never_spends_or_creates_project(self):
        for reason in ['energy','goods','damage','building','control','bombardment','technology']:
            w=World();w.prepare()
            if reason=='energy':w.a['resources']['energy']=499
            elif reason=='goods':w.a['resources']['consumer_goods']=199
            elif reason=='damage':w.q['devastation']=9.9
            elif reason=='building':w.q['inactive'].add(BUILDING)
            elif reason=='control':w.q['controller']=w.countries['B']
            elif reason=='bombardment':w.q['bombarded']=True
            else:w.a['techs'].remove(TECH)
            before=w.state();self.assertFalse(w.use('start'));w.force('start');self.assertEqual(w.state(),before)
        w=World();self.assertFalse(w.use('start'));self.assertEqual(w.page(),['acr.intro'])

    def test_six_valid_months_reduce_actual_damage_only_and_keep_story_and_other_inventory(self):
        w=World();w.prepare();self.assertTrue(w.use('start'));self.assertTrue(w.use('reserve',old=True))
        sources=w.source_state();resources=deepcopy(w.a['resources'])
        for n in range(1,7):
            w.month();self.assertEqual(w.q['devastation'],50-5*n);self.assertEqual(w.q['vars'][WORK],n)
        self.assertNotIn(PROJECT,w.q['modifiers']);self.assertIn(DONE,w.q['modifiers']);self.assertEqual(w.page(),['acr.done'])
        self.assertIn('acs_supply_reserved',w.q['modifiers']);self.assertEqual(w.a['resources'],resources);self.assertEqual(w.source_state(),sources)
        receipt=w.state();w.month();w.use('status');self.assertEqual(w.state(),receipt);self.assertEqual(len(w.healing),6)
        # 仍有真实损伤时可另付一轮；原记录由新轮更新，不自动循环。
        self.assertTrue(w.use('start'));self.assertNotIn(DONE,w.q['modifiers']);self.assertEqual(w.q['vars'][WORK],0)

    def test_pause_preserves_national_slot_and_resume_has_no_catchup(self):
        w=World();w.prepare();self.assertTrue(w.use('start'));w.month()
        for stop,resume in [
            (lambda:w.q.update(controller=w.countries['B']),lambda:w.q.update(controller=w.a)),
            (lambda:w.q.update(bombarded=True),lambda:w.q.update(bombarded=False)),
            (lambda:w.q['inactive'].add(BUILDING),lambda:w.q['inactive'].clear()),
            (lambda:w.a['techs'].remove(TECH),lambda:w.a['techs'].add(TECH)),
        ]:
            stop();before=w.state();w.month();w.month();self.assertEqual(w.state(),before);self.assertEqual(w.page(),['acr.paused']);resume()
        w.p['buildings'].add(BUILDING);w.p['devastation']=80;self.assertTrue(w.use('reserve',w.p,old=True))
        self.assertFalse(w.use('start',w.p));w.month();self.assertEqual(w.q['vars'][WORK],2);self.assertEqual(w.q['devastation'],40)

    def test_low_remaining_damage_finishes_without_negative_value_or_fabricated_work(self):
        for current,expected,work in [(10,0,2),(10.5,.5,2),(50,0,0)]:
            w=World();w.q['devastation']=current;w.prepare();self.assertTrue(w.use('start'))
            if work==0:w.q['devastation']=0 # 原生/外部先恢复完，不伪称本项目完成了施工。
            w.month();w.month();self.assertEqual(w.q['devastation'],expected);self.assertEqual(w.q['vars'][WORK],work)
            self.assertNotIn(PROJECT,w.q['modifiers']);self.assertIn(DONE,w.q['modifiers'])

    def test_cancel_transfer_and_destroy_no_refund_or_healing_rollback(self):
        for action in ['cancel','2','3']:
            w=World();w.prepare();self.assertTrue(w.use('start'));w.month();self.assertTrue(w.use('reserve',old=True))
            paid=deepcopy(w.a['resources']);sources=w.source_state()
            if action=='cancel':
                w.q['inactive'].add(BUILDING);self.assertTrue(w.use('cancel'));self.assertIn('acs_supply_reserved',w.q['modifiers'])
            else:
                if action=='2':w.q['owner']=w.q['controller']=w.countries['B']
                w.execute(child(calibration.CIV_EVENTS['artifact_civil_supply.'+action],'immediate'),[w.q])
            self.assertNotIn(PROJECT,w.q['modifiers']);self.assertNotIn(DONE,w.q['modifiers']);self.assertNotIn(WORK,w.q['vars'])
            self.assertEqual(w.q['devastation'],45);self.assertEqual(w.a['resources'],paid);self.assertEqual(w.source_state(),sources)


if __name__=='__main__':unittest.main()
