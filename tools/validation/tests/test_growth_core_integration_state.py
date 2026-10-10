"""执行实际成长、方舟、研判选项与旗舰恢复脚本。

引擎控制权、舰船创建、计时到期和存读档为明确夹具；不冒称原生运行证明。
复用已有付费账本解释器，未支持的原生操作继续报错。
"""
from copy import deepcopy
import unittest

from test_artifact_companions_state import Ledger as CompanionLedger, read_script
from test_artifact_companions_state import ROOT
from check_mod import parse, scalar


def load(relative):
    return {e.key: e.value for e in read_script(relative)}


COURT_EVENTS = {scalar(e.value, 'id'): e.value for e in read_script(
    'mod/events/central_court_events.txt') if e.key == 'country_event'}


class CoreLedger(CompanionLedger):
    def __init__(self):
        super().__init__()
        self.effects = dict(self.effects)
        self.effects.update(load('mod/common/scripted_effects/central_court_effects.txt'))
        self.effects.update(load('mod/common/scripted_effects/aemusa_ms_flagship_effects.txt'))
        self.triggers = dict(self.triggers)
        self.triggers.update(load('mod/common/scripted_triggers/central_court_triggers.txt'))
        self.leaders.update({
            'antoniva': {'level': 10, 'flags': {'cc_antoniva_unique'}, 'ruler': True},
            'yanhua': {'level': 7, 'flags': {'cc_yanhua_unique'}, 'class': 'official'},
            'aemusa': {'level': 11, 'flags': {'aemusa_unique_leader'}},
        })
        self.resources['unity'] = 10000
        self.external.update(dict.fromkeys((
            'cc_antoniva_available', 'cc_yanhua_available', 'cc_analysis_target_valid',
            'cc_analysis_has_military_intel', 'cc_analysis_candidate',
            'cc_ark_destination_valid', 'cc_ark_friendly_force',
            'aemusa_ms_flagship_has_safe_capital'), True))
        self.external['aemusa_ms_has_flagship_instance'] = False
        self.objects.update({
            'cc_analysis_candidate': {'kind': 'country', 'flags': set(), 'modifiers': set()},
            'cc_ark_force': {'flags': {'cc_ark_force'}, 'modifiers': set()},
            'cc_capital': {'flags': set(), 'modifiers': set()},
            'cc_yanhua_force': {'flags': set(), 'modifiers': set(), 'leader': self.leaders['yanhua']},
        })
        self.objects['cc_analysis_target'] = self.objects['cc_analysis_candidate']
        self.created_flagships = 0
        self.fleet_fixture = 'cc_yanhua_force'

    def term(self, e, obj, params):
        if e.key == 'leader_class':
            return obj.get('class') == e.value
        if e.key == 'is_ruler':
            return obj.get('ruler', False) == (e.value == 'yes')
        if e.key == 'is_variable_set':
            return e.value in self.variables
        if e.key == 'has_fleet_flag':
            return e.value in obj['flags']
        if e.key == 'exists' and e.value in ('capital_scope', 'leader'):
            return e.value == 'capital_scope' or 'leader' in obj
        if e.key == 'leader':
            return self.condition(e.value, obj['leader'], params)
        if e.key == 'is_ship_class':
            return e.value == 'shipclass_military'
        if e.key == 'any_owned_fleet':
            return self.condition(e.value, self.objects['cc_yanhua_force'], params)
        return super().term(e, obj, params)

    def execute_extra(self, key, value, obj, params):
        if key == 'country_event':
            self.delayed_events.append((scalar(value, 'id'), int(scalar(value, 'days') or 0)))
        elif key == 'every_country':
            target = self.objects['cc_analysis_candidate']
            limit = next((e.value for e in value if e.key == 'limit'), [])
            if self.condition(limit, target, params):
                self.execute([e for e in value if e.key != 'limit'], target, params)
        elif key == 'capital_scope':
            self.execute(value, self.objects['cc_capital'], params)
        elif key == 'save_event_target_as':
            pass  # 引用及原生创建效果由夹具提供。
        elif key == 'create_fleet':
            self.created_flagships += 1
            self.external['aemusa_ms_has_flagship_instance'] = True
        else:
            super().execute_extra(key, value, obj, params)

    def claim(self, label):
        options = [e.value for e in COURT_EVENTS['central_court.51'] if e.key == 'option']
        option = next(body for body in options if scalar(body, 'name') == label)
        self.execute(next(e.value for e in option if e.key == 'hidden_effect'))


