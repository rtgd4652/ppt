"""输出可计数的16T方案示意和数据，不写入游戏配置或生成船模。"""

from html import escape
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art/concepts/aemusa_flagship_redesign_20261104'


def main():
    # 坐标仅为相对布置，不是米制、PDX坐标或正式模型尺寸。
    banks=(
        ('A','上层左舷',(-50,-42,-34,-26),22,12),
        ('B','上层右舷',(26,34,42,50),22,12),
        ('C','下层左舷',(-66,-58,-50,-42),54,-8),
        ('D','下层右舷',(42,50,58,66),54,-8),
    )
    slots=[]
    for bank,label,xs,y,z in banks:
        for x in xs:
            index=len(slots)+1
            slots.append({'id':f'T{index:02d}','bank':bank,'bank_label':label,
                'slot_name_proposal':f'TITANIC_{index:02d}',
                'template_reference':'invisible_titanic_fixed','size':'titanic',
                'locator_name_proposal':f'xl_gun_{index:02d}',
                'schematic_position':[x,y,z],'schematic_forward':[0,1,0]})
    assert len(slots)==16 and len({s['id'] for s in slots})==16
    assert len({s['locator_name_proposal'] for s in slots})==16
    assert all(sum(s['bank']==b[0] for s in slots)==4 for b in banks)
    data={'date':'2026-11-04','status':'draft_pending_human_review',
        'requirement':'at least 16 true T slots','proposed_count':16,'implemented_in_mod':False,
        'coordinates':'relative schematic only; +Y forward; not authoring or PDX units',
        'native_evidence':[
            'common/section_templates/titan.txt: TITANIC_01 -> invisible_titanic_fixed -> xl_gun_01',
            'common/component_slot_templates/00_component_slots_fixed.txt: size=titanic; component=weapon; is_fixed=yes',
            'common/component_templates/00_weapons_extra_large.txt: PERDITION_BEAM_TITAN; size=titanic; ship_uses_titan_components=yes',
            'common/scripted_triggers/07_scripted_triggers_ships.txt: native allow-list excludes aemusa_reality_flagship'],
        'implementation_followup':'use a mod-owned true titanic weapon allowed for the independent flagship; do not globally override vanilla ship eligibility',
        'visual_banks':'four structural groups; each contains four independent component slots and emission locators',
        'fire_control':'bank grouping does not promise separate command UI or synchronized volleys',
        'slots':slots}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'layout_16t_v01.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    sx=lambda x:550+x*5.7
    sy=lambda y:530-y*4.1
    def points(pairs):return ' '.join(f'{sx(x):.1f},{sy(y):.1f}' for x,y in pairs)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1000" viewBox="0 0 1600 1000">',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#69c1cc"/></marker></defs>',
        '<rect width="1600" height="1000" fill="#111b23"/>',
        '<g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif">',
        '<text x="60" y="57" font-size="32" fill="#e0e6e9">私人旗舰重设｜16T布置草案</text>',
        '<text x="60" y="91" font-size="17" fill="#a8b5c0">4组 × 4个独立T槽 · 平面结构示意 · 非模型尺寸／非游戏实现</text>',
        '<line x1="1095" y1="130" x2="1095" y2="917" stroke="#304651" stroke-width="2"/>']
    # 舰体和路径仅解释主结构关系；不将示意轮廓伪装成生成图的精确投影。
    hull=[(-16,82),(-32,68),(-70,65),(-76,45),(-75,-18),(-53,-71),
          (53,-71),(75,-18),(76,45),(70,65),(32,68),(16,82)]
    svg += [f'<polygon points="{points(hull)}" fill="#182630" stroke="#738995" stroke-width="3"/>']
    for side in (-1,1):
        for route in ([(side*8,-65),(side*21,-37),(side*31,-7),(side*23,48),(0,78)],
                      [(side*18,-65),(side*57,-30),(side*63,21),(side*40,58),(0,78)]):
            svg += [f'<polyline points="{points(route)}" fill="none" stroke="#38505e" stroke-width="30" stroke-linejoin="round"/>',
                    f'<polyline points="{points(route)}" fill="none" stroke="#8b5771" stroke-width="3" stroke-linejoin="round"/>']
    for y in (-39,-15,9,33):
        svg += [f'<polygon points="{points([(-12,y-5),(10,y-3),(12,y+5),(-10,y+3)])}" fill="#443448" stroke="#a87891" stroke-width="1.5"/>']
    svg += [f'<rect x="{sx(-38)}" y="{sy(-55)}" width="{76*5.7}" height="{16*4.1}" rx="7" fill="#304651" stroke="#9ba8ae"/>',
            f'<text x="550" y="{sy(-63)+7}" text-anchor="middle" fill="#d6d9d5" font-size="21">推进／供能／散热区</text>',
            '<text x="550" y="158" fill="#d6d9d5" font-size="21" text-anchor="middle">舰首 · 统一前向</text>',
            '<path d="M550 197 L550 173" stroke="#69c1cc" stroke-width="3" marker-end="url(#arrow)"/>']
    for bank,label,xs,y,z in banks:
        x0=sx(min(xs))-23; y0=sy(y)-26
        width=(max(xs)-min(xs))*5.7+46
        color='#69c1cc' if z>0 else '#d39a55'
        label_y=y0-65 if z<0 else y0+87
        svg += [f'<rect x="{x0-10}" y="{y0-13}" width="{width+20}" height="75" rx="7" fill="#14232d" stroke="{color}" stroke-width="2"/>',
                f'<text x="{x0+width/2}" y="{label_y}" font-size="17" fill="{color}" text-anchor="middle">{bank} · {label} · 4T</text>']
        for s in (s for s in slots if s['bank']==bank):
            x=sx(s['schematic_position'][0]); cy=sy(y)
            svg += [f'<g id="slot-{s["id"]}" data-size="titanic" data-bank="{bank}">',
                f'<rect x="{x-20}" y="{cy-20}" width="40" height="40" rx="4" fill="#2d444f" stroke="{color}" stroke-width="2"/>',
                f'<text x="{x}" y="{cy+6}" font-size="16" fill="#f2f5f6" text-anchor="middle">{s["id"]}</text>',
                f'<path d="M{x} {cy-45} L{x} {cy-68}" stroke="#69c1cc" stroke-width="2" marker-end="url(#arrow)"/>','</g>']
    notes=[('硬性要求','#69c1cc'),('至少16个真正的T槽','#e0e6e9'),('图中T01—T16均为独立位置。','#a8b5c0'),
        ('当前草案','#69c1cc'),('A／B：上层火力组','#e0e6e9'),('C／D：前置下层火力组','#e0e6e9'),('上下错层，为前向发射留空间。','#a8b5c0'),
        ('整舰组织','#69c1cc'),('主脊分岔 → 保留空腔 → 汇合','#e0e6e9'),('命运接口进入舰体主结构。','#a8b5c0'),('每组后方配供能、火控和维护体量。','#a8b5c0'),
        ('实际实现待做','#d39a55'),('原生规格：size = titanic','#e0e6e9'),('独立舰种还需可用的T级武器组件。','#a8b5c0'),('当前游戏仍使用旧六L技术样品。','#a8b5c0')]
    y=177
    for line,color in notes:
        heading=line in ('硬性要求','当前草案','整舰组织','实际实现待做')
        if heading and y>177:y+=25
        svg += [f'<text x="1130" y="{y}" fill="{color}" font-size="{22 if heading else 18}">{escape(line)}</text>']
        y+=34
    svg += ['<text x="60" y="944" fill="#a8b5c0" font-size="17">正式外观、分段数量、武器种类与数值待收敛；当前坐标仅供方案讨论。2D投影不证明3D射界或无遮挡。</text>',
            '<text x="60" y="973" fill="#70828f" font-size="15">2026-11-04 · 方案v01 · 世界观与美术依据见同目录README与docs/art/ships/AEMUSA_FLAGSHIP_REDESIGN_v0.1.md</text>',
            '</g></svg>']
    text='\n'.join(svg)+'\n'
    parsed=ET.fromstring(text)
    assert len([n for n in parsed.iter() if n.attrib.get('id','').startswith('slot-')])==16
    (OUT/'layout_16t_v01.svg').write_text(text,encoding='utf-8')
    print('FLAGSHIP_LAYOUT_SAVED 16 unique true-T positions, four banks; no game files changed')


if __name__=='__main__':main()
