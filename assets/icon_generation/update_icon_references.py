from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def set_top_block_field(path: Path, key: str, field: str, value: str) -> None:
    """按顶层对象 key 修改字段，避免误改同文件中的其他对象。"""
    text = read(path)
    pattern = re.compile(rf"(?ms)(^{re.escape(key)}\s*=\s*\{{.*?^\s*{re.escape(field)}\s*=\s*)([^\r\n]+)")
    new, count = pattern.subn(rf"\g<1>{value}", text, count=1)
    if count == 0:
        print(f"NO_MATCH top {field} {key} in {path.relative_to(ROOT)}")
    write(path, new)


def set_top_block_icon(path: Path, key: str, icon_value: str) -> None:
    """按顶层对象 key 修改第一条 icon。"""
    set_top_block_field(path, key, "icon", icon_value)


def set_top_block_overlay(path: Path, key: str, overlay_value: str) -> None:
    """按顶层对象 key 修改区划覆盖图标。"""
    set_top_block_field(path, key, "overlay_icon", overlay_value)


def set_keyed_block_icon(path: Path, key: str, icon_value: str) -> None:
    """按 component key 修改对应部件或部件组的第一条 icon。"""
    text = read(path)
    pattern = re.compile(rf"(?ms)(key\s*=\s*\"{re.escape(key)}\".*?^\s*icon\s*=\s*)([^\r\n]+)")
    new, count = pattern.subn(rf"\g<1>{icon_value}", text, count=1)
    if count == 0:
        print(f"NO_MATCH keyed {key} in {path.relative_to(ROOT)}")
    write(path, new)


