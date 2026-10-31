"""执行D12正式条件和回调，检查敌我/范围、费用契约和共享冷却。

原生按钮、扣费、冷却计时和序列化由外部夹具代表，不等于游戏或真实存读档通过。
未知条件/效果即报错；PREV链按实际作用域栈解释，避免只比对源码字符串。
"""
from copy import deepcopy
import unittest

import test_artifact_foundation_projects as base
from check_mod import parse, scalar

child = base.child
TECH = 'tech_artifact_limited_field_suppression'
MODULE = 'ARTIFACT_FIELD_SUPPRESSOR'
SIZE = 'artifact_strategic_cruiser'
TRIGGERS = {**base.load('mod/common/scripted_triggers/artifact_strategic_hull_triggers.txt'),
            **base.load('mod/common/scripted_triggers/artifact_field_suppression_triggers.txt')}
ACTION = base.load('mod/common/scripted_actions/artifact_field_suppression_actions.txt')['artifact_field_suppression']
ON_ACTIONS = base.load('mod/common/on_actions/artifact_field_suppression_on_actions.txt')
EVENTS = {scalar(e.value, 'id'): e.value for e in parse((base.ROOT / 'mod/events/artifact_field_suppression_events.txt').read_text(encoding='utf-8')) if e.key == 'fleet_event'}
PART = base.load('mod/common/component_templates/artifact_field_suppression_components.txt')['utility_component_template']


