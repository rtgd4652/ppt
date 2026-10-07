"""执行新增终章实际脚本，检查决定分离、三结果、研修与重复奖励保护。

仅覆盖账本子集；不模拟原版作用域、经验曲线、UI、调度或真实存读档。
"""

from copy import deepcopy
import re
import unittest

from test_awp02_state import EFFECTS, TRIGGERS, PREFIX, ROOT, child, parse, scalar
from test_awp04_entry_state import CrisisLedger


def script(path):
    text = (ROOT / path).read_text(encoding='utf-8')
    names = {'>=': 'greater_equal', '>': 'greater_than', '<=': 'less_equal', '<': 'less_than'}
    text = re.sub(r'\b(value|has_base_skill)\s*(>=|<=|>|<)\s*(\d+)',
                  lambda m: f'{m[1]}_{names[m[2]]} = {m[3]}', text)
    return parse(text)


for path in ('mod/common/scripted_triggers/aemusa_ms_finale_triggers.txt',
             'mod/common/scripted_triggers/aemusa_ms_state_audit_triggers.txt'):
    TRIGGERS.update({entry.key: entry.value for entry in script(path)})
EFFECTS.update({entry.key: entry.value for entry in script(
    'mod/common/scripted_effects/aemusa_ms_finale_effects.txt')})


class FinaleLedger(CrisisLedger):
    def __init__(self):
        super().__init__()
        self.events.update({scalar(e.value, 'id'): e.value for e in script(
            'mod/events/aemusa_ms_finale_events.txt') if e.key == 'country_event'})
        self.level = 30
        self.leader_flags = {'aemusa_unique_leader'}
        self.traits = {'leader_trait_aemusa_commander'}
        self.resources = {'energy': 10000, 'unity': 10000}

    def snapshot(self):
        return super().snapshot(), self.level, set(self.leader_flags), set(self.traits)

    def term(self, entry):
        if entry.key in {'event_target:aemusa_leader', 'owner'}:
            # 只提供固定测试对象；引擎的实际领袖所有者须另验。
            return self.condition(entry.value)
        if entry.key == 'is_same_value' and entry.value == 'root':
            return True
        if entry.key == 'has_leader_flag':
            return entry.value in self.leader_flags
        if entry.key == 'has_base_skill_greater_equal':
            return self.level >= int(entry.value)
        if entry.key == 'check_variable':
            current = self.variables.get(scalar(entry.value, 'which'), 0)
            for key, compare in (
                ('value_greater_equal', lambda a, b: a >= b),
                ('value_greater_than', lambda a, b: a > b),
                ('value_less_equal', lambda a, b: a <= b),
                ('value_less_than', lambda a, b: a < b),
            ):
                target = scalar(entry.value, key)
                if target is not None:
                    return compare(current, float(target))
        return super().term(entry)

    def execute_extra(self, entry):
        if entry.key == 'event_target:aemusa_leader':
            self.execute(entry.value)
        elif entry.key == 'add_skill':
            self.level += int(entry.value)
        elif entry.key == 'set_leader_flag':
            self.leader_flags.add(entry.value)
        elif entry.key == 'add_trait':
            self.traits.add(entry.value)
        elif entry.key == 'aemusa_refresh_portrait':
            pass  # 图像与30级肖像为运行时表现，不伪装成已验证。
        else:
            super().execute_extra(entry)


def ready(level=30):
    ledger = FinaleLedger()
    ledger.level = level
    ledger.variables.update({PREFIX + 'chapter_index': 14,
        PREFIX + 'act_index': 5, PREFIX + 'investigation_aemusa_decision_index': 1,
        PREFIX + 'civilization_responsibility_radius_index': 2,
        PREFIX + 'first_intervention_decision_index': 1})
    ledger.flags.update(PREFIX + f'chapter_{n:02d}_completed' for n in range(14))
    ledger.flags.update(PREFIX + f'settlement_chapter_{n:02d}_done' for n in range(14))
    ledger.flags.update(PREFIX + name for name in (
        'history_fallen_empire_war_settled', 'history_vanilla_crisis_settled',
        'exclusive_future_reopened', 'investigation_rights_protected',
        'investigation_player_support_confirmed', 'investigation_joint_response_authorized'))
    ledger.flags.update({'aemusa_ms_crisis_exclusive_completed', 'aemusa_ms_crisis_exclusive_settled'})
    return ledger


def step(ledger, number, suffix='continue'):
    ledger.queue.clear()
    ledger.step(f'aemusa_finale.{number}', suffix)


def route(ledger):
    ledger.queue.clear()
    assert ledger.open('aemusa_finale.1')
    return ledger.queue.pop()[0]


def reach_player_choice(intent='possibilities'):
    ledger = ready()
    for number, choice in ((10, 'review'), (20, 'public'), (30, 'boundaries'), (40, 'recognize'),
                           (50, 'continue'), (60, intent)):
        step(ledger, number, choice)
    assert route(ledger) == 'aemusa_finale.70'
    ledger.open('aemusa_finale.70')
    ledger.queue.clear()
    return ledger


