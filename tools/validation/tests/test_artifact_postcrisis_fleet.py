"""执行F07候选、舰装资格与E10原建造接口；不模拟原生战斗/设计器/读档。

F06已解译和D13定型为既有接口输入，原工业条件实际求值；未知语法不放行。
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_strategic_hull as strategic

base,supply,child=strategic.foundation,strategic.supply,strategic.child
load,scalar=base.load,strategic.scalar
TECH='tech_artifact_postcrisis_ship_engineering'
F06='tech_artifact_post_disaster_record_decoding'
RECORD='aph_victory_records_decoded'
VICTORY={'aemusa_ms_crisis_exclusive_completed','aemusa_ms_crisis_exclusive_settled',
         'aemusa_ms_country_settlement_exclusive_crisis_victory_done'}
TRIGGERS={**load('mod/common/scripted_triggers/artifact_postcrisis_archive_triggers.txt'),
          **load('mod/common/scripted_triggers/artifact_postcrisis_fleet_triggers.txt')}
PARTS=strategic.components('artifact_postcrisis_fleet_components.txt')
TECHNOLOGY=load('mod/common/technology/artifact_postcrisis_fleet_technology.txt')[TECH]
SECTION=next(e.value for e in base.parse((base.ROOT/'mod/common/section_templates/artifact_postcrisis_fleet_sections.txt').read_text(encoding='utf-8')) if e.key=='ship_section_template')


class World(strategic.World):
    def __init__(self):
        super().__init__()
        for c in self.countries.values():
            c['flags']=set();c['techs'].update({TECH,F06,strategic.TECH,strategic.ENGINEERING,strategic.hull.TECH})
        self.a=self.countries['A'];self.p=self.planets['P']
        self.a['flags'].update(VICTORY)
        self.a['modifiers'].update({RECORD:-1,strategic.hull.QUALIFIED:-1})
        self.p['buildings'].add(strategic.YARD)
        self.p['modifiers'].update(acs_segmented_project=-1,acs_segmented_operational=-1)
        self.targets['acs_owner@P']=self.ref(self.a)
        self.port=dict(kind='starbase',size='starbase_citadel',owner='A')

    def term(self,e,obj,ctx,prev):
        if e.key=='has_country_flag':
            assert obj['kind']=='country';return e.value in obj['flags']
        return super().term(e,obj,ctx,prev)

    def candidate(self):
        return {e.value for e in child(TECHNOLOGY,'prerequisites')}<=self.a['techs'] and self.condition(child(TECHNOLOGY,'potential'),self.a,{})


class PostcrisisFleetTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(base.TRIGGERS,{**supply.TRIGGERS,**strategic.TRIGGERS,**TRIGGERS}))

    def test_candidate_and_fit_require_decoded_public_knowledge_and_existing_qualification(self):
        w=World();self.assertTrue(w.candidate());self.assertTrue(all(w.may_fit(p) for p in PARTS.values()))
        for flag in VICTORY:
            w.a['flags'].remove(flag);self.assertFalse(w.candidate());self.assertFalse(any(w.may_fit(p) for p in PARTS.values()));w.a['flags'].add(flag)
        w.a['modifiers'].pop(RECORD);self.assertFalse(w.candidate());self.assertFalse(any(w.may_fit(p) for p in PARTS.values()))
        w.a['modifiers'][RECORD]=-1
        for t in [F06,strategic.TECH,TECH]:
            w.a['techs'].remove(t);self.assertFalse(any(w.may_fit(p) for p in PARTS.values()));w.a['techs'].add(t)
        w.a['modifiers'].pop(strategic.hull.QUALIFIED)
        # 正常研究资格与已经完成承载定型分别成立；研究不会凭空生成定型记录。
        self.assertTrue(w.candidate());self.assertFalse(any(w.may_fit(p) for p in PARTS.values()))

    def test_ship_size_species_and_bio_boundaries_preserve_personal_and_native_hulls(self):
        w=World();before=deepcopy(w.a)
        for size in ['corvette','battleship','titan','aemusa_reality_flagship','destiny_lord']:
            self.assertFalse(any(w.may_fit(p,size) for p in PARTS.values()),size)
        for field,value in [('species','HUM'),('bio',True)]:
            old=w.a.get(field);w.a[field]=value
            self.assertFalse(w.candidate());self.assertFalse(any(w.may_fit(p) for p in PARTS.values()))
            if old is None:w.a.pop(field)
            else:w.a[field]=old
        self.assertEqual(w.a,before)

    def test_original_industry_controls_orders_without_erasing_known_component_designs(self):
        w=World();self.assertTrue(w.may_order(w.port))
        for field,value in [('controller','B'),('bombarded',True),('inactive',{strategic.YARD})]:
            old=deepcopy(w.p[field]);w.p[field]=value
            self.assertFalse(w.may_order(w.port));self.assertTrue(all(w.may_fit(p) for p in PARTS.values()));w.p[field]=old
        self.assertTrue(w.may_order(w.port))
        self.assertTrue(w.may_fit(strategic.PARTS['ARTIFACT_STRATEGIC_REACTOR']))

    def test_spinal_fit_has_explicit_weapon_parameters_and_power_for_essential_cores(self):
        w=World();bow_weapon=PARTS['ARTIFACT_POSTCRISIS_SPINAL_LANCE'];reactor=PARTS['ARTIFACT_POSTCRISIS_REACTOR'];frame=PARTS['ARTIFACT_POSTCRISIS_RECOVERY_FRAME']
        self.assertEqual(scalar(SECTION,'ship_size'),strategic.SIZE)
        self.assertEqual(scalar(SECTION,'fits_on_slot'),'bow');self.assertEqual(scalar(SECTION,'large_utility_slots'),'3')
        self.assertEqual(scalar(child(SECTION,'component_slot'),'template'),'invisible_extra_large_fixed')
        self.assertEqual(scalar(bow_weapon,'size'),'extra_large');self.assertEqual(scalar(reactor,'size'),'small');self.assertEqual(scalar(frame,'size'),'aux')
        self.assertEqual(scalar(reactor,'component_set'),'power_core')
        # 无原版XL研究也能选择本包配套舰首；自动设计权重不能落入原版科技白名单。
        guard=[e for e in child(child(SECTION,'ai_weight'),'modifier') if e.key!='factor']
        self.assertFalse(w.condition(guard,w.a,{}))
        w.a['modifiers'].pop(RECORD);self.assertTrue(w.condition(guard,w.a,{}));w.a['modifiers'][RECORD]=-1
        for body in PARTS.values():self.assertNotIn('upgrades_to',{e.key for e in body})
        self.assertGreater(float(scalar(child(bow_weapon,'damage'),'min')),0)
        self.assertGreater(float(scalar(bow_weapon,'total_fire_time')),0)
        self.assertEqual(float(scalar(bow_weapon,'shield_penetration')),0);self.assertEqual(float(scalar(bow_weapon,'armor_penetration')),0)
        # 新增部分+既有必需推进/电脑的供能余量；不冒称原生完整自动设计或实际DPS。
        loadout=[bow_weapon,frame,frame,strategic.PARTS['ARTIFACT_STRATEGIC_THRUSTER'],strategic.PARTS['ARTIFACT_STRATEGIC_COMPUTER_ARTILLERY']]
        self.assertGreater(float(scalar(reactor,'power'))+sum(float(scalar(p,'power')) for p in loadout),0)
        self.assertTrue(all(w.may_fit(p) for p in PARTS.values()))


if __name__=='__main__':unittest.main()
