"""执行A11正式脚本，检查成果来源、付费复核、升级兼容与只读事实。

沿用A09严格解释器；原生升级、岗位尺度、费用、显示及存读档仍为外部契约。
不把剧情输入夹具记为自然发生的危机，不修改被读取的主线记录。
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_observation_calibration as calibration
from check_mod import parse, scalar

ROOT, child = calibration.ROOT, calibration.child
load = calibration.joint.base.load
TECH = 'tech_artifact_high_dimensional_model_review'
HIGH = 'building_artifact_high_dimensional_review_station'
OLD = 'building_artifact_black_gate_observatory'
LOW = 'building_artifact_baseline_observation_station'
SAMPLE = 'building_artifact_sample_repository'
INTERFACE = 'artifact_public_rule_interface_record'
MODEL = 'amr_model_reviewed'
PROJECT = 'acs_model_review_project'
WORK = 'acs_model_review_work'
CRISIS = 'amr_crisis_context_reviewed'
LOSS = 'amr_loss_reviewed'
SOURCE_CRISIS = 'aemusa_ms_country_history_vanilla_crisis_started'
SOURCE_BASELINE = 'aemusa_ms_country_anchor_baseline_recorded'
SOURCE_INIT = 'aemusa_ms_crisis_exclusive_initialized'
SOURCE_LOSSES = 'aemusa_ms_country_anchor_losses'
TRIGGERS = load('mod/common/scripted_triggers/artifact_observation_review_triggers.txt')
EFFECTS = load('mod/common/scripted_effects/artifact_observation_review_effects.txt')
DECISIONS = load('mod/common/decisions/artifact_observation_review_decisions.txt')
UI = calibration.events('mod/events/artifact_observation_review_events.txt')['artifact_observation_review.1']
BUILDINGS = {}
for name in ('aemusa_buildings','artifact_public_foundation_buildings','artifact_observation_review_buildings'):
    BUILDINGS.update(load('mod/common/buildings/'+name+'.txt'))


class World(calibration.World):
    def __init__(self):
        super().__init__()
        for country in self.countries.values():
            country['flags'] = {INTERFACE}
            country['techs'].update({TECH,'tech_artifact_stable_rule_interface','tech_artifact_black_gate_observation',
                                    'tech_artifact_tarot_economy','tech_artifact_multi_source_comparison'})
            country['resources']['rare_crystals'] = 1000
            country['modifiers'][calibration.ARCHIVE] = -1
        for p in self.planets.values(): p['queued'] = set()
        self.p['buildings'] = {HIGH}

    def term(self, e, stack):
        obj = stack[-1]
        if e.key == 'has_country_flag':
            assert obj['kind'] == 'country'
            return e.value in obj['flags']
        if e.key == 'is_variable_set': return e.value in obj['vars']
        if e.key == 'has_building_construction': return e.value in obj['queued']
        if e.key == 'check_variable' and scalar(e.value,'which') == SOURCE_LOSSES:
            # 不允许默认0掩盖未初始化的主线变量，正式脚本必须先通过存在检查。
            assert SOURCE_LOSSES in obj['vars']
        return super().term(e,stack)

    def execute(self, entries, stack):
        # 仅捕获原生界面契约；先验证完成通知使用的确是行星载体。
        for e in entries:
            if e.key == 'carrier_event':
                assert stack[-1]['kind'] == 'planet'
                self.notifications.append(scalar(e.value,'id'))
        super().execute([e for e in entries if e.key != 'carrier_event'],stack)

    def use(self, name, planet=None):
        p = self.p if planet is None else planet
        d = DECISIONS['decision_artifact_model_review_'+name]
        if not all(self.condition(child(d,k,[]),[p]) for k in ('potential','allow')): return False
        cost = child(child(d,'resources',[]),'cost',[])
        resources = p['owner']['resources']
        if any(resources.get(e.key,0) < float(e.value) for e in cost): return False
        for e in cost: resources[e.key] -= float(e.value)
        self.execute(child(d,'effect'),[p]); return True

    def complete(self):
        assert self.use('start')
        for _ in range(4): self.monthly()

    def page(self):
        return [scalar(e.value,'text') for e in UI if e.key == 'desc'
                and self.condition(child(e.value,'trigger'),[self.p])]

    def yields(self):
        keys = ['job_artifact_tarot_analyst_add','job_artifact_junior_observer_add','planet_stability_add',
                'planet_jobs_physics_research_produces_mult','planet_jobs_engineering_research_produces_mult']
        total = dict.fromkeys(keys,0)
        for name in self.p['buildings'] - self.p['inactive']:
            for e in BUILDINGS.get(name,[]):
                if e.key == 'planet_modifier' or (e.key == 'triggered_planet_modifier'
                        and self.condition(child(e.value,'potential'),[self.colony(self.p)])):
                    for key in keys: total[key] += float(scalar(e.value,key) or 0)
        return total


class ObservationReviewTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(calibration.TRIGGERS,TRIGGERS))
        self.enterContext(patch.dict(calibration.EFFECTS,EFFECTS))

    def test_real_archives_exact_fee_unique_slot_and_four_months(self):
        w = World(); self.assertEqual(w.page(),['amr.intro'])
        for source in ('calibration','interface'):
            if source == 'calibration': w.a['modifiers'].pop(calibration.ARCHIVE)
            else: w.a['flags'].remove(INTERFACE)
            before = deepcopy(w.a['resources']); self.assertFalse(w.use('start'))
            self.assertEqual(w.a['resources'],before)
            if source == 'calibration': w.a['modifiers'][calibration.ARCHIVE] = -1
            else: w.a['flags'].add(INTERFACE)
        w.a['resources'] = dict(energy=600,consumer_goods=300,rare_crystals=100)
        self.assertTrue(w.use('start')); self.assertFalse(w.use('start'))
        self.assertEqual(w.a['resources'],dict(energy=0,consumer_goods=0,rare_crystals=0))
        w.q['buildings'] = {HIGH}; self.assertFalse(w.use('start',w.q))
        for _ in range(3): w.monthly()
        self.assertNotIn(MODEL,w.a['modifiers']); self.assertEqual(w.p['vars'][WORK],3)
        w.monthly(); self.assertIn(MODEL,w.a['modifiers'])
        self.assertNotIn(PROJECT,w.p['modifiers']); self.assertNotIn(WORK,w.p['vars'])
        self.assertNotIn(CRISIS,w.a['modifiers']); self.assertNotIn(LOSS,w.a['modifiers'])
        self.assertEqual(w.a['flags'],{INTERFACE})
        self.assertEqual(w.notifications,['artifact_observation_review.1'])
        self.assertEqual(w.page(),['amr.reviewed_basic'])

    def test_pause_restore_and_read_only_page(self):
        w = World(); self.assertTrue(w.use('start')); w.monthly()
        pairs = [(lambda: w.p.update(controller=w.countries['B']),lambda: w.p.update(controller=w.a)),
            (lambda: w.p['inactive'].add(HIGH),lambda: w.p['inactive'].clear()),
            (lambda: w.p.update(bombarded=True),lambda: w.p.update(bombarded=False)),
            (lambda: w.a['flags'].remove(INTERFACE),lambda: w.a['flags'].add(INTERFACE))]
        for stop,resume in pairs:
            stop(); w.monthly(); self.assertEqual(w.p['vars'][WORK],1)
            self.assertEqual(w.page(),['amr.paused'])
            before = deepcopy(w.a['resources']); self.assertTrue(w.use('status'))
            self.assertEqual(w.a['resources'],before); self.assertEqual(w.p['vars'][WORK],1)
            resume(); self.assertEqual(w.page(),['amr.working'])
        w.monthly(); self.assertEqual(w.p['vars'][WORK],2)

    def test_known_facts_append_only_once_without_writing_story_sources(self):
        w = World(); w.a['flags'].add(SOURCE_CRISIS)
        source_flags,source_vars = deepcopy(w.a['flags']),deepcopy(w.a['vars'])
        w.complete(); self.assertIn(CRISIS,w.a['modifiers']); self.assertNotIn(LOSS,w.a['modifiers'])
        self.assertEqual(w.page(),['amr.reviewed_crisis']); self.assertFalse(w.use('append'))
        self.assertEqual(w.a['flags'],source_flags); self.assertEqual(w.a['vars'],source_vars)
        w.a['flags'].add(SOURCE_INIT); w.a['vars'][SOURCE_LOSSES] = 0
        self.assertFalse(w.use('append'))
        w.a['vars'][SOURCE_LOSSES] = 1
        before = deepcopy(w.a['resources']); self.assertTrue(w.use('append'))
        self.assertEqual(w.a['resources']['energy'],before['energy']-300)
        self.assertEqual(w.a['resources']['consumer_goods'],before['consumer_goods']-100)
        self.assertEqual(w.a['vars'][SOURCE_LOSSES],1)
        self.assertEqual(w.page(),['amr.reviewed_both']); self.assertFalse(w.use('append'))
        other = World(); other.a['flags'].add(SOURCE_INIT); other.a['vars'][SOURCE_LOSSES] = 1
        other.complete(); self.assertEqual(other.page(),['amr.reviewed_loss'])
        other.a['flags'].add(SOURCE_BASELINE); self.assertTrue(other.use('append'))
        self.assertEqual(other.page(),['amr.reviewed_both'])

    def test_cancel_transfer_and_completed_national_knowledge(self):
        w = World(); self.assertTrue(w.use('start')); w.p['modifiers']['acs_supply_reserved'] = -1
        before = deepcopy(w.a['resources']); w.p['controller'] = w.countries['B']
        self.assertTrue(w.use('cancel')); self.assertEqual(w.a['resources'],before)
        self.assertIn('acs_supply_reserved',w.p['modifiers']); self.assertFalse(w.use('cancel'))
        w.p['controller'] = w.a; self.assertTrue(w.use('start')); w.monthly()
        w.p.update(owner=w.countries['B'],controller=w.countries['B'])
        w.execute(child(calibration.CIV_EVENTS['artifact_civil_supply.2'],'immediate'),[w.p])
        self.assertNotIn(PROJECT,w.p['modifiers']); self.assertNotIn(WORK,w.p['vars'])
        self.assertNotIn(MODEL,w.countries['B']['modifiers'])
        completed = World(); completed.complete()
        completed.p.update(owner=completed.countries['B'],controller=completed.countries['B'])
        completed.execute(child(calibration.CIV_EVENTS['artifact_civil_supply.2'],'immediate'),[completed.p])
        self.assertIn(MODEL,completed.a['modifiers']); self.assertNotIn(MODEL,completed.countries['B']['modifiers'])

    def test_final_upgrade_retains_old_jobs_comparison_and_blocks_lower_rebuild(self):
        w = World(); w.p['buildings'] = {OLD,SAMPLE}
        before = w.yields()
        self.assertEqual(before['job_artifact_tarot_analyst_add'],6)
        self.assertEqual(before['planet_jobs_physics_research_produces_mult'],.1)
        self.assertTrue(w.condition(child(BUILDINGS[OLD],'allow'),[w.p]))
        w.p['queued'].add(HIGH)
        self.assertFalse(w.condition(child(BUILDINGS[OLD],'allow'),[w.p]))
        self.assertFalse(w.condition(child(BUILDINGS[LOW],'allow'),[w.p]))
        self.assertTrue(w.condition(child(BUILDINGS[OLD],'potential'),[w.p]))
        self.assertEqual([e.value for e in child(BUILDINGS[OLD],'upgrades')],[HIGH])
        self.assertEqual(scalar(BUILDINGS[HIGH],'can_build'),'no')
        w.p['queued'].clear(); w.p['buildings'] = {HIGH,SAMPLE}
        self.assertEqual(w.yields(),before)
        # 强制遗留并存时也仅由最高活动阶段供给原岗位与比对收益。
        w.p['buildings'].update({OLD,LOW}); self.assertEqual(w.yields(),before)

    def test_upgrade_preserves_active_calibration_and_prepaid_local_window(self):
        w = World(); w.a['modifiers'].pop(calibration.ARCHIVE)
        w.p['buildings'] = {calibration.LONG}; w.pair(); self.assertTrue(w.choose('start'))
        w.monthly(); self.assertEqual(w.a['vars']['aoc_work'],1)
        w.q['buildings'] = {HIGH}; w.monthly(); self.assertEqual(w.a['vars']['aoc_work'],2)
        for _ in range(4): w.monthly()
        self.assertIn(calibration.ARCHIVE,w.a['modifiers'])
        r = w.add_planet('R',system='T'); r.update(vars={},bombarded=False,queued=set())
        r['flags'].clear(); r['buildings'] = {calibration.OBS}
        self.assertTrue(w.choose('apply',r)); expected = w.support()
        r['buildings'] = {HIGH}
        self.assertEqual(r['modifiers']['acs_observation_window'],360)
        self.assertEqual(w.support(),expected)
        self.assertEqual(expected,dict(ship_sensor_range_add=1,ship_hyperlane_range_add=2))


if __name__ == '__main__': unittest.main()