class Milestone2FinaleTests(unittest.TestCase):
    def test_success_keeps_authorization_response_and_identity_separate(self):
        ledger = reach_player_choice()
        ledger.choose('aemusa_finale.70', 'defer')
        self.assertEqual(ledger.variables['aemusa_ms_decision_joint_state_index'], 1)
        self.assertNotIn('aemusa_ms_decision_player_authorized', ledger.flags)
        ledger = deepcopy(ledger)  # 持久账本恢复，不冒称真实存档测试。
        self.assertEqual(route(ledger), 'aemusa_finale.70')
        step(ledger, 72, 'authorize')
        self.assertIn('aemusa_ms_decision_player_authorized', ledger.flags)
        self.assertNotIn('aemusa_ms_decision_aemusa_accepted', ledger.flags)
        self.assertNotIn(PREFIX + 'fate_sovereign_authority_active', ledger.flags)
        ledger.open('aemusa_finale.75')
        self.assertIn('aemusa_ms_decision_aemusa_accepted', ledger.flags)
        step(ledger, 80, 'listen')
        step(ledger, 90)
        self.assertEqual(ledger.variables[PREFIX + 'chapter_index'], 16)
        self.assertNotIn(PREFIX + 'fate_sovereign_authority_active', ledger.flags)
        for number in (120, 130, 140, 150, 160, 170, 180):
            step(ledger, number)
        self.assertEqual(ledger.variables[PREFIX + 'chapter_index'], 18)
        self.assertEqual(ledger.variables[PREFIX + 'epilogue_tone_index'], 2)
        self.assertIn(PREFIX + 'epilogue_settled', ledger.flags)
        self.assertIn('leader_trait_aemusa_fate_sovereign', ledger.traits)
        self.assertIn('leader_trait_aemusa_commander', ledger.traits)
        before = ledger.snapshot()
        ledger.open('aemusa_finale.130', forced=True)
        ledger.choose('aemusa_finale.130', 'continue')
        self.assertEqual(ledger.snapshot(), before)
        self.assertEqual(route(ledger), 'aemusa_finale.200')

    def test_player_refusal_is_permanent_and_distinct_from_defer(self):
        ledger = reach_player_choice()
        step(ledger, 71, 'refuse')
        step(ledger, 100, 'accept')
        self.assertIn(PREFIX + 'ending_non_transform_player_refusal_settled', ledger.flags)
        self.assertNotIn('aemusa_ms_decision_player_authorized', ledger.flags)
        self.assertNotIn('aemusa_ms_decision_aemusa_refused', ledger.flags)
        self.assertNotIn('leader_trait_aemusa_fate_sovereign', ledger.traits)
        self.assertEqual(route(ledger), 'aemusa_finale.200')
        before = ledger.snapshot()
        ledger.choose('aemusa_finale.72', 'authorize')
        self.assertEqual(ledger.snapshot(), before)

    def test_aemusa_refusal_follows_her_own_response_and_cannot_be_reasked(self):
        ledger = reach_player_choice('certainty')
        step(ledger, 72, 'authorize')
        self.assertNotIn('aemusa_ms_decision_aemusa_refused', ledger.flags)
        ledger.open('aemusa_finale.75')
        self.assertIn('aemusa_ms_decision_aemusa_refused', ledger.flags)
        step(ledger, 110, 'accept')
        self.assertIn(PREFIX + 'ending_non_transform_aemusa_refusal_settled', ledger.flags)
        self.assertEqual(route(ledger), 'aemusa_finale.200')
        before = ledger.snapshot()
        ledger.execute(EFFECTS['aemusa_ms_finale_resolve_aemusa_once'])
        self.assertEqual(ledger.snapshot(), before)

    def test_training_waits_spends_once_and_preserves_civilization_facts(self):
        ledger = ready(level=29)
        for number, suffix in ((10, 'review'), (20, 'public'), (30, 'boundaries')):
            step(ledger, number, suffix)
        self.assertEqual(route(ledger), 'aemusa_finale.3')
        self.assertIn('aemusa_ms_truth_civilization_facts_settled', ledger.flags)
        step(ledger, 3, 'train')
        self.assertEqual(ledger.resources, {'energy': 9800, 'unity': 9500})
        before = ledger.snapshot()
        ledger.choose('aemusa_finale.3', 'train')
        self.assertEqual(ledger.snapshot(), before)
        ledger.elapse(179)
        ledger.open('aemusa_finale.5')
        self.assertEqual(ledger.level, 29)
        ledger = deepcopy(ledger)
        ledger.elapse(1)
        ledger.open('aemusa_finale.5')
        self.assertEqual(ledger.level, 30)
        before = ledger.snapshot()
        ledger.open('aemusa_finale.5')
        self.assertEqual(ledger.snapshot(), before)
        self.assertNotIn('aemusa_ms_decision_aemusa_accepted', ledger.flags)
        self.assertEqual(route(ledger), 'aemusa_finale.40')

    def test_forced_final_identity_without_both_sources_writes_nothing(self):
        ledger = reach_player_choice()
        step(ledger, 72, 'authorize')
        before = ledger.snapshot()
        ledger.open('aemusa_finale.130', forced=True)
        ledger.choose('aemusa_finale.130', 'continue')
        self.assertEqual(ledger.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
