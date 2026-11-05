"""安装已离线核对的终局旗舰候选，登记来源并消除旧v08公共贴图重名。"""

import csv
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'art/models/aemusa_endgame_runtime_v03'
DEST=ROOT/'mod/gfx/models/aemusa_endgame_v03'


def main():
    manifest=json.loads((SOURCE/'production_manifest.json').read_text(encoding='utf-8'))
    assert manifest['source_reopened'] and manifest['T_locator_count']==16
    assert DEST.resolve().is_relative_to((ROOT/'mod/gfx/models').resolve())
    DEST.mkdir(parents=True,exist_ok=True)
    installed=[]
    for path in (SOURCE/'export').iterdir():
        if path.suffix in ('.mesh','.dds','.gfx','.asset'):
            target=DEST/path.name;shutil.copy2(path,target)
            assert path.read_bytes()==target.read_bytes()
            installed.append(target.relative_to(ROOT).as_posix())
    # 本机此前日志指出v08与公共v04有三张同名DDS；独立改名v08副本，像素字节不改。
    legacy=ROOT/'mod/gfx/models/aemusa_reality_identity_v08'
    gfx=legacy/'_reality_identity_v08_meshes.gfx'
    original=gfx.read_text(encoding='utf-8')
    renamed=[]
    replacements={}
    for suffix in ('diffuse','normal','properties'):
        old='cc_surface_v05_'+suffix+'.dds';new='arfv08_public_'+suffix+'.dds'
        oldpath=legacy/old;newpath=legacy/new
        public=ROOT/'mod/gfx/models/central_court_v04'/old
        if oldpath.is_file():
            assert oldpath.read_bytes()==public.read_bytes(),old
            assert not newpath.exists(),new
            oldpath.rename(newpath)
        assert newpath.is_file() and newpath.read_bytes()==public.read_bytes()
        original=original.replace('"'+old+'"','"'+new+'"')
        replacements[(legacy/old).relative_to(ROOT).as_posix()]=newpath.relative_to(ROOT).as_posix()
        renamed.append({'old':old,'new':new,'content_preserved':True})
    gfx.write_text(original,encoding='utf-8')
    registry=ROOT/'docs/art/ASSET_REGISTRY.csv'
    with registry.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
    rows=[r for r in rows if not r['asset_id'].startswith('ASSET-AEF03-')]
    for r in rows:
        if r['mod_path'] in replacements:
            r['mod_path']=replacements[r['mod_path']]
            if '2026-11-06独立改名' not in r['notes']:
                r['notes']+=' 2026-11-06独立改名v08公共DDS副本以消除运行重名，文件字节保持；未做游戏观察。'
    def entry(key,title,kind,source,target):
        row={f:'' for f in fields}
        row.update(asset_id=key,title=title,asset_type=kind,source_path=source,mod_path=target,
                   origin_method='项目原创v02三维结构与程序化星空，UV烘焙及PDX导出',
                   rights_status='project_generated_source_recorded',redistribution_allowed='pending',
                   art_review_status='draft_integrated_pending_human_review',game_spec_status='static_checked_runtime_pending',
                   original_redraw='false',re_modeled='true',abstract_rules_only='true',
                   authorization_review='user_requested_prelaunch_preparation',
                   notes='2026-11-06；中央星空意象得到肯定，整舰外观仍为候选；仅准备到登录游戏之前，未操作游戏。')
        rows.append(row)
    for part in ('bow','mid','stern'):
        entry('ASSET-AEF03-MESH-'+part.upper(),'终局旗舰'+part+'网格开发候选','ship_model',
              (SOURCE/'endgame_runtime_v03.blend').relative_to(ROOT).as_posix(),(DEST/('aef03_'+part+'.mesh')).relative_to(ROOT).as_posix())
    for family in ('hull','star'):
        for suffix in ('diffuse','normal','properties'):
            name='aef03_'+family+'_'+suffix
            entry('ASSET-AEF03-TEX-'+family.upper()+'-'+suffix.upper(),'终局旗舰'+family+' '+suffix+'贴图候选','model_texture',
                  (SOURCE/'export'/(name+'.png')).relative_to(ROOT).as_posix(),(DEST/(name+'.dds')).relative_to(ROOT).as_posix())
    entry('ASSET-AEF03-ENTITY-PACK','终局旗舰三段显示实体开发候选','entity_pack',
          (SOURCE/'export/_aef03_entities.asset').relative_to(ROOT).as_posix(),(DEST/'_aef03_entities.asset').relative_to(ROOT).as_posix())
    with registry.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    result={'date':'2026-11-06','installed_files':installed,'legacy_dds_renames':renamed,
            'registry_records_added':10,'game_operated':False,'runtime_status':'not_started'}
    (ROOT/'reports/flagship_v03_installation_2026-11-06.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ENDGAME_INSTALLED',len(installed),'files; 10 registry records; 3 legacy DDS names fixed')


if __name__=='__main__':main()
