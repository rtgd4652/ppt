"""核对R3d解锁边界与真实原生槽位合同；不模拟战斗、引擎装配或存读档。"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from check_mod import parse,scalar

ROOT=Path(__file__).resolve().parents[3]
def read(path):return parse((ROOT/path).read_text(encoding='utf-8-sig'))
def block(nodes,key):return next((e.value for e in nodes if e.key==key),[])
def keys(nodes,key):return {e.value for e in block(nodes,key)}
def components(path):return {scalar(e.value,'key'):e.value for e in read(path)}

TECH={e.key:e.value for e in read('mod/common/technology/artifact_midgame_military_technology.txt')}
PARTS=components('mod/common/component_templates/artifact_midgame_military_components.txt')
OLD=components('mod/common/component_templates/artifact_close_combat_components.txt')
ARMY=read('mod/common/armies/artifact_resonance_siege_armies.txt')[0].value
LEGACY_ARMIES={e.key:e.value for e in read('mod/common/armies/aemusa_artifact_armies.txt')}

class MidgameMilitaryTests(unittest.TestCase):
    def test_real_prerequisites_and_public_route_without_personal_gate(self):
        all_tech={e.key for p in (ROOT/'mod/common/technology').glob('*.txt')
                  for e in parse(p.read_text(encoding='utf-8-sig'))}
        self.assertEqual(len(TECH),5)
        for key,body in TECH.items():
            self.assertLessEqual(keys(body,'prerequisites'),all_tech)
            self.assertNotIn(key,keys(body,'prerequisites'))
            self.assertGreater(float(scalar(body,'cost')),0)
            self.assertNotIn('modifier',{e.key for e in body})
            self.assertNotIn('country_modifier',{e.key for e in body})
            serialized=str(body)
            self.assertNotIn('aemusa_ms_',serialized)
            self.assertNotIn('has_ascension_perk',serialized)

    def test_long_range_weapons_have_inline_values_and_real_tradeoffs(self):
        for size in ('SMALL','MEDIUM','LARGE'):
            p=PARTS[size+'_ARTIFACT_LONG_RANGE_PHASE_PROJECTOR']
            old=OLD[size+'_ARTIFACT_CLOSE_RESONANCE_EMITTER']
            self.assertEqual(scalar(p,'type'),'instant')
            for field in ('damage','windup','total_fire_time','power','range','tracking','accuracy'):
                self.assertIsNotNone(scalar(p,field) if field not in ('damage','windup') else block(p,field),field)
            self.assertGreater(float(scalar(block(p,'damage'),'min')),0)
            self.assertGreater(float(scalar(p,'range')),float(scalar(old,'range')))
            self.assertLess(float(scalar(p,'tracking')),float(scalar(old,'tracking')))
            self.assertGreater(float(scalar(p,'total_fire_time')),float(scalar(old,'total_fire_time')))
            self.assertLess(float(scalar(p,'power')),float(scalar(old,'power')))
            self.assertNotIn('ai_weight',{e.key for e in p})

    def test_layered_defense_requires_two_tracks_for_composite_armor(self):
        for size in ('SMALL','MEDIUM','LARGE'):
            shield=PARTS[size+'_ARTIFACT_LAYERED_PHASE_SHIELD']
            armor=PARTS[size+'_ARTIFACT_COMPOSITE_RUNIC_ARMOR']
            self.assertEqual(keys(armor,'prerequisites'),{
                'tech_artifact_layered_phase_defense','tech_artifact_runic_hull_armor'})
            old=OLD[size+'_ARTIFACT_RESONANCE_DEFLECTOR']
            self.assertGreater(float(scalar(block(shield,'modifier'),'ship_shield_add')),
                               float(scalar(block(old,'modifier'),'ship_shield_add')))
            self.assertLess(float(scalar(shield,'power')),float(scalar(old,'power')))
            self.assertGreater(float(scalar(block(shield,'ship_modifier'),'ship_shield_hardening_add')),0)
            self.assertGreater(float(scalar(block(armor,'ship_modifier'),'ship_armor_hardening_add')),0)

    def test_reclamation_has_no_event_payout_and_consumes_aux_slot(self):
        p=PARTS['ARTIFACT_REPAIR_RECLAMATION_MODULE']
        self.assertEqual(scalar(p,'size'),'aux')
        self.assertLess(float(scalar(p,'power')),0)
        self.assertGreater(float(scalar(block(p,'modifier'),'ship_hull_regen_add_perc')),0)
        self.assertGreater(float(scalar(block(p,'modifier'),'ship_armor_regen_add_perc')),0)
        self.assertGreater(float(scalar(block(p,'ship_modifier'),'ship_upkeep_mult')),-1)
        self.assertLess(float(scalar(block(p,'ship_modifier'),'ship_upkeep_mult')),0)
        self.assertFalse({'on_destroy','on_ship_destroyed','produces'} & {e.key for e in p})
        self.assertFalse(block(block(p,'resources'),'produces'))
        self.assertGreater(float(scalar(block(block(p,'resources'),'upkeep'),'alloys')),0)

    def test_ftl_is_native_lane_slot_without_jump_or_legacy_overrides(self):
        p=PARTS['ARTIFACT_COORDINATED_HYPER_DRIVE']
        self.assertEqual(scalar(p,'component_set'),'ftl_components')
        self.assertEqual(scalar(p,'size'),'small')
        self.assertEqual(scalar(p,'ftl'),'yes')
        self.assertEqual(scalar(p,'jumpdrive'),'no')
        self.assertGreater(float(scalar(block(p,'ship_modifier'),'ship_interstellar_speed_mult')),0)
        self.assertLess(float(scalar(block(p,'ship_modifier'),'ship_windup_mult')),0)
        self.assertFalse(set(PARTS) & set(OLD))
        for body in PARTS.values():
            self.assertIsNone(scalar(body,'upgrades_to'))
            self.assertIn('ARTIFACT_USER',str(block(body,'potential')))

    def test_siege_durability_cost_and_collateral_are_not_free_power(self):
        old=LEGACY_ARMIES['artifact_user_resonance_army']
        self.assertGreater(float(scalar(ARMY,'health')),float(scalar(old,'health')))
        self.assertGreater(float(scalar(ARMY,'collateral_damage')),float(scalar(old,'collateral_damage')))
        self.assertGreater(float(scalar(ARMY,'time')),float(scalar(old,'time')))
        # 旧军队既有20%伤害修正也纳入比较，不只比较基础倍率。
        self.assertLessEqual(float(scalar(ARMY,'damage')),float(scalar(old,'damage'))*1.2)
        for field in ('energy','alloys'):
            self.assertGreater(float(scalar(block(block(ARMY,'resources'),'upkeep'),field)),
                               float(scalar(block(block(old,'resources'),'upkeep'),field)))
        self.assertNotIn('defensive',{e.key for e in ARMY})
        self.assertNotIn('is_pop_spawned',{e.key for e in ARMY})

if __name__=='__main__':unittest.main()
