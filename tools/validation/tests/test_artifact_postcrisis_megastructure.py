"""执行F08正式门禁、完工标记和造境实效；不模拟原生施工/计费/殖民或存读档。

严格作用域栈沿用A09；新扩展仅覆盖本包实际使用的原生巨构与行星叶接口。
"""
from copy import deepcopy
import re
import unittest

import test_artifact_observation_calibration as calibration
from check_mod import parse, scalar

ROOT, child = calibration.ROOT, calibration.child
TECH = 'tech_artifact_postcrisis_megastructure_engineering'
F06 = 'tech_artifact_post_disaster_record_decoding'
E11 = 'tech_artifact_interstellar_engineering_coordination'
RECORD = 'aph_victory_records_decoded'
VICTORY = {'aemusa_ms_crisis_exclusive_completed', 'aemusa_ms_crisis_exclusive_settled',
           'aemusa_ms_country_settlement_exclusive_crisis_victory_done'}
BASE, LIVE = 'artifact_postcrisis_world_former_0', 'artifact_postcrisis_world_former_1'


def load(path):
    text = (ROOT/path).read_text(encoding='utf-8')
    # 通用解析器不保存比较符；只对本包的两种尺寸比较建立显式测试键。
    text = re.sub(r'planet_size\s*(>=|<=)', lambda m: 'planet_size_'+('ge' if m[1] == '>=' else 'le')+' =', text)
    return {e.key:e.value for e in parse(text)}


TRIGGERS = {**load('mod/common/scripted_triggers/artifact_postcrisis_archive_triggers.txt'),
            **load('mod/common/scripted_triggers/artifact_postcrisis_megastructure_triggers.txt')}
EFFECTS = load('mod/common/scripted_effects/artifact_postcrisis_megastructure_effects.txt')
STAGES = load('mod/common/megastructures/artifact_postcrisis_megastructures.txt')
TECHNOLOGY = load('mod/common/technology/artifact_postcrisis_megastructure_technology.txt')[TECH]
EDICT = load('mod/common/edicts/artifact_postcrisis_megastructure_edicts.txt')['edict_artifact_activate_world_former']


