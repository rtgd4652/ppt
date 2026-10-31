"""执行F02正式候选门禁、归档和E06监听消费者；主线来源为既有输入。

复用A11严格作用域栈，不重跑主线调查或模拟原生隐形发现/存读档。
校验源旗标/计数只读，正常决议费用是外部原生契约。
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_observation_review as review

calibration, child, load = review.calibration, review.child, review.load
scalar = review.scalar
TECH = 'tech_artifact_crisis_signal_identification'
E08 = 'tech_artifact_rule_anchoring_engineering'
E06 = 'tech_artifact_orbital_coordination'
ANCHOR = 'building_artifact_rule_anchor_test_site'
ARCHIVE = 'aci_signal_identified'
WINDOW = 'acs_crisis_listening_window'
ECHO = 'aemusa_ms_country_boundary_echo_verified'
INITIALIZED = 'aemusa_ms_crisis_exclusive_initialized'
COUNTER = 'aemusa_ms_country_anchors_archived'
WARNING_ARRAY = 'building_artifact_phase_warning_array'
WARNING_TECH = 'tech_artifact_phase_disturbance_warning'
TRIGGERS = load('mod/common/scripted_triggers/artifact_crisis_intelligence_triggers.txt')
EFFECTS = load('mod/common/scripted_effects/artifact_crisis_intelligence_effects.txt')
DECISIONS = load('mod/common/decisions/artifact_crisis_intelligence_decisions.txt')
TECHNOLOGY = load('mod/common/technology/artifact_crisis_intelligence_technology.txt')[TECH]


class World(review.World):
    def __init__(self):
        super().__init__()
        for country in self.countries.values():
            country['techs'].update({TECH, E08, E06})
        # A11完成模型是已独立验证的接口输入，不重复其月度项目。
        self.a['modifiers'][review.MODEL] = -1
        self.a['flags'].add(ECHO)
        self.q['buildings'] = {ANCHOR}

    def add_planet(self, key, country='A', system='S'):
        p = super().add_planet(key,country,system)
        p.update(vars={},bombarded=False,queued=set())
        return p

    def term(self, e, stack):
        if e.key == 'check_variable' and scalar(e.value,'which') == COUNTER:
            assert COUNTER in stack[-1]['vars'], '必须先检查主线归档计数存在'
        return super().term(e,stack)

    def use(self, action, p=None):
        p = self.p if p is None else p
        key = 'decision_artifact_crisis_'+('signal_archive' if action == 'archive' else 'listening')
        d = DECISIONS[key]
        if not all(self.condition(child(d,k,[]),[p]) for k in ('potential','allow')): return False
        resources, cost = p['owner']['resources'],child(child(d,'resources',[]),'cost',[])
        if any(resources.get(e.key,0) < float(e.value) for e in cost): return False
        for e in cost: resources[e.key] -= float(e.value)
        self.execute(child(d,'effect'),[p]); return True

    def contacted(self):
        return self.condition(TRIGGERS['artifact_crisis_intelligence_contacted'],[self.a])

    def candidate(self):
        prerequisites = {e.value or e.key for e in child(TECHNOLOGY,'prerequisites')}
        return prerequisites <= self.a['techs'] and self.condition(child(TECHNOLOGY,'potential'),[self.a])

    def identified(self, country=None):
        return self.condition(TRIGGERS['artifact_crisis_intelligence_identified'],[self.a if country is None else country])

    def detection(self, system='T'):
        station = self.systems[system]['starbase']
        return sum(float(scalar(e.value,'ship_cloaking_detection_add') or 0)
            for e in calibration.joint.STATION if e.key=='triggered_station_modifier'
            and self.condition(child(e.value,'potential'),[station]))

    def source_state(self):
        return deepcopy({key:(c['flags'],c['vars']) for key,c in self.countries.items()})


class CrisisIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(calibration.TRIGGERS,{**review.TRIGGERS,**TRIGGERS}))
        self.enterContext(patch.dict(calibration.EFFECTS,{**review.EFFECTS,**EFFECTS}))

    def test_contact_gate_uses_persistent_real_sources_and_guards_missing_counter(self):
        w = World(); w.a['flags'].discard(ECHO)
        for flags,variables in [
            (set(),{}),
            ({review.SOURCE_CRISIS},{}),
            ({INITIALIZED},{}),
            ({INITIALIZED,review.SOURCE_BASELINE},{COUNTER:0}),
            ({'aemusa_ms_country_boundary_verification_pending'},{}),
            (set(),{COUNTER:1}),
        ]:
            w.a['flags'], w.a['vars'] = flags,variables
            self.assertFalse(w.contacted()); self.assertFalse(w.candidate())
        for flags,variables in [({ECHO},{}),({INITIALIZED},{COUNTER:1})]:
            w.a['flags'],w.a['vars'] = flags,variables
            before=w.source_state()
            self.assertTrue(w.contacted()); self.assertTrue(w.candidate())
            self.assertEqual(w.source_state(),before)
        w.a['techs'].remove(E08); self.assertFalse(w.candidate())

    def test_archive_is_free_once_requires_model_and_valid_site_without_story_writes(self):
        for reason in ('contact','model','research','site','control'):
            w=World()
            if reason=='contact':w.a['flags'].discard(ECHO)
            elif reason=='model':w.a['modifiers'].pop(review.MODEL)
            elif reason=='research':w.a['techs'].remove(TECH)
            elif reason=='site':w.p['inactive'].add(review.HIGH)
            else:w.p['controller']=w.countries['B']
            before=deepcopy(w.a['resources']); sources=w.source_state()
            self.assertFalse(w.use('archive'))
            w.execute(EFFECTS['artifact_crisis_intelligence_identify'],[w.p])
            self.assertFalse(w.identified());self.assertEqual(w.a['resources'],before)
            self.assertEqual(w.source_state(),sources)
        for pkey in ('P','Q'):
            w=World();p=w.planets[pkey];before=deepcopy(w.a['resources']);sources=w.source_state()
            self.assertTrue(w.use('archive',p));self.assertFalse(w.use('archive',p))
            self.assertEqual(w.a['resources'],before);self.assertEqual(w.source_state(),sources)
            p['buildings'].clear();self.assertTrue(w.identified())

    def test_exact_native_fee_repeat_guard_and_one_detection_with_old_array(self):
        w=World();self.assertTrue(w.use('archive'))
        # 遗留阵列仍需A07研究；F02付费窗口不需要另取得唯一阵列。
        w.q['buildings'].add(WARNING_ARRAY);self.assertEqual(w.detection(),0)
        w.q['buildings'].discard(WARNING_ARRAY)
        w.a['resources'].update(energy=300,consumer_goods=100)
        sources=w.source_state()
        self.assertTrue(w.use('listen',w.q));self.assertEqual(w.detection(),1)
        self.assertEqual((w.a['resources']['energy'],w.a['resources']['consumer_goods']),(0,0))
        w.elapsed(1);self.assertFalse(w.use('listen',w.q))
        w.execute(EFFECTS['artifact_crisis_intelligence_listen'],[w.q])
        self.assertEqual(w.q['modifiers'][WINDOW],359)
        w.a['techs'].add(WARNING_TECH);w.q['buildings'].add(WARNING_ARRAY)
        self.assertEqual(w.detection(),1)
        # 同星系多个合格来源仍由一个原生修正块供给一份。
        r=w.add_planet('R',system='T');r['buildings']={ANCHOR}
        w.a['resources'].update(energy=300,consumer_goods=100)
        self.assertTrue(w.use('listen',r));self.assertEqual(w.detection(),1)
        self.assertEqual(w.source_state(),sources)

    def test_disabling_control_or_research_pauses_supply_but_window_clock_runs(self):
        w=World();self.assertTrue(w.use('archive'));self.assertTrue(w.use('listen',w.q))
        station=w.systems['T']['starbase']
        for stop,resume in (
            (lambda:w.q['inactive'].add(ANCHOR),lambda:w.q['inactive'].clear()),
            (lambda:w.q.update(controller=w.countries['B']),lambda:w.q.update(controller=w.a)),
            (lambda:w.q.update(bombarded=True),lambda:w.q.update(bombarded=False)),
            (lambda:station.update(controller=w.countries['B']),lambda:station.update(controller=w.a)),
            (lambda:w.a['techs'].remove(E08),lambda:w.a['techs'].add(E08)),
        ):
            stop();self.assertEqual(w.detection(),0);w.elapsed(10)
            resume();self.assertEqual(w.detection(),1)
        self.assertEqual(w.q['modifiers'][WINDOW],310)
        w.elapsed(310);self.assertEqual(w.detection(),0);self.assertNotIn(WINDOW,w.q['modifiers'])
        self.assertTrue(w.identified());self.assertTrue(w.use('listen',w.q))

    def test_missing_foreign_or_occupied_orbital_interface_rejects_before_payment(self):
        w=World();self.assertTrue(w.use('archive'));station=w.systems['T']['starbase']
        for stop,resume in (
            (lambda:station['buildings'].clear(),lambda:station['buildings'].add(calibration.joint.LINK)),
            (lambda:station.update(controller=w.countries['B']),lambda:station.update(controller=w.a)),
            (lambda:station.update(owner=w.countries['B'],controller=w.countries['B']),lambda:station.update(owner=w.a,controller=w.a)),
            (lambda:station.update(normal=False),lambda:station.update(normal=True)),
            (lambda:w.a['techs'].remove(E06),lambda:w.a['techs'].add(E06)),
        ):
            stop();before=deepcopy(w.a['resources']);self.assertFalse(w.use('listen',w.q))
            self.assertEqual(w.a['resources'],before);self.assertNotIn(WINDOW,w.q['modifiers'])
            resume()
        self.assertTrue(w.use('listen',w.q))

    def test_transfer_and_destruction_clear_local_window_not_national_archive(self):
        for outcome in ('transfer','destroy'):
            w=World();self.assertTrue(w.use('archive'));self.assertTrue(w.use('listen',w.q))
            sources=w.source_state();paid=deepcopy(w.a['resources'])
            event='artifact_civil_supply.'+('2' if outcome=='transfer' else '3')
            if outcome=='transfer':w.q['owner']=w.q['controller']=w.countries['B']
            w.execute(child(calibration.CIV_EVENTS[event],'immediate'),[w.q])
            self.assertNotIn(WINDOW,w.q['modifiers']);self.assertEqual(w.detection(),0)
            self.assertTrue(w.identified());self.assertFalse(w.identified(w.countries['B']))
            self.assertEqual(w.a['resources'],paid);self.assertEqual(w.source_state(),sources)


if __name__=='__main__':
    unittest.main()
