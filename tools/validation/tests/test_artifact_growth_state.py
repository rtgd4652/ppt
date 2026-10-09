"""执行十人成长生产脚本，检查等级边界、失去人物后的缓存清理及只读边界。"""
import unittest
from copy import deepcopy
from test_artifact_engineering_state import Ledger


ROLES = [['aemusa','aemusa_unique_leader'],['antoniva','cc_antoniva_unique'],['yanhua','cc_yanhua_unique'],['seth','seth_unique_leader'],['yutong','yutong_unique_leader'],['rabi','rabi_unique_leader'],['an','ar_an_unique'],['greysa','ar_greysa_unique'],['wenzi','ar_wenzi_unique'],['li','ar_li_unique']]


class GrowthStateTests(unittest.TestCase):
    def test_every_registered_role_obeys_real_level_boundaries(self):
        for role, flag in ROLES:
            for level, stage, primary, support in (
                (1, 1, 1, 1.1), (10, 1, 1, 1.1),
                (11, 2, 1.25, 1.2), (20, 2, 1.25, 1.2),
                (21, 3, 1.5, 1.3), (30, 3, 1.5, 1.3),
            ):
                with self.subTest(role=role, level=level):
                    x = Ledger()
                    x.leaders = {'actor': {'flags': {flag}, 'class': 'official',
                                           'level': level, 'xp': 0}}
                    x.effect('artifact_growth_refresh')
                    self.assertEqual(stage, x.variables['ag_' + role + '_stage'])
                    self.assertAlmostEqual(primary, x.variables['ag_' + role + '_primary'])
                    self.assertAlmostEqual(support, x.variables['ag_' + role + '_support'])

    def test_removed_actor_cannot_leave_old_contribution_and_unmarked_npc_is_ignored(self):
        for role, flag in ROLES:
            with self.subTest(role=role):
                x = Ledger()
                x.leaders = {'actor': {'flags': {flag}, 'class': 'commander',
                                       'level': 30, 'xp': 0}}
                x.effect('artifact_growth_refresh')
                x.leaders = {'npc': {'flags': set(), 'class': 'commander',
                                     'level': 30, 'xp': 0}}
                x.effect('artifact_growth_refresh')
                for suffix in ('stage', 'primary', 'support'):
                    self.assertEqual(0, x.variables['ag_' + role + '_' + suffix])

    def test_roster_refresh_never_creates_work_records_experience_or_rewards(self):
        x = Ledger()
        x.flags = {'ar_an_working', 'ae_eng_completed'}
        before = deepcopy((x.flags, x.resources, x.leaders, x.techs,
                           x.options, x.events, x.targets, x.capital, x.variables))
        x.effect('artifact_growth_refresh')
        x.effect('artifact_growth_refresh')
        after = (x.flags, x.resources, x.leaders, x.techs,
                 x.options, x.events, x.targets, x.capital,
                 {k: v for k, v in x.variables.items() if not k.startswith('ag_')})
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
