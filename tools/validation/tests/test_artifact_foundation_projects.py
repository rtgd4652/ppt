"""执行R1正式脚本检查付费、现场与一次结算；原生对象和回调为外部夹具。

不模拟原生升级、就业、日期或真实存读档。未知条件／效果立即报错。
"""
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from check_mod import parse, scalar

ROOT=Path(__file__).resolve().parents[3]
def load(path):
    text=(ROOT/path).read_text(encoding='utf-8-sig')
    # 检查器解析器不保留比较符；夹具显式保留这两个实际用到的比较。
    text=re.sub(r'\b(value|amount)\s*>=\s*([\w.-]+)',r'\1_ge = \2',text)
    return {e.key:e.value for e in parse(text) if e.key}
TRIGGERS=load('mod/common/scripted_triggers/artifact_foundation_triggers.txt')
EFFECTS=load('mod/common/scripted_effects/artifact_foundation_effects.txt')
DECISIONS=load('mod/common/decisions/artifact_foundation_decisions.txt')
EVENTS={scalar(e.value,'id'):e.value for e in parse((ROOT/'mod/events/artifact_foundation_events.txt').read_text(encoding='utf-8')) if e.key.endswith('_event')}
SPEC=json.loads((ROOT/'docs/design/artifact_civilization_r1_implementation_spec_v0.1.json').read_text(encoding='utf-8'))
TECHS=set(load('mod/common/technology/artifact_public_foundation_technology.txt'))
MODE_SPECS={m['id']:m for m in SPEC['project_modes']}

def child(entries,key,default=None):
    return next((e.value for e in entries if e.key==key),default)