class World:
    def __init__(self):
        self.countries = {key: dict(id=key, techs={TECH, 'tech_artifact_strategic_hull_engineering'},
            species='ARTIFACT_USER', bio=False, modifiers={'acs_hull_qualified': -1},
            resources={'energy': 1500, 'rare_crystals': 25}, hostile=set()) for key in ('A', 'B', 'C')}
        self.countries['B']['hostile'] = {'A'}
        self.systems = {key: dict(id=key, fleets=[]) for key in ('here', 'other')}
        self.fleets = []
        self.actor = self.fleet('A', 'here', SIZE, module=True)
        self.enemy = self.fleet('B', 'here', 'battleship')

    def fleet(self, country, system, size, module=False):
        owner = self.countries[country]
        ship = dict(size=size, components={MODULE} if module else set(),
                    ship_class='shipclass_military', disabled=False, modifiers={})
        fleet = dict(owner=owner, controller=owner, solar_system=self.systems[system],
                     ships=[ship], civilian=False, cloaked=False, disabled=False, native_cooldown=0)
        self.fleets.append(fleet)
        self.systems[system]['fleets'].append(fleet)
        return fleet

    def resolve(self, path, stack):
        parts = path.split('.')
        if parts[0] == 'root':
            obj, parts = stack[0], parts[1:]
        elif parts[0].startswith('prev'):
            n = len(parts[0]) // 4
            assert parts[0] == 'prev' * n and n < len(stack), path
            obj, parts = stack[-1 - n], parts[1:]
        else:
            obj = stack[-1]
        for key in parts:
            obj = obj.get(key) if obj is not None else None
        return obj

    def condition(self, entries, stack):
        return all(self.term(e, stack) for e in entries)

    def term(self, e, stack):
        k, v, obj = e.key, e.value, stack[-1]
        if k in TRIGGERS:
            return self.condition(TRIGGERS[k], stack) == (v == 'yes')
        if k in ('AND', 'custom_tooltip'):
            return self.condition(v, stack)
        if k in ('NOT', 'NOR'):
            return not any(self.term(x, stack) for x in v)
        if k == 'OR':
            return any(self.term(x, stack) for x in v)
        if k in ('fail_text', 'text'):
            return True
        if k == 'exists':
            return self.resolve(v, stack) is not None
        if k in ('owner', 'controller', 'solar_system'):
            target = self.resolve(k, stack)
            return target is not None and self.condition(v, stack + [target])
        if k == 'owner_main_species':
            return self.condition(v, stack)
        if k in ('any_fleet_in_system', 'any_owned_ship'):
            return any(self.condition(v, stack + [item]) for item in obj['fleets' if k == 'any_fleet_in_system' else 'ships'])
        if k == 'is_owned_by':
            return obj['owner'] is self.resolve(v, stack)
        if k == 'is_hostile':
            return self.resolve(v, stack)['id'] in obj['hostile']
        if k in ('has_technology', 'has_modifier', 'has_component'):
            return v in obj[{'has_technology': 'techs', 'has_modifier': 'modifiers', 'has_component': 'components'}[k]]
        if k in ('is_ship_size', 'is_ship_class', 'is_species_class'):
            return obj[{'is_ship_size': 'size', 'is_ship_class': 'ship_class', 'is_species_class': 'species'}[k]] == v
        if k in ('is_civilian', 'is_cloaked', 'is_disabled', 'country_uses_bio_ships'):
            return obj[{'is_civilian': 'civilian', 'is_cloaked': 'cloaked', 'is_disabled': 'disabled', 'country_uses_bio_ships': 'bio'}[k]] == (v == 'yes')
        raise AssertionError(('unknown trigger', k))

    def execute(self, entries, stack):
        obj = stack[-1]
        for e in entries:
            k, v = e.key, e.value
            if k == 'if':
                if self.condition(child(v, 'limit'), stack):
                    self.execute([x for x in v if x.key != 'limit'], stack)
            elif k in ('owner', 'solar_system'):
                self.execute(v, stack + [obj[k]])
            elif k in ('every_fleet_in_system', 'every_owned_ship'):
                for item in obj['fleets' if k == 'every_fleet_in_system' else 'ships']:
                    current = stack + [item]
                    if self.condition(child(v, 'limit'), current):
                        self.execute([x for x in v if x.key != 'limit'], current)
            elif k == 'add_modifier':
                obj['modifiers'][scalar(v, 'modifier')] = int(scalar(v, 'days'))
            else:
                raise AssertionError(('unknown effect', k))

    def activate(self, actor=None):
        actor = self.actor if actor is None else actor
        stack = [actor]
        # 原生行动的外部契约：可见/可用/possible、成本和舰队冷却；不是引擎实现证明。
        if actor['native_cooldown'] or not all(self.condition(child(ACTION, key), stack)
                for key in ('button_visible', 'button_clickable', 'possible')):
            return False
        resources = actor['controller']['resources']
        cost = {e.key: int(e.value) for e in child(ACTION, 'cost')}
        if any(resources.get(k, 0) < amount for k, amount in cost.items()):
            return False
        for k, amount in cost.items():
            resources[k] -= amount
        actor['native_cooldown'] = int(scalar(ACTION, 'cooldown'))
        for event in child(ON_ACTIONS[scalar(ACTION, 'on_completed')], 'events'):
            self.execute(child(EVENTS[event.value], 'immediate'), stack)
        return True

    def elapsed(self, days):
        # 外部日期夹具只递减源码声明的时限，不声称验证原生存档序列化。
        objects = list(self.countries.values())
        for fleet in self.fleets:
            fleet['native_cooldown'] = max(0, fleet['native_cooldown'] - days)
            objects.extend(fleet['ships'])
        for obj in objects:
            obj['modifiers'] = {k: (-1 if n == -1 else n - days)
                for k, n in obj['modifiers'].items() if n == -1 or n > days}