def main() -> None:
    tech = ROOT / "common/technology/aemusa_technology.txt"
    for key in [
        "tech_artifact_tarot_calculation",
        "tech_artifact_black_gate_observation",
        "tech_artifact_relic_fabrication",
        "tech_artifact_central_court_protocols",
        "tech_artifact_tarot_economy",
        "tech_artifact_resonance_manufacturing",
        "tech_artifact_seven_day_logistics",
        "tech_artifact_destiny_economy",
        "tech_artifact_phase_energy",
        "tech_artifact_phase_extraction",
        "tech_artifact_crossing_trade",
        "tech_artifact_civic_industry",
        "tech_artifact_rare_resonance",
        "tech_artifact_covenant_administration",
        "tech_artifact_relic_archive_restoration",
        "tech_artifact_destiny_city_project",
        "tech_artifact_fate_observatory",
        "tech_artifact_destiny_lord",
        "tech_artifact_user_combat_doctrine",
        "tech_artifact_user_resonance_armaments",
        "tech_artifact_user_apotheosis_warfare",
    ]:
        set_top_block_icon(tech, key, key)

    buildings = ROOT / "common/buildings/aemusa_buildings.txt"
    for key in [
        "building_artifact_sanctum",
        "building_artifact_black_gate_observatory",
        "building_artifact_relic_workshop",
        "building_artifact_seven_day_command",
        "building_artifact_fate_calculus_institute",
        "building_artifact_destiny_research_spire",
        "building_artifact_resonance_alloy_forge",
        "building_artifact_civic_goods_manufactory",
        "building_artifact_phase_reactor",
        "building_artifact_crossing_trade_tower",
        "building_artifact_phase_mine",
        "building_artifact_rare_resonance_refinery",
        "building_artifact_memory_palace",
        "building_artifact_covenant_chamber",
        "building_artifact_relic_archive",
    ]:
        set_top_block_icon(buildings, key, key)

    districts = ROOT / "common/districts/aemusa_districts.txt"
    for key in [
        "district_artifact_nexus",
        "district_artifact_destiny_commons",
        "district_artifact_destiny_industry",
        "district_artifact_destiny_foundation",
        "district_artifact_destiny_research",
        "district_artifact_destiny_fleet",
    ]:
        set_top_block_icon(districts, key, key)
    for key, overlay in {
        "district_artifact_nexus": "GFX_district_artifact_destiny_research",
        "district_artifact_destiny_commons": "GFX_district_artifact_destiny_commons",
        "district_artifact_destiny_industry": "GFX_district_artifact_destiny_industry",
        "district_artifact_destiny_foundation": "GFX_district_artifact_destiny_foundation",
        "district_artifact_destiny_research": "GFX_district_artifact_destiny_research",
        "district_artifact_destiny_fleet": "GFX_district_artifact_destiny_fleet",
    }.items():
        set_top_block_overlay(districts, key, overlay)

    armies = ROOT / "common/armies/aemusa_artifact_armies.txt"
    set_top_block_icon(armies, "artifact_user_guardian_army", "GFX_army_type_artifact_user_guardian")
    set_top_block_icon(armies, "artifact_user_resonance_army", "GFX_army_type_artifact_user_resonance")
    set_top_block_icon(armies, "artifact_user_apotheosis_army", "GFX_army_type_artifact_user_apotheosis")

    set_top_block_icon(
        ROOT / "common/governments/civics/aemusa_origins.txt",
        "origin_artifact_resonance",
        '"gfx/interface/icons/origins/origin_artifact_resonance.dds"',
    )
    set_top_block_icon(
        ROOT / "common/decisions/aemusa_destiny_city_decisions.txt",
        "decision_artifact_destiny_city_project",
        "decision_artifact_destiny_city_project",
    )

    edicts = ROOT / "common/edicts/00_simple_leader_edict.txt"
    set_top_block_icon(edicts, "edict_summon_stellar_administrator", '"GFX_edict_summon_aemusa" # 使用爱缪莎召唤专属图标。')
    set_top_block_icon(edicts, "edict_contact_aemusa", '"GFX_edict_contact_aemusa" # 使用爱缪莎通讯专属图标。')

    base_sets = ROOT / "common/component_sets/aemusa_component_sets.txt"
    for key, icon in {
        "ARTIFACT_TAROT_RAY": "GFX_ship_part_artifact_tarot_ray",
        "ARTIFACT_FATE_ARMOR": "GFX_ship_part_artifact_fate_armor",
        "ARTIFACT_SEVEN_DAY_CORE": "GFX_ship_part_artifact_seven_day_core",
        "ARTIFACT_TAROT_JUDGEMENT": "GFX_ship_part_artifact_tarot_judgement",
        "ARTIFACT_FATE_DOMINION": "GFX_ship_part_artifact_fate_dominion",
    }.items():
        set_keyed_block_icon(base_sets, key, f'"{icon}"')

    tier_sets = ROOT / "common/component_sets/aemusa_tiered_component_sets.txt"
    for key, icon in {
        "ARTIFACT_FATE_RAY_1": "GFX_ship_part_artifact_fate_ray_1",
        "ARTIFACT_FATE_RAY_2": "GFX_ship_part_artifact_fate_ray_2",
        "ARTIFACT_FATE_RAY_3": "GFX_ship_part_artifact_fate_ray_3",
        "ARTIFACT_BLACK_GATE_SHIELD_1": "GFX_ship_part_artifact_black_gate_shield_1",
        "ARTIFACT_BLACK_GATE_SHIELD_2": "GFX_ship_part_artifact_black_gate_shield_2",
        "ARTIFACT_BLACK_GATE_SHIELD_3": "GFX_ship_part_artifact_black_gate_shield_3",
        "ARTIFACT_DESTINY_ARMOR_1": "GFX_ship_part_artifact_destiny_armor_1",
        "ARTIFACT_DESTINY_ARMOR_2": "GFX_ship_part_artifact_destiny_armor_2",
        "ARTIFACT_DESTINY_ARMOR_3": "GFX_ship_part_artifact_destiny_armor_3",
        "ARTIFACT_TACTICAL_CORE_1": "GFX_ship_part_artifact_tactical_core_1",
        "ARTIFACT_TACTICAL_CORE_2": "GFX_ship_part_artifact_tactical_core_2",
        "ARTIFACT_TACTICAL_CORE_3": "GFX_ship_part_artifact_tactical_core_3",
    }.items():
        set_keyed_block_icon(tier_sets, key, f'"{icon}"')

    base_component_icons = {
        "SMALL_ARTIFACT_TAROT_RAY": "GFX_ship_part_artifact_tarot_ray",
        "MEDIUM_ARTIFACT_TAROT_RAY": "GFX_ship_part_artifact_tarot_ray",
        "LARGE_ARTIFACT_TAROT_RAY": "GFX_ship_part_artifact_tarot_ray",
        "SMALL_ARTIFACT_FATE_ARMOR": "GFX_ship_part_artifact_fate_armor",
        "MEDIUM_ARTIFACT_FATE_ARMOR": "GFX_ship_part_artifact_fate_armor",
        "LARGE_ARTIFACT_FATE_ARMOR": "GFX_ship_part_artifact_fate_armor",
        "ARTIFACT_SEVEN_DAY_CORE": "GFX_ship_part_artifact_seven_day_core",
        "ARTIFACT_DESTINY_LORD_REACTOR": "GFX_ship_part_artifact_destiny_lord_reactor",
        "ARTIFACT_DESTINY_LORD_SENSOR": "GFX_ship_part_artifact_destiny_lord_sensor",
        "ARTIFACT_DESTINY_LORD_DRIVE": "GFX_ship_part_artifact_destiny_lord_drive",
        "ARTIFACT_DESTINY_LORD_THRUSTER": "GFX_ship_part_artifact_destiny_lord_thruster",
        "ARTIFACT_DESTINY_LORD_COMPUTER": "GFX_ship_part_artifact_destiny_lord_computer",
        "ARTIFACT_AURA_GUARDIAN_MATRIX": "GFX_ship_part_artifact_aura_guardian_matrix",
        "ARTIFACT_AURA_BLACK_GATE_SUPPRESSION": "GFX_ship_part_artifact_aura_black_gate_suppression",
        "EXTRA_LARGE_ARTIFACT_TAROT_JUDGEMENT": "GFX_ship_part_artifact_tarot_judgement",
        "TITANIC_ARTIFACT_FATE_DOMINION": "GFX_ship_part_artifact_fate_dominion",
    }
    for key, icon in base_component_icons.items():
        set_keyed_block_icon(ROOT / "common/component_templates/aemusa_artifact_components.txt", key, f'"{icon}"')

    tier_component_icons = {
        "ARTIFACT_TACTICAL_CORE_1": "GFX_ship_part_artifact_tactical_core_1",
        "ARTIFACT_TACTICAL_CORE_2": "GFX_ship_part_artifact_tactical_core_2",
        "ARTIFACT_TACTICAL_CORE_3": "GFX_ship_part_artifact_tactical_core_3",
        "ARTIFACT_COMBAT_COMPUTER_1": "GFX_ship_part_artifact_combat_computer_1",
        "ARTIFACT_COMBAT_COMPUTER_2": "GFX_ship_part_artifact_combat_computer_2",
        "ARTIFACT_COMBAT_COMPUTER_3": "GFX_ship_part_artifact_combat_computer_3",
        "ARTIFACT_SENSOR_1": "GFX_ship_part_artifact_sensor_1",
        "ARTIFACT_SENSOR_2": "GFX_ship_part_artifact_sensor_2",
        "ARTIFACT_SENSOR_3": "GFX_ship_part_artifact_sensor_3",
    }
    for tier in ["1", "2", "3"]:
        for size in ["SMALL", "MEDIUM", "LARGE"]:
            tier_component_icons[f"{size}_ARTIFACT_FATE_RAY_{tier}"] = f"GFX_ship_part_artifact_fate_ray_{tier}"
            tier_component_icons[f"{size}_ARTIFACT_BLACK_GATE_SHIELD_{tier}"] = f"GFX_ship_part_artifact_black_gate_shield_{tier}"
            tier_component_icons[f"{size}_ARTIFACT_DESTINY_ARMOR_{tier}"] = f"GFX_ship_part_artifact_destiny_armor_{tier}"
    for key, icon in tier_component_icons.items():
        set_keyed_block_icon(ROOT / "common/component_templates/aemusa_artifact_tiered_components.txt", key, f'"{icon}"')


if __name__ == "__main__":
    main()
