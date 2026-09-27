#!/usr/bin/env python3
"""正式 Mod 的只读静态检查；不替代 Stellaris 运行时和人工验收。"""

import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys


SCRIPT_EXTENSIONS = {".txt", ".gfx", ".asset", ".gui", ".mod"}
OWNED = re.compile(r"aemusa|artifact|destiny_lord|white_night", re.I)
STATE = re.compile(r"aemusa_ms_(?:country|leader|truth|decision)_\w+\Z")
EVENT_ID = re.compile(r"([A-Za-z_]\w*)\.\d+\Z")


@dataclass
class Entry:
    key: str
    value: object
    line: int


def tokenize(text):
    """字符串与注释中的括号不参与结构检查；保留源行号。"""
    tokens = []
    i, line = 0, 1
    while i < len(text):
        char = text[i]
        if char.isspace():
            line += char == "\n"
            i += 1
        elif char == "#":
            end = text.find("\n", i)
            i = len(text) if end == -1 else end
        elif char == '"':
            start, start_line = i, line
            i += 1
            while i < len(text):
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                line += text[i] == "\n"
                i += 1
            if i >= len(text):
                raise ValueError(f"第 {start_line} 行字符串未闭合")
            tokens.append((text[start + 1:i], start_line, True))
            i += 1
        elif char in "{}=<>!":
            value = text[i:i + 2] if text[i:i + 2] in {">=", "<=", "!="} else char
            tokens.append((value, line, False))
            i += len(value)
        else:
            start = i
            while i < len(text) and not text[i].isspace() and text[i] not in '{}=<>!#"':
                i += 1
            tokens.append((text[start:i], line, False))
    return tokens


def parse(text):
    tokens, position = tokenize(text), 0

    def block(nested=False):
        nonlocal position
        entries = []
        while position < len(tokens):
            value, line, quoted = tokens[position]
            if value == "}" and not quoted:
                if not nested:
                    raise ValueError(f"第 {line} 行存在多余右括号")
                position += 1
                return entries
            if value == "{" and not quoted:
                position += 1
                entries.append(Entry("", block(True), line))
                continue
            if not quoted and value in {"=", ">", "<", "!=", ">=", "<="}:
                raise ValueError(f"第 {line} 行出现意外标记 {value}")
            position += 1
            if position < len(tokens) and not tokens[position][2] and tokens[position][0] in {"=", ">", "<", "!=", ">=", "<="}:
                position += 1
                if position >= len(tokens):
                    raise ValueError(f"第 {line} 行赋值缺少值")
                item, _, is_string = tokens[position]
                position += 1
                if item == "{" and not is_string:
                    item = block(True)
                elif not is_string and item in {"}", "=", ">", "<", "!=", ">=", "<="}:
                    raise ValueError(f"第 {line} 行赋值缺少有效值")
                entries.append(Entry(value, item, line))
            else:
                entries.append(Entry("", value, line))
        if nested:
            raise ValueError("块缺少右括号")
        return entries

    return block()


def walk(entries, parents=()):
    for entry in entries:
        yield entry, parents
        if isinstance(entry.value, list):
            yield from walk(entry.value, parents + (entry.key,))


def scalar(entries, key):
    return next((e.value for e in entries if e.key == key and isinstance(e.value, str)), None)