class World:
    def __init__(self):
        self.countries={key:{'kind':'country','id':key,'ai':False,'species':'ARTIFACT_USER','techs':set(TECHS),'resources':{'energy':5000,'minerals':5000,'consumer_goods':5000,'alloys':5000},'vars':{}} for key in ['A','B']}
        self.planets={}
        self.targets={}
        self.last_event=None
        self.add_planet('P')

    def add_planet(self,key,owner='A'):
        self.planets[key]={'kind':'colony','id':key,'owner':owner,'controller':owner,'colony':True,'flags':set(),'vars':{},'modifiers':{},'bombarded':False,'buildings':{'building_artifact_sample_repository','building_artifact_standard_parts_workshop'}}
        return self.planets[key]

    def ref(self,obj):
        return (obj['kind'],obj['id'])

    def deref(self,ref):
        if ref is None:return None
        return (self.countries if ref[0]=='country' else self.planets).get(ref[1])

    def target_key(self,name,obj,prev):
        if '@' not in name:return name
        stem,scope=name.split('@',1)
        target=obj if scope=='this' else prev if scope=='prev' else None
        if target is None:raise AssertionError(('unknown dynamic scope',scope))
        return f'{stem}@{target["id"]}'

    def resolve(self,name,obj,ctx,prev=None):
        if name=='owner':return self.countries.get(obj.get('owner'))
        if name.startswith('event_target:'):
            key=name[len('event_target:'):]
            if '@' in key:return self.deref(self.targets.get(self.target_key(key,obj,prev)))
            return self.deref(ctx.get(key))
        raise AssertionError(('unknown object',name))

    def number(self,value,obj):
        try:return float(value)
        except (ValueError,TypeError):return obj['vars'][value]

    def condition(self,entries,obj,ctx,prev=None):
        return all(self.term(e,obj,ctx,prev) for e in entries)

    def term(self,e,obj,ctx,prev):
        k,v=e.key,e.value
        if k in TRIGGERS:return self.condition(TRIGGERS[k],obj,ctx,prev)==(v=='yes')
        if k in ('AND','limit','potential'):return self.condition(v,obj,ctx,prev)
        if k=='OR':return any(self.term(x,obj,ctx,prev) for x in v)
        if k in ('NOR','NOT'):return not any(self.term(x,obj,ctx,prev) for x in v)
        if k in ('fail_text','text'):return True
        if k=='custom_tooltip':return self.condition(v,obj,ctx,prev)
        if k=='owner_main_species':return self.condition(v,obj,ctx,prev)
        if k=='owner':
            owner=self.resolve('owner',obj,ctx,prev)
            return owner is not None and self.condition(v,owner,ctx,obj)
        if k=='any_owned_colony':return any(self.condition(v,p,ctx,obj) for p in self.planets.values() if p['owner']==obj['id'])
        if k=='exists':return self.resolve(v,obj,ctx,prev) is not None
        if k=='carrier_is_type':return v=='planet' and obj['kind']=='colony'
        if k=='is_colony':return obj.get('colony',False)==(v=='yes')
        if k=='is_ai':return obj['ai']==(v=='yes')
        if k=='is_species_class':return obj['species']==v
        if k=='has_technology':return v in obj['techs']
        if k=='has_resource':return obj['resources'][scalar(v,'type')]>=self.number(scalar(v,'amount_ge'),obj)
        if k=='has_building':return v in obj['buildings']
        if k=='has_carrier_flag':return v in obj['flags']
        if k=='has_modifier':return v in obj['modifiers']
        if k=='has_orbital_bombardment':return obj['bombarded']==(v=='yes')
        if k in ('is_owned_by','is_controlled_by'):
            target=self.resolve(v,obj,ctx,prev)
            return target is not None and obj['owner' if k=='is_owned_by' else 'controller']==target['id']
        if k=='check_variable':return obj['vars'].get(scalar(v,'which'),0)>=self.number(scalar(v,'value_ge'),obj)
        raise AssertionError(('unknown trigger',k))

    def execute(self,entries,obj,ctx,prev=None):
        taken=None
        for e in entries:
            k,v=e.key,e.value
            if k in ('if','else_if','else'):
                if k=='if':taken=False
                if not taken and (k=='else' or self.condition(child(v,'limit'),obj,ctx,prev)):
                    taken=True
                    self.execute([x for x in v if x.key!='limit'],obj,ctx,prev)
                continue
            taken=None
            if k in EFFECTS:self.execute(EFFECTS[k],obj,ctx,prev)
            elif k in ('hidden_effect','effect'):self.execute(v,obj,ctx,prev)
            elif k=='custom_tooltip':continue
            elif k=='owner':self.execute(v,self.resolve('owner',obj,ctx,prev),ctx,obj)
            elif k=='every_owned_colony':
                for p in list(self.planets.values()):
                    if p['owner']==obj['id'] and self.condition(child(v,'limit'),p,ctx,obj):
                        self.execute([x for x in v if x.key!='limit'],p,ctx,obj)
            elif k=='save_event_target_as':ctx[v]=self.ref(obj)
            elif k=='save_global_event_target_as':self.targets[self.target_key(v,obj,prev)]=self.ref(obj)
            elif k=='clear_global_event_target':self.targets.pop(self.target_key(v,obj,prev),None)
            elif k=='set_carrier_flag':obj['flags'].add(v)
            elif k=='remove_carrier_flag':obj['flags'].discard(v)
            elif k=='clear_variable':obj['vars'].pop(v,None)
            elif k in ('set_variable','change_variable'):
                key=scalar(v,'which'); value=self.number(scalar(v,'value'),obj)
                obj['vars'][key]=value+(obj['vars'].get(key,0) if k=='change_variable' else 0)
            elif k=='add_resource':
                for resource in v:obj['resources'][resource.key]+=float(resource.value)
            elif k=='remove_modifier':obj['modifiers'].pop(v,None)
            elif k=='add_modifier':obj['modifiers'][scalar(v,'modifier')]=int(scalar(v,'days'))
            elif k=='carrier_event':self.dispatch(scalar(v,'id'),obj,ctx)
            else:raise AssertionError(('unknown effect',k))

    def dispatch(self,event,obj,ctx=None):
        ctx={} if ctx is None else ctx
        fields=EVENTS[event]
        if not self.condition(child(fields,'trigger',[]),obj,ctx):return False
        self.last_event=event
        self.execute(child(fields,'immediate',[]),obj,ctx)
        return True

    def open(self,kind,planet='P'):
        obj=self.planets[planet];ctx={}
        fields=DECISIONS['decision_artifact_foundation_'+kind]
        if not self.condition(child(fields,'potential'),obj,ctx):return None
        self.execute(child(fields,'effect'),obj,ctx)
        return ctx

    def choose(self,mode,planet='P',ctx=None):
        ctx=self.open('sample' if mode=='sample_analysis' else 'workshop',planet) if ctx is None else ctx
        event=10 if mode=='sample_analysis' else 20
        options=[e.value for e in EVENTS[f'artifact_foundation.{event}'] if e.key=='option']
        option=next(o for o in options if scalar(o,'name')=='artifact_foundation.start_'+mode)
        if ctx is None or not self.condition(child(option,'allow'),self.planets[planet],ctx):return False
        self.execute(child(option,'hidden_effect'),self.planets[planet],ctx)
        return True

    def monthly(self,owner='A'):
        self.dispatch('artifact_foundation.1',self.countries[owner])

    def elapsed(self,days):
        for p in self.planets.values():
            p['modifiers']={key:left-days for key,left in p['modifiers'].items() if left>days}