class GrowthCoreIntegrationTests(unittest.TestCase):
    def test_crisis_pipeline_stays_below_native_five_level_init_boundary(self):
        # 4.5.2冷启动实测：第五层仍有未展开效果时报告CRITICAL；延迟事件不算同步调用。
        effects = {e.key: e.value for path in (ROOT / 'mod/common/scripted_effects').glob('*.txt')
                   for e in parse(path.read_text(encoding='utf-8'))}

        def calls(entries):
            for e in entries:
                if e.key in effects:
                    yield e.key
                if isinstance(e.value, list):
                    yield from calls(e.value)

        def depth(key, visited=()):
            self.assertNotIn(key, visited, '同步脚本调用不得成环')
            return 1 + max((depth(c, visited + (key,)) for c in calls(effects[key])), default=0)

        self.assertLessEqual(depth('aemusa_ms_exclusive_monthly_update'), 4)

    def test_ark_growth_preserves_paid_shared_cooldown_and_running_timer(self):
        for level, days in ((10, 60), (11, 45), (21, 30)):
            with self.subTest(level=level):
                x = CoreLedger()
                x.leaders['antoniva']['level'] = level
                x.effect('cc_start_ark_warp')
                self.assertEqual(days, x.timed_flags['cc_ark_calibration_time'])
                self.assertEqual(360, x.timed_flags['cc_ark_cooldown'])
                paid = deepcopy(x.resources)
                x.leaders['antoniva']['level'] = 30
                x.effect('cc_start_ark_warp')
                self.assertEqual(days, x.timed_flags['cc_ark_calibration_time'])
                self.assertEqual(paid, x.resources)
                self.assertEqual(9500, x.resources['energy'])

    def test_yanhua_growth_respects_month_guard_and_fixed_claim_record(self):
        for level, months, days in ((7, 3, 180), (11, 3, 240), (21, 2, 300)):
            with self.subTest(level=level):
                x = CoreLedger()
                x.leaders['yanhua']['level'] = level
                x.effect('cc_start_analysis')
                x.external['cc_analysis_has_military_intel'] = False
                x.effect('cc_analysis_monthly')
                self.assertEqual(0, x.variables['cc_analysis_progress'])
                x.external['cc_analysis_has_military_intel'] = True
                for _ in range(months):
                    x.flags.discard('cc_analysis_month_counted')
                    x.effect('cc_analysis_monthly')
                    progress = x.variables['cc_analysis_progress']
                    x.effect('cc_analysis_monthly')
                    self.assertEqual(progress, x.variables['cc_analysis_progress'])
                x.leaders['yanhua']['level'] = 30 if level == 7 else 7
                x.claim('cc.prepare_capital')
                x.claim('cc.prepare_capital')
                self.assertEqual(days, x.objects['cc_capital']['modifier_days']['cc_yanhua_internal_preparation'])
                self.assertNotIn('cc_analysis_conclusion', x.flags)
                self.assertIn('cc_analysis_cooldown', x.flags)

    def test_flagship_growth_keeps_unique_instance_and_timer_blocks_stale_callback(self):
        for level, days in ((7, 90), (11, 75), (21, 60), (None, 90)):
            with self.subTest(level=level):
                x = CoreLedger()
                if level is None:
                    del x.leaders['aemusa']
                else:
                    x.leaders['aemusa']['level'] = level
                x.flags.add('aemusa_ms_country_flagship_commissioned')
                x.effect('aemusa_ms_flagship_begin_recovery')
                self.assertEqual(days, x.timed_flags['aemusa_ms_country_flagship_recovery_time_remaining'])
                self.assertEqual([('aemusa_flagship.2', days)], x.delayed_events)
                x.effect('aemusa_ms_flagship_begin_recovery')
                x.effect('aemusa_ms_flagship_finish_recovery')
                x.effect('aemusa_ms_flagship_ensure_present')
                self.assertEqual(0, x.created_flagships)
                self.assertEqual(1, len(x.delayed_events))
                x.flags.discard('aemusa_ms_country_flagship_recovery_time_remaining')
                x.effect('aemusa_ms_flagship_finish_recovery')
                x.external['aemusa_ms_flagship_has_safe_capital'] = False
                x.effect('aemusa_ms_flagship_ensure_present')
                self.assertEqual(0, x.created_flagships)
                self.assertIn('aemusa_ms_country_flagship_recovery_ready', x.flags)
                x.external['aemusa_ms_flagship_has_safe_capital'] = True
                x.effect('aemusa_ms_flagship_ensure_present')
                x.effect('aemusa_ms_flagship_ensure_present')
                self.assertEqual(1, x.created_flagships)

    def test_yanhua_fleet_claim_uses_country_record_and_old_conclusion_stays_basic(self):
        for record, days in ((None, 180), (2, 240), (3, 300)):
            with self.subTest(record=record):
                x = CoreLedger()
                x.leaders['yanhua']['level'] = 30
                x.flags.update(('cc_analysis_conclusion', 'cc_analysis_fresh'))
                if record is not None:
                    x.variables['cc_analysis_record_stage'] = record
                x.claim('cc.military_counter')
                self.assertEqual(days, x.objects['cc_yanhua_force']['modifier_days']['cc_yanhua_fleet_counter'])
                self.assertNotIn('cc_analysis_conclusion', x.flags)
                x.claim('cc.prepare_capital')
                self.assertNotIn('modifier_days', x.objects['cc_capital'])


if __name__ == '__main__':
    unittest.main()
