"""执行F04实存备件、备用物流和升级兼容；原生施工/维修及读档不模拟。

沿用E12/E11严格作用域栈，实际跑B14支付和E09阶段；既有F02档案为接口输入。
未知语法仍报错，不把状态夹具等同游戏内验证。
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_civil_engineering as civil
import test_artifact_crisis_intelligence as intelligence
import test_artifact_public_theory as theory

calibration,base,child=civil.calibration,civil.base,civil.child
load,scalar=base.load,base.scalar
TECH='tech_artifact_emergency_engineering_redundancy'
HIGH='building_artifact_redundant_rule_anchor_station'
LOW=intelligence.ANCHOR
STOCK='aer_spares_reserved'
WINDOW='aer_support_window'
TRIGGERS=load('mod/common/scripted_triggers/artifact_engineering_redundancy_triggers.txt')
EFFECTS=load('mod/common/scripted_effects/artifact_engineering_redundancy_effects.txt')
DECISIONS=load('mod/common/decisions/artifact_engineering_redundancy_decisions.txt')
BUILDINGS={**load('mod/common/buildings/artifact_boundary_engineering_buildings.txt'),
           **load('mod/common/buildings/artifact_engineering_redundancy_buildings.txt')}
UI=calibration.events('mod/events/artifact_civil_supply_events.txt')['artifact_civil_supply.10']


class World(civil.World):
    def __init__(self):
        super().__init__()
        for c in self.countries.values():
            c['techs'].update({TECH,intelligence.TECH,intelligence.E08,intelligence.E06,theory.TECH})
            c['resources']['rare_crystals']=5000
        self.a['modifiers'][intelligence.ARCHIVE]=-1
        self.a['modifiers'][theory.METHODS]=-1
        self.a['flags'].update({'artifact_public_rule_interface_record',
            'aemusa_ms_country_flagship_commissioned','aemusa_ms_country_flagship_recovering'})
        self.q['buildings'].add(HIGH)

    def use(self,action,p=None,old=False):
        p=self.q if p is None else p
        if old:return super().use(action,p,old=True)
        d=DECISIONS['decision_artifact_engineering_redundancy_'+action]
        if not all(self.condition(child(d,k,[]),[p]) for k in ('potential','allow')):return False
        assert child(d,'resources') is None,'备料已付费，决议不能二次扣款'
        self.execute(child(d,'effect'),[p]);return True

    def force(self,action,p=None):
        self.execute(EFFECTS['artifact_engineering_redundancy_'+action],[self.q if p is None else p])

    def reserve_spares(self):
        for a in ['register_receiver','reserve','strategic_reserve']:assert self.use(a,old=True),a
        assert self.use('reserve')

    def month(self):self.execute(calibration.EFFECTS['artifact_civil_supply_monthly'],[self.q])

    def active(self):return self.condition(TRIGGERS['artifact_engineering_redundancy_active'],[self.q])

    def bonuses(self):
        total=dict(planet_orbital_bombardment_damage=0,planet_building_build_speed_mult=0)
        for name in self.q['buildings']-self.q['inactive']:
            for e in BUILDINGS.get(name,[]):
                if e.key=='triggered_planet_modifier' and self.condition(child(e.value,'potential'),[self.colony(self.q)]):
                    for k in total:total[k]+=float(scalar(e.value,k) or 0)
        return total

    def page(self):
        return [scalar(e.value,'text') for e in UI if e.key=='desc' and self.condition(child(e.value,'trigger'),[self.q])]

    def source_state(self):
        return deepcopy({k:(c['flags'],c['vars'],c['modifiers']) for k,c in self.countries.items()})


class EngineeringRedundancyTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(calibration.TRIGGERS,{**civil.system.TRIGGERS,**TRIGGERS,**theory.TRIGGERS}))
        self.enterContext(patch.dict(calibration.EFFECTS,{**civil.system.EFFECTS,**intelligence.EFFECTS,**EFFECTS}))

    def test_upgrade_retains_old_defense_listening_and_public_methods_without_stacking(self):
        w=World();self.assertEqual([e.value for e in child(BUILDINGS[LOW],'upgrades')],[HIGH])
        self.assertEqual(scalar(BUILDINGS[HIGH],'can_build'),'no')
        self.assertFalse(w.condition(child(BUILDINGS[LOW],'allow'),[w.q]))
        # 两级遗留并存也只供给一份旧防护；升级不改写360日期限。
        w.q['buildings'].add(LOW)
        w.execute(calibration.EFFECTS['artifact_civil_supply_register_receiver'],[w.q])
        w.execute(calibration.EFFECTS['artifact_rule_anchor_activate'],[w.q])
        self.assertEqual(w.bonuses()['planet_orbital_bombardment_damage'],-.20)
        self.assertTrue(intelligence.World.use(w,'listening',w.q))
        self.assertEqual(w.q['modifiers']['acs_crisis_listening_window'],360)
        w.q['buildings'].remove(LOW)
        self.assertTrue(w.condition(theory.TRIGGERS['artifact_public_theory_engineering_site'],[w.q]))
        self.assertEqual(w.q['modifiers']['acs_rule_anchor_window'],360)
        self.assertTrue(w.condition(intelligence.TRIGGERS['artifact_crisis_intelligence_archive_site'],[w.q]))

    def test_real_pack_conversion_unique_paused_spares_and_discard_no_refund(self):
        w=World();before=deepcopy(w.a['resources']);w.reserve_spares()
        self.assertEqual(w.a['resources'],{**before,'minerals':before['minerals']-2000,
            'alloys':before['alloys']-1000,'energy':before['energy']-500})
        self.assertNotIn(civil.system.STOCK,w.q['modifiers']);self.assertIn(STOCK,w.q['modifiers'])
        w.q['inactive'].add(HIGH);paid=w.state();w.force('reserve');self.assertEqual(w.state(),paid)
        w.p['buildings'].add(HIGH)
        # 即使别处合法接收、实际准备另一份B14材料，失效备件仍占全国名额。
        self.assertTrue(w.use('unregister',old=True))
        for a in ['register_receiver','reserve','strategic_reserve']:self.assertTrue(w.use(a,w.p,old=True))
        self.assertFalse(w.use('reserve',w.p))
        resources=deepcopy(w.a['resources']);self.assertTrue(w.use('discard'));self.assertEqual(w.a['resources'],resources)
        self.assertIn(civil.system.STOCK,w.p['modifiers']);self.assertFalse(w.use('discard'))

    def test_signal_and_active_site_guard_and_window_cannot_refresh_or_duplicate(self):
        w=World();w.reserve_spares()
        for stop,resume in [
            (lambda:w.a['modifiers'].pop(intelligence.ARCHIVE),lambda:w.a['modifiers'].update({intelligence.ARCHIVE:-1})),
            (lambda:w.a['techs'].remove(TECH),lambda:w.a['techs'].add(TECH)),
            (lambda:w.q['inactive'].add(HIGH),lambda:w.q['inactive'].clear()),
        ]:
            stop();before=w.state();self.assertFalse(w.use('activate'));w.force('activate');self.assertEqual(w.state(),before);resume()
        self.assertTrue(w.use('activate'));self.assertTrue(w.active());self.assertNotIn(STOCK,w.q['modifiers'])
        # 原B14名额已释放，可为下次备料，当前窗口不能提前续期。
        for a in ['reserve','strategic_reserve']:self.assertTrue(w.use(a,old=True))
        self.assertTrue(w.use('reserve'));w.elapsed(17);before=w.state()
        self.assertFalse(w.use('activate'));w.force('activate');self.assertEqual(w.state(),before)
        self.assertEqual(w.q['modifiers'][WINDOW],343)

    def test_backup_advances_only_paid_stage_keeps_work_and_requires_native_yard(self):
        w=World();w.reserve_spares();self.assertTrue(w.use('activate'))
        for a in ['reserve','strategic_reserve','segmented_start']:self.assertTrue(w.use(a,old=True))
        w.month();self.assertEqual(w.q['vars']['acs_segmented_work'],1)
        w.q['inactive'].update({civil.system.DEPOT,civil.system.TERMINAL,civil.system.YARD})
        self.assertFalse(w.condition(calibration.TRIGGERS['artifact_civil_supply_segmented_site'],[w.q]))
        self.assertEqual(w.page(),['artifact_segmented.preparing'])
        w.month();self.assertEqual(w.q['vars']['acs_segmented_work'],2)
        w.q['inactive'].add(civil.system.LARGE);w.month();self.assertEqual(w.q['vars']['acs_segmented_work'],2)
        self.assertEqual(w.page(),['artifact_segmented.paused'])
        w.q['inactive'].remove(civil.system.LARGE);w.month();self.assertIn('acs_segmented_prepared',w.q['modifiers'])
        self.assertEqual(w.page(),['artifact_segmented.prepared'])
        paid=deepcopy(w.a['resources']);self.assertFalse(w.use('segmented_assemble',old=True));w.month()
        self.assertEqual(w.a['resources'],paid);self.assertNotIn('acs_segmented_assembling',w.q['modifiers'])
        w.q['inactive'].clear();self.assertTrue(w.use('segmented_assemble',old=True));w.month()
        w.q['inactive'].add(civil.system.YARD);w.elapsed(360);w.month()
        self.assertEqual(w.q['vars']['acs_segmented_work'],1);self.assertNotIn(WINDOW,w.q['modifiers'])

    def test_window_pauses_source_and_native_build_speed_without_pausing_clock(self):
        w=World();w.reserve_spares();self.assertTrue(w.use('activate'));self.assertEqual(w.bonuses()['planet_building_build_speed_mult'],.25)
        for stop,resume in [
            (lambda:w.q.update(controller=w.countries['B']),lambda:w.q.update(controller=w.a)),
            (lambda:w.q.update(bombarded=True),lambda:w.q.update(bombarded=False)),
            (lambda:w.q['inactive'].add(HIGH),lambda:w.q['inactive'].clear()),
            (lambda:w.a['modifiers'].pop(intelligence.ARCHIVE),lambda:w.a['modifiers'].update({intelligence.ARCHIVE:-1})),
        ]:
            stop();self.assertFalse(w.active());self.assertEqual(w.bonuses()['planet_building_build_speed_mult'],0)
            w.elapsed(10);resume();self.assertTrue(w.active())
        self.assertEqual(w.q['modifiers'][WINDOW],320)
        w.elapsed(320);self.assertFalse(w.active());self.assertEqual(w.bonuses()['planet_building_build_speed_mult'],0)

    def test_transfer_or_destroy_clears_local_spares_window_not_original_knowledge_or_story(self):
        for event in ['2','3']:
            w=World();w.reserve_spares();self.assertTrue(w.use('activate'))
            for a in ['reserve','strategic_reserve']:self.assertTrue(w.use(a,old=True))
            self.assertTrue(w.use('reserve'));source=w.source_state();paid=deepcopy(w.a['resources'])
            if event=='2':w.q['owner']=w.q['controller']=w.countries['B']
            w.execute(child(calibration.CIV_EVENTS['artifact_civil_supply.'+event],'immediate'),[w.q])
            self.assertNotIn(STOCK,w.q['modifiers']);self.assertNotIn(WINDOW,w.q['modifiers'])
            self.assertEqual(w.a['resources'],paid);self.assertEqual(w.source_state(),source)


if __name__=='__main__':unittest.main()