class FoundationProjectTests(unittest.TestCase):
    def test_four_paid_modes_complete_once_and_block_refresh(self):
        for mode,spec in MODE_SPECS.items():
            with self.subTest(mode=mode):
                w=World();before=deepcopy(w.countries['A']['resources'])
                self.assertTrue(w.choose(mode))
                expected={k:v-spec['cost'].get(k,0) for k,v in before.items()}
                self.assertEqual(w.countries['A']['resources'],expected)
                for _ in range(spec['monthly_steps']):w.monthly()
                p=w.planets['P'];mod='artifact_foundation_'+mode
                self.assertEqual(p['modifiers'],{mod:720})
                w.elapsed(1)
                w.execute(EFFECTS['artifact_foundation_complete'],p,{})
                self.assertEqual(p['modifiers'][mod],719)
                self.assertFalse(w.choose(mode))
                self.assertEqual(w.countries['A']['resources'],expected)

    def test_duplicate_window_selection_does_not_charge_or_advance(self):
        w=World();ctx=w.open('workshop');w.choose('materials_study',ctx=ctx)
        before=deepcopy(w.countries['A']['resources'])
        self.assertFalse(w.choose('materials_study',ctx=ctx))
        for _ in range(3):w.open('workshop')
        self.assertEqual(w.planets['P']['vars']['arf_r1_progress'],0)
        self.assertEqual(w.countries['A']['resources'],before)

    def test_control_bombardment_and_missing_site_pause_without_refund(self):
        for condition in ('controller','bombarded','buildings'):
            with self.subTest(condition=condition):
                w=World();w.choose('materials_study');w.monthly();p=w.planets['P']
                saved=deepcopy(w.countries['A']['resources']);old=deepcopy(p[condition])
                p[condition]={'controller':'B','bombarded':True,'buildings':set()}[condition]
                w.monthly();self.assertEqual(p['vars']['arf_r1_progress'],1)
                self.assertEqual(w.countries['A']['resources'],saved)
                p[condition]=old;w.monthly();w.monthly()
                self.assertIn('artifact_foundation_materials_study',p['modifiers'])

    def test_upgrade_to_existing_workshop_keeps_site_valid(self):
        w=World();w.choose('basic_construction');p=w.planets['P']
        p['buildings']={'building_artifact_relic_workshop'}
        for _ in range(4):w.monthly()
        self.assertIn('artifact_foundation_basic_construction',p['modifiers'])

    def test_transfer_aborts_and_stale_window_cannot_charge_new_owner(self):
        w=World();ctx=w.open('workshop');w.choose('materials_study',ctx=ctx);w.monthly()
        p=w.planets['P'];p['owner']=p['controller']='B'
        before=deepcopy(w.countries['B']['resources'])
        w.dispatch('artifact_foundation.2',p)
        self.assertNotIn('arf_r1_active',p['flags'])
        self.assertEqual(p['vars']['arf_r1_last_progress'],1)
        self.assertFalse(w.choose('materials_study',ctx=ctx))
        self.assertEqual(w.countries['B']['resources'],before)
        self.assertEqual(w.targets,{})
        self.assertTrue(w.choose('materials_study'))

    def test_two_sites_keep_separate_original_owner_targets(self):
        w=World();w.add_planet('Q');w.choose('materials_study','P');w.choose('sample_analysis','Q')
        self.assertEqual(set(w.targets),{'arf_r1_owner@P','arf_r1_owner@Q'})
        w.planets['P']['owner']=w.planets['P']['controller']='B'
        w.dispatch('artifact_foundation.2',w.planets['P'])
        w.monthly()
        self.assertNotIn('arf_r1_active',w.planets['P']['flags'])
        self.assertEqual(w.planets['Q']['vars']['arf_r1_progress'],1)

    def test_no_tech_no_site_or_insufficient_resources_never_charge(self):
        for reason in ('tech','site','resource'):
            with self.subTest(reason=reason):
                w=World()
                if reason=='tech':w.countries['A']['techs'].discard('tech_artifact_resonance_material_screening')
                if reason=='site':w.planets['P']['buildings']=set()
                if reason=='resource':w.countries['A']['resources']['energy']=199
                before=deepcopy(w.countries['A']['resources'])
                self.assertFalse(w.choose('materials_study'))
                self.assertEqual(w.countries['A']['resources'],before)

    def test_benefit_expires_and_new_project_pays_again(self):
        w=World();w.choose('sample_analysis')
        for _ in range(3):w.monthly()
        self.assertFalse(w.choose('materials_study'))
        w.elapsed(720)
        self.assertTrue(w.choose('materials_study'))
        self.assertEqual(w.planets['P']['vars']['arf_r1_progress'],0)
        self.assertEqual(w.planets['P']['modifiers'],{})

    def test_colony_destruction_cleans_before_owner_is_cleared(self):
        w=World();w.choose('materials_study');p=w.planets['P']
        self.assertEqual(p['owner'],'A')
        w.dispatch('artifact_foundation.3',p)
        self.assertNotIn('arf_r1_managed',p['flags'])
        self.assertEqual(w.targets,{})

    def test_completed_benefit_does_not_transfer(self):
        w=World();w.choose('sample_analysis')
        for _ in range(3):w.monthly()
        p=w.planets['P'];p['owner']=p['controller']='B'
        w.dispatch('artifact_foundation.2',p)
        self.assertEqual(p['modifiers'],{})

    def test_new_owner_monthly_guard_catches_missing_transfer_callback(self):
        w=World();w.choose('materials_study');p=w.planets['P'];p['owner']=p['controller']='B'
        w.monthly('B')
        self.assertNotIn('arf_r1_active',p['flags'])
        self.assertEqual(p['modifiers'],{})

    def test_explicit_abort_keeps_cost_and_requires_new_payment(self):
        w=World();w.choose('basic_construction');before=deepcopy(w.countries['A']['resources'])
        ctx=w.open('workshop');option=next(e.value for e in EVENTS['artifact_foundation.30'] if e.key=='option' and scalar(e.value,'name')=='artifact_foundation.abort')
        w.execute(child(option,'hidden_effect'),w.planets['P'],ctx)
        self.assertEqual(w.countries['A']['resources'],before)
        self.assertTrue(w.choose('basic_construction'))
        self.assertEqual(w.countries['A']['resources']['minerals'],before['minerals']-300)

if __name__=='__main__':unittest.main()