class FieldSuppressionTests(unittest.TestCase):
    def test_local_hostile_military_only_and_one_native_payment(self):
        w = World()
        friend = w.fleet('C', 'here', 'battleship')
        remote = w.fleet('B', 'other', 'battleship')
        civilian = w.fleet('B', 'here', 'science'); civilian['civilian'] = True
        starbase = w.fleet('B', 'here', 'starbase_citadel')
        starbase['ships'][0]['ship_class'] = 'shipclass_starbase'
        cloaked = w.fleet('B', 'here', 'battleship'); cloaked['cloaked'] = True
        disabled = w.fleet('B', 'here', 'battleship'); disabled['ships'][0]['disabled'] = True
        self.assertTrue(w.activate())
        self.assertEqual(w.enemy['ships'][0]['modifiers'], {'afs_suppressed': 60})
        for fleet in (w.actor, friend, remote, civilian, starbase, cloaked, disabled):
            self.assertEqual(fleet['ships'][0]['modifiers'], {})
        self.assertEqual(w.countries['A']['resources'], {'energy': 0, 'rare_crystals': 0})
        self.assertEqual(w.countries['A']['modifiers']['afs_recharging'], 180)

    def test_no_target_insufficient_funds_and_platform_fail_without_payment(self):
        mutations = [lambda w: w.enemy['controller']['hostile'].clear(),
            lambda w: w.countries['A']['resources'].update(energy=1499),
            lambda w: w.countries['A']['resources'].update(rare_crystals=24),
            lambda w: w.actor['ships'][0]['components'].clear(),
            lambda w: w.actor['ships'][0].update(size='destiny_lord'),
            lambda w: w.actor.update(cloaked=True),
            lambda w: w.actor.update(solar_system=None),
            lambda w: w.actor.update(controller=w.countries['C']),
            lambda w: w.countries['A']['techs'].remove(TECH),
            lambda w: w.countries['A']['modifiers'].pop('acs_hull_qualified')]
        for mutate in mutations:
            with self.subTest(case=mutations.index(mutate)):
                w = World(); mutate(w)
                before = deepcopy(w.countries)
                self.assertFalse(w.activate())
                self.assertEqual(w.countries, before)
                self.assertEqual(w.enemy['ships'][0]['modifiers'], {})

    def test_scope_stack_is_independent_of_ui_root_and_component_is_hull_restricted(self):
        w = World()
        # 界面可拥有无关ROOT，PREV链仍必须找到真正发射者。
        self.assertTrue(w.condition(TRIGGERS['artifact_field_suppression_ready'], [{}, w.actor]))
        self.assertEqual(scalar(PART, 'size'), 'aux')
        self.assertEqual([x.value for x in child(PART, 'size_restriction')], [SIZE])
        self.assertEqual([x.value for x in child(PART, 'prerequisites')], [TECH])
        self.assertEqual([x.value for x in child(PART, 'scripted_action')], ['artifact_field_suppression'])
        self.assertEqual([(e.key, e.value) for e in ACTION[:2]], [('user_scope', 'fleet'), ('scope', 'self')])

    def test_shared_cooldown_survives_new_fleet_and_effect_expires_separately(self):
        w = World(); self.assertTrue(w.activate())
        second = w.fleet('A', 'here', SIZE, module=True)
        w.countries['A']['resources'].update(energy=5000, rare_crystals=100)
        self.assertFalse(w.activate(second))
        # 换编队后原生舰队冷却为零，仍受国家记录限制。
        w.elapsed(60)
        self.assertNotIn('afs_suppressed', w.enemy['ships'][0]['modifiers'])
        self.assertFalse(w.activate(second))
        w.elapsed(119); self.assertFalse(w.activate(second))
        w.elapsed(1); self.assertTrue(w.activate(second))
        self.assertEqual(w.countries['A']['resources'], {'energy': 3500, 'rare_crystals': 75})

    def test_existing_hits_not_refreshed_late_arrivals_not_hit_and_departures_keep_timer(self):
        w = World()
        already = w.fleet('B', 'here', 'battleship')
        already['ships'][0]['modifiers']['afs_suppressed'] = 12
        self.assertTrue(w.activate())
        self.assertEqual(already['ships'][0]['modifiers']['afs_suppressed'], 12)
        late = w.fleet('B', 'here', 'battleship')
        self.assertEqual(late['ships'][0]['modifiers'], {})
        w.systems['here']['fleets'].remove(w.enemy)
        w.enemy['solar_system'] = w.systems['other']
        w.systems['other']['fleets'].append(w.enemy)
        # 发射者损失也不删除既有命中；本测试只检查没有源舰持续依赖。
        w.actor['ships'].clear()
        w.elapsed(59)
        self.assertEqual(w.enemy['ships'][0]['modifiers']['afs_suppressed'], 1)
        w.elapsed(1); self.assertEqual(w.enemy['ships'][0]['modifiers'], {})


if __name__ == '__main__':
    unittest.main()
