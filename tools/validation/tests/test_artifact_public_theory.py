"""执行A12正式条件/效果及C10消费者；不把源码夹具当作游戏运行证据。

A11完成模型是已单独验证的接口输入。C10方法仍从本次实际执行的原样本/
材料项目归档取得，检查无新等待、免费汇编、原付费复现与拥有者清理。
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_artifact_research_reproduction as reproduction

base = reproduction.foundation
child, load = base.child, base.load
TECH = 'tech_artifact_public_artifact_theory'
A11 = 'tech_artifact_high_dimensional_model_review'
MODEL = 'amr_model_reviewed'
METHODS = 'apt_public_engineering_methods'
HIGH = 'building_artifact_high_dimensional_review_station'
YARD = 'building_artifact_engineering_supply_yard'
ANCHOR = 'building_artifact_rule_anchor_test_site'
B14 = 'tech_artifact_strategic_engineering_supply'
E08 = 'tech_artifact_rule_anchoring_engineering'
TRIGGERS = {**load('mod/common/scripted_triggers/artifact_public_theory_triggers.txt'),
            **load('mod/common/scripted_triggers/artifact_observation_review_triggers.txt')}
EFFECTS = load('mod/common/scripted_effects/artifact_public_theory_effects.txt')
DECISION = load('mod/common/decisions/artifact_public_theory_decisions.txt')['decision_artifact_public_theory_compile']


class World(reproduction.World):
    def __init__(self):
        super().__init__()
        for country in self.countries.values():
            country['techs'].update({TECH, A11, B14, E08})
            country['modifiers'] = {}
        # 真实A11项目输出作为接口输入；不重复运行那一套月度模型检查。
        self.countries['A']['modifiers'][MODEL] = -1

    def prepare(self, kind='sample'):
        self.source(kind)
        assert self.archive(kind)
        self.planets['P']['buildings'].add(HIGH)

    def compile(self):
        p = self.planets['P']
        if not all(self.condition(child(DECISION, k, []), p, {}) for k in ('potential', 'allow')):
            return False
        self.execute(child(DECISION, 'effect'), p, {})
        return True

    def qualified(self, country='A'):
        return self.condition(TRIGGERS['artifact_public_theory_qualified'], self.countries[country], {})


class PublicTheoryTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(base.TRIGGERS, TRIGGERS))
        self.enterContext(patch.dict(base.EFFECTS, EFFECTS))

    def test_sources_research_and_live_site_are_required(self):
        for reason in ('A12', 'A11', 'C10', 'model', 'method', 'disabled', 'control', 'bombardment'):
            with self.subTest(reason=reason):
                w = World(); w.prepare()
                a, p = w.countries['A'], w.planets['P']
                if reason in ('A12', 'A11', 'C10'):
                    a['techs'].remove({'A12': TECH, 'A11': A11, 'C10': reproduction.C10}[reason])
                elif reason == 'model': a['modifiers'].pop(MODEL)
                elif reason == 'method': a['flags'].remove(reproduction.SAMPLE)
                elif reason == 'disabled': p['inactive'].add(HIGH)
                elif reason == 'control': p['controller'] = 'B'
                else: p['bombarded'] = True
                before = deepcopy((w.countries, w.planets, w.targets))
                self.assertFalse(w.compile()); self.assertFalse(w.qualified())
                # 防止直接调用效果绕过同一来源守卫。
                w.execute(EFFECTS['artifact_public_theory_compile'], p, {})
                self.assertEqual((w.countries, w.planets, w.targets), before)

    def test_free_immediate_compile_preserves_existing_work_and_story_records(self):
        w = World(); w.prepare('materials')
        a, p = w.countries['A'], w.planets['P']
        a['flags'].add('aemusa_ms_country_history_vanilla_crisis_started')
        a['vars']['aemusa_ms_country_anchor_losses'] = 2
        # 其他系统已有当地项目/库存不因汇编被清理或改写。
        p['modifiers']['acs_supply_reserved'] = -1
        p['vars']['acs_unrelated_work'] = 2
        before = deepcopy((w.countries, w.planets, w.targets))
        self.assertFalse(w.qualified()); self.assertTrue(w.compile()); self.assertTrue(w.qualified())
        expected = before
        expected[0]['A']['modifiers'][METHODS] = -1
        self.assertEqual((w.countries, w.planets, w.targets), expected)
        self.assertFalse(w.compile())
        w.execute(EFFECTS['artifact_public_theory_compile'], p, {})
        self.assertEqual((w.countries, w.planets, w.targets), expected)
        p['buildings'].clear()
        self.assertTrue(w.qualified())  # 已完成的国家知识不依赖原站仍在。

    def test_both_engineering_sites_reuse_paid_projects_and_only_known_methods(self):
        for site, kind in ((YARD, 'sample'), (ANCHOR, 'materials')):
            with self.subTest(site=site, kind=kind):
                w = World(); w.prepare(kind)
                a = w.countries['A']; a['techs'].remove(reproduction.E05)
                q = w.add_planet('Q'); q['buildings'] = {site}
                mode = 'reproduce_' + kind
                before = deepcopy(a['resources'])
                self.assertFalse(w.choose(mode, 'Q'))  # A12研究不等于已汇编。
                self.assertEqual(a['resources'], before)
                self.assertTrue(w.compile())
                unknown = 'reproduce_materials' if kind == 'sample' else 'reproduce_sample'
                self.assertFalse(w.choose(unknown, 'Q'))
                self.assertTrue(w.choose(mode, 'Q')); self.assertFalse(w.choose(mode, 'Q'))
                expected = {**before, 'energy': before['energy'] - 300,
                            'consumer_goods': before['consumer_goods'] - 150}
                self.assertEqual(a['resources'], expected)
                for _ in range(5): w.monthly()
                result = 'artifact_foundation_' + ('sample_analysis' if kind == 'sample' else 'materials_study')
                self.assertNotIn(result, q['modifiers']); self.assertEqual(q['vars']['arf_r1_progress'], 5)
                w.monthly(); self.assertEqual(q['modifiers'], {result: 720})
                self.assertEqual(a['resources'], expected)

    def test_new_route_pauses_then_resumes_without_paying_again(self):
        w = World(); w.prepare(); self.assertTrue(w.compile())
        a = w.countries['A']; a['techs'].remove(reproduction.E05)
        q = w.add_planet('Q'); q['buildings'] = {YARD}
        self.assertTrue(w.choose('reproduce_sample', 'Q')); w.monthly()
        paid = deepcopy(a['resources'])
        for stop, resume in (
            (lambda: q['inactive'].add(YARD), lambda: q['inactive'].clear()),
            (lambda: q.update(controller='B'), lambda: q.update(controller='A')),
            (lambda: a['techs'].remove(B14), lambda: a['techs'].add(B14)),
            (lambda: a['techs'].remove(TECH), lambda: a['techs'].add(TECH)),
        ):
            stop(); w.monthly(); self.assertEqual(q['vars']['arf_r1_progress'], 1)
            resume()
        for _ in range(5): w.monthly()
        self.assertEqual(q['modifiers'], {'artifact_foundation_sample_analysis': 720})
        self.assertEqual(a['resources'], paid)

    def test_transfer_keeps_original_country_knowledge_and_rejects_old_window(self):
        w = World(); w.prepare(); self.assertTrue(w.compile())
        q = w.add_planet('Q'); q['buildings'] = {ANCHOR}
        ctx = w.open('sample', 'Q'); self.assertTrue(w.choose('reproduce_sample', 'Q', ctx))
        w.monthly()
        before = deepcopy(w.countries)
        q['owner'] = q['controller'] = 'B'
        w.dispatch('artifact_foundation.2', q)
        self.assertNotIn('arf_r1_active', q['flags'])
        self.assertFalse(w.choose('reproduce_sample', 'Q', ctx))
        self.assertFalse(w.choose('reproduce_sample', 'Q'))
        self.assertTrue(w.qualified('A')); self.assertFalse(w.qualified('B'))
        # 原编订站随后转让也不会转移国家资格。
        w.planets['P']['owner'] = w.planets['P']['controller'] = 'B'
        self.assertFalse(w.compile())
        self.assertEqual(w.countries, before)


if __name__ == '__main__':
    unittest.main()