class World(calibration.World):
    def __init__(self):
        super().__init__()
        for c in self.countries.values():
            c.update(flags=set()); c['techs'].update({TECH, F06, E11})
        self.a['flags'].update(VICTORY | {'aemod_has_special_planet'})
        self.a['modifiers'][RECORD] = -1
        for system in self.systems.values(): system['owner'] = self.a
        for p in self.planets.values(): p['pc'] = 'pc_continental'
        self.target = self.add_planet('Empty', system='T')
        self.target.update(owner=None, controller=None, colony=False, pc='pc_barren', size=20,
            deposits=set(), moon=False, anomaly=False, terraforming=False, colonizing=False, surveyed=True)
        self.target['flags'].clear()
        self.mega = dict(kind='megastructure', id='M', owner=self.a, planet=self.target,
            solar_system=self.systems['T'], type=LIVE, flags=set())
        self.megas = [self.mega]
        self.native_from, self.native_fromfrom = self.a, self.mega

    def resolve(self, path, stack):
        if path in ('from', 'fromfrom'): return self.native_from if path == 'from' else self.native_fromfrom
        return super().resolve(path, stack)

    def term(self, e, stack):
        k, v, obj = e.key, e.value, stack[-1]
        if k in TRIGGERS: return self.condition(TRIGGERS[k], stack) == (v == 'yes')
        if k in ('from', 'fromfrom', 'controller'):
            target = self.resolve(k, stack)
            return target is not None and self.condition(v, stack+[target])
        if k in ('has_country_flag', 'has_planet_flag', 'has_megastructure_flag'): return v in obj['flags']
        if k == 'is_planet_class': return obj['pc'] == v
        if k in ('planet_size_ge', 'planet_size_le'):
            return obj['size'] >= float(v) if k.endswith('ge') else obj['size'] <= float(v)
        if k == 'num_deposits': return len(obj['deposits']) == int(v)
        if k == 'is_megastructure_type': return obj['type'] == v
        if k in ('is_moon', 'has_anomaly', 'is_terraforming', 'is_under_colonization'):
            return obj[dict(is_moon='moon', has_anomaly='anomaly', is_terraforming='terraforming',
                            is_under_colonization='colonizing')[k]] == (v == 'yes')
        if k == 'is_surveyed': return obj['surveyed'] == (scalar(v, 'status') == 'yes')
        if k == 'is_inside_border': return obj['owner'] is self.resolve(v, stack)
        if k == 'any_owned_megastructure':
            return any(self.condition(v, stack+[m]) for m in self.megas if m['owner'] is obj)
        if k == 'any_system_planet':
            return any(self.condition(v, stack+[p]) for p in self.planets.values() if p['solar_system'] is obj)
        if k == 'has_no_non_gate_megastructure':
            return (not any(m['solar_system'] is obj for m in self.megas)) == (v == 'yes')
        return super().term(e, stack)

    def execute(self, entries, stack):
        extra = {'random_owned_megastructure', 'set_megastructure_flag', 'set_planet_flag',
                 'remove_planet_flag', 'planet', 'fromfrom', 'change_pc', 'add_deposit'} | EFFECTS.keys()
        if not any(e.key in extra for e in entries): return super().execute(entries, stack)
        # 新叶接口由本夹具执行，整块if仍委托既有解释器，未扩展的语法继续报错。
        for e in entries:
            k, v, obj = e.key, e.value, stack[-1]
            if k in EFFECTS: self.execute(EFFECTS[k], stack)
            elif k == 'random_owned_megastructure':
                ready = [m for m in self.megas if m['owner'] is obj and self.condition(child(v, 'limit'), stack+[m])]
                if ready: self.execute([x for x in v if x.key != 'limit'], stack+[ready[0]])
            elif k in ('planet', 'fromfrom'): self.execute(v, stack+[self.resolve(k, stack)])
            elif k in ('set_planet_flag', 'set_megastructure_flag'): obj['flags'].add(v)
            elif k == 'remove_planet_flag': obj['flags'].discard(v)
            elif k == 'change_pc': obj['pc'] = v
            elif k == 'add_deposit': obj['deposits'].add(v)
            else: super().execute([e], stack)

    def candidate(self):
        return {e.value for e in child(TECHNOLOGY, 'prerequisites')} <= self.a['techs'] and self.condition(child(TECHNOLOGY, 'potential'), [self.a])

    def force(self, country=None):
        self.execute(EFFECTS['artifact_postcrisis_world_former_activate'], [self.a if country is None else country])

    def use(self):
        if not all(self.condition(child(EDICT, k, []), [self.a]) for k in ('potential', 'allow')): return False
        self.execute(child(EDICT, 'effect'), [self.a]); return True


