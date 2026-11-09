"""回放结尾交接入口和状态文案，档案、舰装及平台条件均求值于各模块既有夹具。"""
import re
import unittest
from unittest.mock import patch

import test_artifact_postcrisis_archive as archive
import test_artifact_postcrisis_fleet as fleet
import test_artifact_postcrisis_megastructure as platform
from check_mod import parse, scalar

ROOT, child = archive.calibration.ROOT, archive.child
FINALE = archive.calibration.events('mod/events/aemusa_ms_finale_events.txt')
MEMORY = archive.calibration.events('mod/events/aemusa_dialogue_events.txt')['aemusa_dialogue.4']
REPORT = FINALE['aemusa_finale.210']
SITE = FINALE['aemusa_finale.211']
TEXTS = {
    scalar(entry.value, 'name'): entry.value for entry in parse(
        (ROOT / 'mod/common/scripted_loc/artifact_postcrisis_handover_loc.txt').read_text(encoding='utf-8'))
}


def option(event, name):
    return next(entry.value for entry in event if entry.key == 'option' and scalar(entry.value, 'name') == name)


def displayed(section, condition):
    # 原版 000_example 定义：random=no 时选同权的首个有效文本，均未命中时使用 default。
    body = TEXTS['GetArtifactPostcrisis' + section]
    assert scalar(body, 'random') == 'no'
    for entry in body:
        if entry.key == 'text' and condition(child(entry.value, 'trigger')):
            return scalar(entry.value, 'localization_key')
    return scalar(body, 'default')


class PostcrisisHandoverTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(archive.calibration.TRIGGERS, archive.TRIGGERS))
        self.enterContext(patch.dict(archive.calibration.EFFECTS, archive.EFFECTS))

    def test_entry_reads_common_victory_without_personal_conditions(self):
        world = archive.World()
        visible = child(REPORT, 'trigger')
        for screen in (FINALE['aemusa_finale.10'], FINALE['aemusa_finale.200'], MEMORY):
            link = option(screen, 'aemusa_finale.handover')
            self.assertEqual([(e.key, e.value) for e in child(link, 'trigger')],
                             [(e.key, e.value) for e in visible])
            effect = child(link, 'hidden_effect')
            self.assertEqual([e.key for e in effect], ['country_event'])
            self.assertEqual(scalar(child(effect, 'country_event'), 'id'), 'aemusa_finale.210')
        world.a['flags'] = set(archive.VICTORY)
        before = world.state()
        for _ in range(2):
            self.assertTrue(world.condition(visible, [world.a]))
        self.assertEqual(before, world.state())
        for flag in archive.VICTORY:
            world.a['flags'].remove(flag)
            self.assertFalse(world.condition(visible, [world.a]))
            world.a['flags'].add(flag)
        world.a['species'] = 'HUM'
        self.assertTrue(world.condition(visible, [world.a]))
        descriptions = [scalar(e.value, 'text') for e in REPORT if e.key == 'desc'
                        and world.condition(child(e.value, 'trigger'), [world.a])]
        self.assertEqual(descriptions, ['aemusa_finale.210.history'])
        world.a['ai'] = True
        self.assertFalse(world.condition(visible, [world.a]))

    def test_old_personal_result_remains_readable_after_leader_leaves_without_granting_public_victory(self):
        self.enterContext(patch.dict(archive.finale.TRIGGERS, archive.TRIGGERS))
        ledger = archive.finale.reach_player_choice()
        archive.finale.step(ledger, 71, 'refuse')
        archive.finale.step(ledger, 100, 'accept')
        ledger.leader_flags.clear()
        ledger.flags.discard('aemusa_ms_country_settlement_exclusive_crisis_victory_done')
        before = ledger.snapshot()
        self.assertFalse(ledger.open('aemusa_finale.1'))
        self.assertFalse(ledger.open('aemusa_finale.210'))
        self.assertTrue(ledger.condition(child(option(MEMORY, 'aemusa_finale.210.result'), 'trigger')))
        self.assertTrue(ledger.open('aemusa_finale.200'))
        self.assertEqual(ledger.snapshot(), before)
        ledger.flags.remove('aemusa_ms_decision_player_refused')
        self.assertFalse(ledger.open('aemusa_finale.200'))

    def test_legacy_ledger_prints_available_counts_without_fabricating_zero(self):
        world = archive.World()
        report = lambda: displayed('Ledger', lambda conditions: world.condition(conditions, [world.a]))
        names = ['projections_defeated', 'anchors_archived', 'anchors_liberated', 'anchor_losses']
        ledger = {'aemusa_ms_country_' + name: n for name, n in zip(names, [3, 3, 3, 0])}
        world.a['vars'].update(ledger)
        self.assertEqual(report(), 'aph.handover.ledger')
        for name, value in ledger.items():
            del world.a['vars'][name]
            self.assertEqual(report(), 'aph.handover.ledger_summary')
            world.a['vars'][name] = value

    def test_archive_map_target_requires_same_available_site_as_the_local_decision(self):
        world = archive.World()
        self.assertEqual(scalar(SITE, 'location'), 'root')
        locate = option(REPORT, 'aemusa_finale.210.locate')
        pick = child(child(locate, 'hidden_effect'), 'random_owned_colony')
        self.assertEqual(scalar(child(child(pick, 'carrier'), 'planet_event'), 'id'), 'aemusa_finale.211')
        self.assertEqual([e.key for e in pick], ['limit', 'carrier'])
        view = lambda: displayed('Archive', lambda conditions: world.condition(conditions, [world.a]))
        self.assertEqual(view(), 'aph.handover.archive_ready')
        world.a['resources']['minor_artifacts'] = 19
        self.assertEqual(view(), 'aph.handover.archive_funding')
        for planet, expected in ((world.p, False), (world.q, True)):
            self.assertEqual(world.condition(child(pick, 'limit'), [world.a, world.colony(planet)]), expected)
            self.assertEqual(world.condition(child(SITE, 'trigger'), [planet]), expected)
        world.q['inactive'].add(archive.HIGH)
        self.assertFalse(world.condition(child(locate, 'trigger'), [world.a]))
        self.assertEqual(view(), 'aph.handover.archive_site')
        world.a['techs'].remove(archive.TECH)
        self.assertEqual(view(), 'aph.handover.archive_research')
        world.a['techs'].remove(archive.F05)
        self.assertEqual(view(), 'aph.handover.archive_prerequisites')
        world = archive.World()
        self.assertTrue(world.use())
        self.assertEqual(view(), 'aph.handover.archive_decoded')
        self.assertFalse(world.condition(child(locate, 'trigger'), [world.a]))
        self.assertFalse(world.condition(child(SITE, 'trigger'), [world.q]))

    def test_fleet_reports_actual_design_eligibility_and_research(self):
        self.enterContext(patch.dict(fleet.base.TRIGGERS, {
            **fleet.supply.TRIGGERS, **fleet.strategic.TRIGGERS, **fleet.TRIGGERS}))
        world = fleet.World()
        view = lambda: displayed('Fleet', lambda conditions: world.condition(conditions, world.a, {}))
        self.assertEqual(view(), 'aph.handover.fleet_design')
        world.a['modifiers'].pop(fleet.strategic.hull.QUALIFIED)
        self.assertEqual(view(), 'aph.handover.fleet_qualification')
        world.a['techs'].remove(fleet.TECH)
        self.assertEqual(view(), 'aph.handover.fleet_research')
        world.a['techs'].remove(fleet.strategic.TECH)
        self.assertEqual(view(), 'aph.handover.fleet_hull')
        world.a['modifiers'].pop(fleet.RECORD)
        self.assertEqual(view(), 'aph.handover.fleet_wait')
        world.a['bio'] = True
        self.assertEqual(view(), 'aph.handover.fleet_bio')

    def test_platform_reports_current_target_and_prioritises_another_usable_site(self):
        world = platform.World()
        view = lambda: displayed('WorldFormer', lambda conditions: world.condition(conditions, [world.a]))
        self.assertEqual(view(), 'aph.handover.platform_ready')
        world.systems['T']['starbase']['controller'] = world.countries['B']
        self.assertEqual(view(), 'aph.handover.platform_control')
        world.systems['T']['starbase']['controller'] = world.a
        self.assertTrue(world.use())
        self.assertEqual(view(), 'aph.handover.platform_formed')
        other = dict(world.mega, type=platform.BASE, flags=set())
        world.megas.append(other)
        self.assertEqual(view(), 'aph.handover.platform_upgrade')
        world.megas.clear()
        self.assertEqual(view(), 'aph.handover.platform_build')
        world.a['techs'].remove(platform.TECH)
        self.assertEqual(view(), 'aph.handover.platform_research')
        world.a['techs'].remove(platform.E11)
        self.assertEqual(view(), 'aph.handover.platform_infrastructure')
        world.a['modifiers'].pop(platform.RECORD)
        self.assertEqual(view(), 'aph.handover.platform_wait')

    def test_every_scripted_status_and_reused_game_name_resolves(self):
        folder = ROOT / 'mod/localisation/simp_chinese'
        strings = {}
        for path in folder.glob('*.yml'):
            strings.update(re.findall(r'^\s*([\w.-]+):\d*\s+"(.*)"', path.read_text(encoding='utf-8-sig'), re.M))
        expected = set(re.findall(r'\[Root\.(GetArtifactPostcrisis\w+)\]', strings['aemusa_finale.210.desc']))
        self.assertEqual(expected, set(TEXTS))
        for body in TEXTS.values():
            keys = [scalar(e.value, 'localization_key') for e in body if e.key == 'text'] + [scalar(body, 'default')]
            for key in keys:
                for reference in re.findall(r'\$([\w.]+)\$', strings[key]):
                    self.assertIn(reference, strings)


if __name__ == '__main__':
    unittest.main()