def check(root, game_dir=None):
    root = Path(root).resolve()
    game_dir = Path(game_dir).resolve() if game_dir else None
    errors, warnings, scripts, localizations = [], [], {}, {}
    external_paths, referenced_states = set(), set()

    def issue(code, path, line, message):
        errors.append({"code": code, "file": str(path).replace("\\", "/"), "line": line, "message": message})

    mod = root / "mod"
    if not (mod / "descriptor.mod").is_file():
        issue("missing_mod", "mod/descriptor.mod", 0, "缺少正式 Mod 描述文件")
    for path in sorted(mod.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCRIPT_EXTENSIONS | {".yml"}:
            continue
        relative = path.relative_to(root).as_posix()
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8-sig")
        except (OSError, UnicodeError) as exc:
            issue("read_encoding", relative, 0, str(exc))
            continue
        bom = raw.startswith(b"\xef\xbb\xbf")
        if path.suffix == ".yml":
            if not bom:
                issue("localization_bom", relative, 1, "本地化必须保留 UTF-8 BOM")
            language = None
            for number, line in enumerate(text.splitlines(), 1):
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                header = re.fullmatch(r"\s*(l_\w+)\s*:\s*(?:#.*)?", line)
                if header:
                    language = header[1]
                    continue
                match = re.fullmatch(r'\s*([\w.\-]+)\s*:\s*(?:\d+\s*)?"(?:\\.|[^"\\])*"\s*(?:#.*)?', line)
                if not match or not language:
                    issue("localization_format", relative, number, "本地化行或语言头格式无效")
                    continue
                key = (language, match[1])
                if key in localizations:
                    issue("duplicate_localization", relative, number, f"重复本地化 {match[1]}；首次位于 {localizations[key]}")
                localizations[key] = f"{relative}:{number}"
        else:
            if bom:
                issue("script_bom", relative, 1, "非本地化脚本必须为 UTF-8 无 BOM")
            try:
                scripts[relative] = parse(text)
            except ValueError as exc:
                issue("syntax", relative, 0, str(exc))

    registry_path = "docs/design/aemusa_main_story_state_registry_expanded_v1.0.csv"
    states, registry_ids = {}, set()
    try:
        with (root / registry_path).open(encoding="utf-8-sig", newline="") as stream:
            for number, row in enumerate(csv.DictReader(stream), 2):
                if not all(row.get(key) for key in ("key", "registry_id", "data_type", "scope", "status")):
                    issue("registry_format", registry_path, number, "登记项缺少必要字段")
                    continue
                if row["key"] in states or row["registry_id"] in registry_ids:
                    issue("duplicate_state", registry_path, number, "状态 key 或登记编号重复")
                states[row["key"]] = row
                registry_ids.add(row["registry_id"])
    except (OSError, UnicodeError, csv.Error) as exc:
        issue("registry_read", registry_path, 0, str(exc))

    events, namespaces, interfaces, sprites = {}, set(), {}, set()
    for file, entries in scripts.items():
        local_constants = {e.key: e.value for e in entries if e.key.startswith("@") and isinstance(e.value, str)}
        for entry in entries:
            # 4.5.1 实测：激活零时长法令后打开内阁会触发整数除零崩溃。
            if file.startswith("mod/common/edicts/") and isinstance(entry.value, list):
                duration = next((e for e in entry.value if e.key == "length" and isinstance(e.value, str)), None)
                if duration:
                    value, seen = duration.value, set()
                    # 只解析本文件常量；循环或外部常量交由引擎语义验收，不猜测数值。
                    while value in local_constants and value not in seen:
                        seen.add(value)
                        value = local_constants[value]
                    if re.fullmatch(r"[+-]?0+(?:\.0+)?", value):
                        issue("zero_duration_edict", file, duration.line,
                              f"法令 {entry.key} 的 length 为 0，会触发 4.5.1 内阁崩溃；即时入口应保留至少 1 天有效期")
            if entry.key == "namespace" and isinstance(entry.value, str):
                namespaces.add(entry.value)
            # 原版无作用域事件使用 event，国家等有作用域事件使用 *_event。
            if file.startswith("mod/events/") and (entry.key == "event" or entry.key.endswith("_event")) and isinstance(entry.value, list):
                event_id = scalar(entry.value, "id")
                if not event_id or not EVENT_ID.fullmatch(event_id):
                    issue("event_id", file, entry.line, "事件缺少有效 ID")
                elif event_id in events:
                    issue("duplicate_event", file, entry.line, f"事件 ID 重复：{event_id}")
                else:
                    events[event_id] = (file, entry.line)
            if file.startswith(("mod/common/scripted_effects/", "mod/common/scripted_triggers/")) and entry.key:
                if entry.key in interfaces:
                    issue("duplicate_interface", file, entry.line, f"重复脚本接口：{entry.key}")
                interfaces[entry.key] = file
        for entry, _ in walk(entries):
            if entry.key == "spriteType" and isinstance(entry.value, list):
                name = scalar(entry.value, "name")
                if name:
                    if name in sprites:
                        issue("duplicate_sprite", file, entry.line, f"重复 sprite：{name}")
                    sprites.add(name)
    for event_id, (file, line) in events.items():
        if event_id.rsplit(".", 1)[0] not in namespaces:
            issue("missing_namespace", file, line, f"事件未声明 namespace：{event_id}")

    for file, entries in scripts.items():
        for entry, parents in walk(entries):
            if entry.key.startswith("aemusa_ms_") and parents and entry.key not in interfaces:
                issue("missing_interface", file, entry.line, f"主线调用没有定义：{entry.key}")
            if not isinstance(entry.value, str):
                continue
            value = entry.value
            event_ref = EVENT_ID.fullmatch(value)
            if event_ref and (event_ref[1] in namespaces or event_ref[1].startswith("aemusa")) and value not in events:
                issue("missing_event", file, entry.line, f"事件引用不存在：{value}")
            if file.startswith("mod/events/") and entry.key in {"title", "desc", "text", "name", "custom_tooltip"}:
                if OWNED.search(value) and re.fullmatch(r"[\w.\-]+", value) and ("l_simp_chinese", value) not in localizations:
                    issue("missing_localization", file, entry.line, f"事件中文本地化缺失：{value}")
            if entry.key == "picture" and OWNED.search(value) and value not in sprites:
                issue("missing_sprite", file, entry.line, f"事件图片未注册：{value}")
            if STATE.fullmatch(value):
                referenced_states.add(value)
                row = states.get(value)
                if not row:
                    issue("unregistered_state", file, entry.line, f"主线状态未登记：{value}")
                else:
                    mutation = entry.key in {"set_country_flag", "remove_country_flag", "set_leader_flag", "remove_leader_flag", "clear_variable"}
                    mutation |= entry.key == "which" and any(p in {"set_variable", "change_variable", "subtract_variable", "multiply_variable", "divide_variable"} for p in parents)
                    if mutation and row["status"].startswith("reserved"):
                        issue("reserved_state_write", file, entry.line, f"禁止写入尚待审核状态：{value}")
                    expected = "flag" if entry.key.endswith("_flag") else "variable" if entry.key in {"which", "is_variable_set", "clear_variable"} else None
                    if expected and row["data_type"] != expected:
                        issue("state_type", file, entry.line, f"状态类型不符：{value} 应为 {expected}")
            # 仅检查明确资源路径；不猜测引擎隐式图标命名或 shader 语义。
            if value.startswith("gfx/") and re.search(r"\.(dds|png|tga|mesh|anim)$", value, re.I):
                target = mod / value
                if not target.resolve().is_relative_to(mod.resolve()):
                    issue("asset_path", file, entry.line, f"资源路径越界：{value}")
                elif not target.is_file():
                    if OWNED.search(value):
                        issue("missing_asset", file, entry.line, f"项目资源不存在：{value}")
                    elif game_dir:
                        if not (game_dir / value).is_file():
                            issue("missing_external_asset", file, entry.line, f"游戏目录也没有资源：{value}")
                    else:
                        external_paths.add(value)
            elif entry.key in {"texture_diffuse", "texture_normal", "texture_specular"} and "/" not in value and OWNED.search(value):
                if not (root / file).parent.joinpath(value).is_file():
                    issue("missing_asset", file, entry.line, f"模型同目录纹理不存在：{value}")

    if external_paths:
        warnings.append({"code": "external_assets_unverified", "count": len(external_paths),
                         "message": "未提供 --game-dir；这些原版路径尚未验证", "paths": sorted(external_paths)})
    return {"status": "fail" if errors else "pass", "errors": errors, "warnings": warnings,
            "counts": {"script_files": len(scripts), "events": len(events), "localization_keys": len(localizations),
                       "registered_states": len(states), "referenced_states": len(referenced_states)},
            "limitations": ["仅验证结构和项目内显式引用，不验证原版触发器、效果、作用域、数值平衡或事件可达性。",
                            "未校验引擎隐式岗位、修正、trait、outliner 图标；须以最新冷启动日志和游戏内显示验收。",
                            "未运行游戏；静态 pass 不能变更 runtime_status，也不能代替存档及日志证据。"]}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--game-dir", type=Path)
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果，不创建报告文件")
    args = parser.parse_args()
    result = check(args.root, args.game_dir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Static check: {result['status'].upper()} | {result['counts']}")
        for error in result["errors"]:
            print(f"ERROR {error['code']} {error['file']}:{error['line']} {error['message']}")
        for warning in result["warnings"]:
            print(f"WARNING {warning['code']}: {warning['message']} ({warning['count']})")
        for note in result["limitations"]:
            print(f"NOTE {note}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
