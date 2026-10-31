"""执行F06公共资格/一次解译，并接原危机生产者与三种原终局分支。

原引擎现场接口和领袖状态沿用此前明确夹具；不模拟原生研究/岗位或真实存读档。
不把源账本回放写成自然危机验证，未知条件仍失败。
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_crisis_intelligence as intelligence
import test_awp06_crisis_state as crisis
import test_milestone2_finale_state as finale

calibration,child,load=intelligence.calibration,intelligence.child,intelligence.load
scalar=intelligence.scalar
TECH='tech_artifact_post_disaster_record_decoding'
F01='tech_artifact_relic_archive_restoration'
F05='tech_artifact_civilization_joint_recovery'
HIGH='building_artifact_civilization_heritage_archive'
LOW='building_artifact_relic_archive'
RECORD='aph_victory_records_decoded'
VICTORY={'aemusa_ms_crisis_exclusive_completed','aemusa_ms_crisis_exclusive_settled',
         'aemusa_ms_country_settlement_exclusive_crisis_victory_done'}
TRIGGERS=load('mod/common/scripted_triggers/artifact_postcrisis_archive_triggers.txt')
EFFECTS=load('mod/common/scripted_effects/artifact_postcrisis_archive_effects.txt')
DECISION=load('mod/common/decisions/artifact_postcrisis_archive_decisions.txt')['decision_artifact_postcrisis_archive_decode']
TECHNOLOGY=load('mod/common/technology/artifact_postcrisis_archive_technology.txt')[TECH]
BUILDINGS={**load('mod/common/buildings/aemusa_buildings.txt'),**load('mod/common/buildings/artifact_postcrisis_archive_buildings.txt')}
MODIFIER=load('mod/common/static_modifiers/artifact_postcrisis_archive_modifiers.txt')[RECORD]


def final_battle_ledger():
    # 与旧生产者检查相同的外部现场输入，真实归档/战斗账本为3；胜利旗仍由正式效果写入。
    ledger=crisis.active_anchor()
    ledger.variables.update({crisis.PREFIX+'chapter_index':13,crisis.PREFIX+'anchor_stage':40,
        crisis.PREFIX+'anchors_archived':3,crisis.PREFIX+'projections_defeated':3})
    ledger.flags.add(crisis.CRISIS+'weakness_verified')
    return ledger


class World(intelligence.World):
    def __init__(self):
        super().__init__()
        for c in self.countries.values():
            c['techs'].update({TECH,F01,F05});c['resources']['minor_artifacts']=200
        self.a['flags'].update(VICTORY)
        self.a['flags'].update({'aemod_has_special_planet','aemusa_ms_country_flagship_recovering'})
        self.p['buildings']={LOW};self.q['buildings']={HIGH}

    def term(self,e,stack):
        if e.key=='has_resource':
            obj=stack[-1];assert obj['kind']=='country'
            return obj['resources'][scalar(e.value,'type')]>=float(scalar(e.value,'amount_ge'))
        return super().term(e,stack)

    def execute(self,entries,stack):
        if not any(e.key=='add_resource' for e in entries):
            return super().execute(entries,stack)
        # 仅扩展国家实付叶块，其他整块条件仍交给严格父解释器。
        assert stack[-1]['kind']=='country'
        for e in entries:
            if e.key=='add_resource':
                for r in e.value:stack[-1]['resources'][r.key]+=float(r.value)
            else:super().execute([e],stack)

    def use(self):
        if not all(self.condition(child(DECISION,k,[]),[self.q]) for k in ('potential','allow')):return False
        assert child(DECISION,'resources') is None
        self.execute(child(DECISION,'effect'),[self.q]);return True

    def force(self):self.execute(EFFECTS['artifact_postcrisis_archive_decode'],[self.q])

    def common(self,country=None):return self.condition(TRIGGERS['artifact_postcrisis_common_victory'],[country or self.a])
    def decoded(self,country=None):return self.condition(TRIGGERS['artifact_postcrisis_records_decoded'],[country or self.a])

    def candidate(self):
        return {e.value for e in child(TECHNOLOGY,'prerequisites')}<=self.a['techs'] and self.condition(child(TECHNOLOGY,'potential'),[self.a])

    def state(self):return deepcopy({k:(c['resources'],c['flags'],c['vars'],c['modifiers']) for k,c in self.countries.items()})

    def yields(self):
        total=dict(job_artifact_relic_curator_add=0,planet_jobs_produces_mult=0)
        for name in self.q['buildings']-self.q['inactive']:
            for e in BUILDINGS[name]:
                if e.key=='planet_modifier' or e.key=='triggered_planet_modifier' and self.condition(child(e.value,'potential'),[self.colony(self.q)]):
                    for k in total:total[k]+=float(scalar(e.value,k) or 0)
        return total


class PostcrisisArchiveTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(calibration.TRIGGERS,TRIGGERS))
        self.enterContext(patch.dict(calibration.EFFECTS,EFFECTS))

    def test_common_gate_from_actual_settlement_excludes_counts_only_and_partial_flags(self):
        w=World();ledger=final_battle_ledger();w.a['flags']=set(ledger.flags)
        self.assertFalse(w.common());self.assertFalse(w.candidate())
        ledger.effect('aemusa_ms_exclusive_reopen_future');w.a['flags']=set(ledger.flags);self.assertFalse(w.common())
        ledger.effect('aemusa_ms_exclusive_settle');w.a['flags']=set(ledger.flags)
        self.assertTrue(VICTORY<=ledger.flags);self.assertTrue(w.common());self.assertTrue(w.candidate())
        for flag in VICTORY:
            w.a['flags']=set(ledger.flags)-{flag};self.assertFalse(w.common());self.assertFalse(w.candidate())
        w.a['flags']={'aemusa_ms_country_history_vanilla_crisis_settled'}
        w.q['modifiers']['acr_rebuild_done']=-1
        self.assertFalse(w.common());self.assertFalse(w.use())

    def test_three_real_ending_branches_preserve_shared_public_eligibility(self):
        victory=final_battle_ledger();victory.effect('aemusa_ms_exclusive_reopen_future');victory.effect('aemusa_ms_exclusive_settle')
        for ending in ['sovereign','player_refusal','aemusa_refusal']:
            ledger=finale.reach_player_choice('certainty' if ending=='aemusa_refusal' else 'possibilities')
            ledger.flags.update(VICTORY & victory.flags)
            if ending=='player_refusal':
                finale.step(ledger,71,'refuse');finale.step(ledger,100,'accept')
                expected=crisis.PREFIX+'ending_non_transform_player_refusal_settled'
            elif ending=='aemusa_refusal':
                finale.step(ledger,72,'authorize');ledger.open('aemusa_finale.75');finale.step(ledger,110,'accept')
                expected=crisis.PREFIX+'ending_non_transform_aemusa_refusal_settled'
            else:
                finale.step(ledger,72,'authorize');ledger.open('aemusa_finale.75');finale.step(ledger,80,'listen');finale.step(ledger,90)
                for n in [120,130,140,150,160,170,180]:finale.step(ledger,n)
                expected=crisis.PREFIX+'ending_fate_sovereign_settled'
            self.assertIn(expected,ledger.flags)
            w=World();w.a['flags']=set(ledger.flags);self.assertTrue(w.candidate());self.assertTrue(w.use());self.assertTrue(w.decoded())

    def test_exact_payment_and_single_country_record_without_history_writes(self):
        w=World();w.a['resources'].update(energy=500,consumer_goods=200,minor_artifacts=20)
        sources=w.source_state();self.assertTrue(w.use())
        self.assertEqual(tuple(w.a['resources'][k] for k in ['energy','consumer_goods','minor_artifacts']),(0,0,0))
        self.assertEqual(w.source_state(),sources);self.assertTrue(w.decoded())
        self.assertEqual(w.a['modifiers'][RECORD],-1);self.assertEqual(scalar(MODIFIER,'all_technology_research_speed'),'0.10')
        w.a['resources'].update(energy=500,consumer_goods=200,minor_artifacts=20)
        paid=w.state();self.assertFalse(w.use());w.force();self.assertEqual(w.state(),paid)

    def test_missing_resource_victory_research_or_safe_archive_never_charges(self):
        for reason in ['energy','goods','artifacts','victory','technology','inactive','control','bombardment']:
            w=World()
            if reason=='energy':w.a['resources']['energy']=499
            elif reason=='goods':w.a['resources']['consumer_goods']=199
            elif reason=='artifacts':w.a['resources']['minor_artifacts']=19
            elif reason=='victory':w.a['flags']-=VICTORY
            elif reason=='technology':w.a['techs'].remove(TECH)
            elif reason=='inactive':w.q['inactive'].add(HIGH)
            elif reason=='control':w.q['controller']=w.countries['B']
            else:w.q['bombarded']=True
            before=w.state();self.assertFalse(w.use());w.force();self.assertEqual(w.state(),before)

    def test_native_upgrade_preserves_original_jobs_and_no_legacy_double_count(self):
        w=World();self.assertEqual([e.value for e in child(BUILDINGS[LOW],'upgrades')],[HIGH])
        self.assertEqual(scalar(BUILDINGS[HIGH],'can_build'),'no')
        self.assertEqual(w.yields(),dict(job_artifact_relic_curator_add=3,planet_jobs_produces_mult=.05))
        w.q['buildings'].add(LOW);self.assertEqual(w.yields(),dict(job_artifact_relic_curator_add=3,planet_jobs_produces_mult=.05))
        self.assertFalse(w.condition(child(BUILDINGS[LOW],'allow'),[w.q]))
        w.q['buildings']={LOW};w.q['queued'].add(HIGH)
        self.assertFalse(w.condition(child(BUILDINGS[LOW],'allow'),[w.q]))

    def test_knowledge_survives_site_loss_and_is_not_inherited_by_new_owner(self):
        w=World();self.assertTrue(w.use());self.assertTrue(w.decoded())
        w.q['buildings'].clear();self.assertTrue(w.decoded());w.elapsed(720);self.assertEqual(w.a['modifiers'][RECORD],-1)
        w.q['buildings']={HIGH};w.q['owner']=w.q['controller']=w.countries['B']
        self.assertNotIn(RECORD,w.countries['B']['modifiers']);self.assertFalse(w.use());self.assertTrue(w.decoded())
        w.countries['B']['flags'].update(VICTORY)
        self.assertTrue(w.use());self.assertTrue(w.decoded(w.countries['B']));self.assertTrue(w.decoded())


if __name__=='__main__':unittest.main()