class PostcrisisMegastructureTests(unittest.TestCase):
    def test_shared_knowledge_guards_research_and_forced_effect_without_personal_identity(self):
        w = World(); self.assertTrue(w.candidate())
        for flag in VICTORY:
            w.a['flags'].remove(flag); self.assertFalse(w.candidate()); w.force()
            self.assertEqual(w.target['pc'], 'pc_barren'); w.a['flags'].add(flag)
        for t in (F06, E11):
            w.a['techs'].remove(t); self.assertFalse(w.candidate()); w.a['techs'].add(t)
        w.a['modifiers'].pop(RECORD); w.force(); self.assertEqual(w.target['pc'], 'pc_barren')
        w.a['modifiers'][RECORD] = -1; w.a['techs'].remove(TECH); w.force()
        self.assertEqual(w.target['pc'], 'pc_barren')
        w.a['techs'].add(TECH); self.assertTrue(w.use())

    def test_actual_world_mutation_once_preserves_colonization_and_unrelated_state(self):
        w = World()
        def old_state(): return deepcopy((w.a, w.p['flags'], w.p['modifiers'], w.p['buildings']))
        def receipts(): return deepcopy((w.target['pc'], w.target['flags'], w.target['deposits'], w.mega['flags']))
        before = old_state()
        w.execute(child(STAGES[LIVE], 'on_build_complete'), [w.systems['T']])
        self.assertIn('has_megastructure', w.target['flags']); self.assertTrue(w.use())
        self.assertEqual(w.target['pc'], 'pc_continental')
        self.assertEqual(w.target['deposits'], {'d_rushing_waterfalls', 'd_rich_mountain', 'd_fertile_lands'})
        self.assertIsNone(w.target['owner']); self.assertFalse(w.target['colony'])
        self.assertNotIn('has_megastructure', w.target['flags'])
        self.assertIn('apm_world_formed', w.mega['flags'])
        self.assertEqual(old_state(), before)
        after = receipts(); self.assertFalse(w.use()); w.force()
        self.assertEqual(receipts(), after)

    def test_occupation_and_changed_target_defer_activation_until_safe_again(self):
        w = World(); station = w.systems['T']['starbase']; station['controller'] = w.countries['B']
        self.assertFalse(w.use()); w.force(); self.assertEqual(w.target['pc'], 'pc_barren')
        station['controller'] = w.a
        changes = [('deposits', {'d_minerals_1'}), ('anomaly', True), ('archaeological_site', object()),
                   ('terraforming', True), ('size', 31), ('flags', {'aemusa_ms_anchor_used'})]
        for key, value in changes:
            with self.subTest(key=key):
                absent = key not in w.target; old = w.target.get(key); w.target[key] = value
                self.assertFalse(w.use()); w.force(); self.assertEqual(w.target['pc'], 'pc_barren')
                if absent: w.target.pop(key)
                else: w.target[key] = old
        self.assertTrue(w.use())

    def test_capture_needs_new_owner_knowledge_and_outer_root_is_not_owner(self):
        w = World(); b = w.countries['B']
        w.mega['owner'] = b; w.systems['T']['owner'] = b
        w.systems['T']['starbase'].update(owner=b, controller=b)
        self.assertFalse(w.use()); w.force(b); self.assertEqual(w.target['pc'], 'pc_barren')
        b['flags'].update(VICTORY); b['modifiers'][RECORD] = -1
        self.assertTrue(w.condition(TRIGGERS['artifact_postcrisis_world_former_can_activate'], [w.a, b]))
        w.force(b); self.assertEqual(w.target['pc'], 'pc_continental')

    def test_native_new_order_and_upgrade_guards_keep_foundation_upgradable(self):
        w = World(); system = w.systems['T']; w.megas.clear()
        self.assertTrue(w.condition(child(STAGES[BASE], 'potential'), [w.a]))
        self.assertTrue(w.condition(child(STAGES[BASE], 'possible'), [system]))
        self.assertTrue(w.condition(child(child(STAGES[BASE], 'placement_rules'), 'planet_possible'), [system, w.target]))
        w.mega['type'] = BASE; w.megas.append(w.mega)
        w.execute(child(STAGES[BASE], 'on_build_complete'), [system])
        self.assertFalse(w.condition(child(STAGES[BASE], 'possible'), [system]))
        self.assertTrue(w.condition(child(STAGES[LIVE], 'potential'), [w.a]))
        self.assertTrue(w.condition(child(STAGES[LIVE], 'possible'), [system]))
        self.assertFalse(w.use())
        w.mega['type'] = LIVE; self.assertTrue(w.use())
        # 实体仍占用名额；原生费用/在建排他/维护/殖民和序列化需阶段试玩确认。
        self.assertFalse(w.condition(child(STAGES[BASE], 'possible'), [system]))


if __name__ == '__main__': unittest.main()
