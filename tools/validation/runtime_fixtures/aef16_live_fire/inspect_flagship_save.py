"""只读核对 4.5.x 文本存档的实装武器、舰船引用和持久化全局设计表。"""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from check_mod import parse, scalar


def block(text, key, indent=""):
    # 存档以制表符标示深度，只截所需记录，再用项目解析器读取嵌套值。
    match = re.search(rf"(?ms)^{indent}{re.escape(key)}=\s*\{{(.*?)^{indent}\}}", text)
    if match is None:
        raise ValueError(f"存档缺少 {key} 区块")
    return match[1]


def records(text):
    return re.finditer(r"(?ms)^\t(\d+)=\s*\{(.*?)^\t\}", text)


def children(entries, key):
    return [e.value for e in entries if e.key == key and isinstance(e.value, list)]


def inspect(path, country_id):
    with ZipFile(path) as archive:
        data = archive.read("gamestate").decode("utf-8")
    country = block(block(data, "country"), str(country_id), "\t")
    owned_fleets = set(re.findall(r"(?m)^\s*fleet=(\d+)$", block(country, "owned_fleets", "\t\t\t")))
    designs = {}
    for record in records(block(data, "ship_design")):
        if 'ship_size="aemusa_reality_flagship"' in record[2]:
            designs[record[1]] = parse(record[2])
    ships = []
    for record in records(block(data, "ships")):
        fleet = re.search(r"(?m)^\t\tfleet=(\d+)$", record[2])
        if not fleet or fleet[1] not in owned_fleets:
            continue
        design_id = re.search(r"(?m)^\t\t\tdesign=(\d+)$", record[2])
        if not design_id or design_id[1] not in designs:
            continue
        ship = parse(record[2])
        design = designs[design_id[1]]
        name, = children(design, "name")
        stages, = children(design, "growth_stages")
        stage, = children(stages, "")
        fitted_sections = {scalar(s,"slot"):s for s in children(stage,"section")}
        weapons = {}
        for section in children(ship, "section"):
            slot = scalar(section, "slot")
            saved = fitted_sections[slot]
            assert scalar(saved,"template") == scalar(section,"design")
            declared = {scalar(c,"slot"):scalar(c,"template") for c in children(saved,"component")
                        if "_GUN_" in scalar(c,"slot")}
            installed = {scalar(w,"component_slot"):scalar(w,"template") for w in children(section,"weapon")}
            assert declared == installed, (slot, declared, installed)
            weapons[slot] = dict(Counter(installed.values()))
        assert set(weapons) == set(fitted_sections) == {"bow","mid","stern"}
        ships.append({"ship_id":int(record[1]), "fleet_id":int(fleet[1]), "design_id":int(design_id[1]),
                      "design_key":scalar(name,"key"), "upgradable":scalar(ship,"upgradable"),
                      "weapons":weapons, "required_components":[e.value for e in stage if e.key=="required_component"]})
    table = parse(block(block(data, "ship_designs"), "global_ship_design", "\t"))
    global_ids = {}
    for item in children(table, ""):
        name, = children(item, "name")
        key = scalar(name, "key")
        if key and key.startswith("NAME_Aemusa_Reality_Flagship"):
            global_ids.setdefault(key, []).append(int(scalar(item,"ship_design")))
    return {"file":path.name, "version":re.search(r'(?m)^version="([^"]+)"',data)[1],
            "date":re.search(r'(?m)^date="([^"]+)"',data)[1], "country":country_id,
            "owned_flagships":ships, "global_design_ids":global_ids}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("save", type=Path, nargs="+")
    parser.add_argument("--country", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps([inspect(p,args.country) for p in args.save], ensure_ascii=False, indent=2))
