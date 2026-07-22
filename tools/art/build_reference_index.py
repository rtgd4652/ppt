#!/usr/bin/env python3
"""校验参考图登记表，并生成不包含任何图片副本的 Markdown 视觉索引。"""

from __future__ import annotations

import argparse
import csv
import html
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import quote, urlsplit


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "docs/art/reference_library/REFERENCE_MANIFEST.csv"

# 表头是参考图库的数据契约。某些字段允许单条记录留空，但列本身不能缺失。
REQUIRED_COLUMNS: tuple[str, ...] = (
    "reference_id",
    "title",
    "category",
    "subcategory",
    "subject",
    "character_or_faction",
    "source_type",
    "source_locator",
    "local_path",
    "copyright_or_license_status",
    "allowed_usage",
    "visual_role",
    "visual_tags",
    "palette_tags",
    "shape_tags",
    "material_tags",
    "composition_tags",
    "what_to_learn",
    "what_not_to_copy",
    "linked_moodboards",
    "review_status",
    "notes",
)

# 这些值决定一条记录是否足以被索引。来源、授权和分析缺失会作为警告单独标出，
# 以便尚在搜集阶段的条目仍能出现在索引中，而不会被悄悄遗漏。
REQUIRED_VALUE_FIELDS: tuple[str, ...] = (
    "reference_id",
    "title",
    "category",
    "subcategory",
    "subject",
    "source_type",
    "allowed_usage",
    "visual_role",
    "review_status",
)

ENUM_VALUES: dict[str, frozenset[str]] = {
    "visual_role": frozenset(
        {
            "primary_anchor",
            "secondary_reference",
            "technical_reference",
            "material_reference",
            "composition_reference",
            "effect_reference",
            "anti_reference",
        }
    ),
    "review_status": frozenset(
        {
            "unreviewed",
            "reviewed",
            "approved_anchor",
            "supporting",
            "rejected",
            "source_uncertain",
        }
    ),
    "copyright_or_license_status": frozenset(
        {
            "user_owned",
            "project_created",
            "official_game_reference",
            "public_domain",
            "licensed",
            "external_reference_only",
            "unknown",
        }
    ),
}

IMAGE_EXTENSIONS = frozenset(
    {".avif", ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".tif", ".tiff", ".webp"}
)


@dataclass(frozen=True)
class Issue:
    """一条可供终端和 Markdown 索引共同展示的质量问题。"""

    severity: str
    code: str
    message: str
    row_number: int | None = None
    reference_id: str = ""


@dataclass(frozen=True)
class Reference:
    """已清理空白、保留 CSV 行号的单条参考记录。"""

    row_number: int
    values: dict[str, str]
    resolved_local_path: Path | None = None
    local_path_exists: bool | None = None

    def get(self, field: str) -> str:
        return self.values.get(field, "")

    @property
    def reference_id(self) -> str:
        return self.get("reference_id")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="离线校验 REFERENCE_MANIFEST.csv，并按分类生成 Markdown 视觉索引。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python tools/art/build_reference_index.py\n"
            "  python tools/art/build_reference_index.py path/to/REFERENCE_MANIFEST.csv -o path/to/INDEX.md\n"
            "  python tools/art/build_reference_index.py --check --strict\n\n"
            "本工具不访问网络、不下载素材、不修改原图，也不生成图片副本。"
        ),
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f"登记表路径（默认：{DEFAULT_MANIFEST}）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="输出 Markdown 路径（默认：登记表同目录下的 REFERENCE_INDEX.md）",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help=f"解析相对 local_path 时使用的项目根目录（默认：{REPO_ROOT}）",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅校验，不写入 Markdown 索引",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：存在任何警告时也返回非零退出码",
    )
    return parser.parse_args(argv)


def _issue(
    issues: list[Issue],
    severity: str,
    code: str,
    message: str,
    reference: Reference | None = None,
    *,
    row_number: int | None = None,
) -> None:
    issues.append(
        Issue(
            severity=severity,
            code=code,
            message=message,
            row_number=reference.row_number if reference else row_number,
            reference_id=reference.reference_id if reference else "",
        )
    )


def _normalise_row(headers: Sequence[str], cells: Sequence[str]) -> dict[str, str]:
    padded = list(cells[: len(headers)]) + [""] * max(0, len(headers) - len(cells))
    return {field: value.strip() for field, value in zip(headers, padded) if field}


def load_manifest(manifest_path: Path, project_root: Path) -> tuple[list[Reference], list[Issue], bool]:
    """读取并校验登记表；第三个返回值表示是否遇到无法继续的读取错误。"""

    references: list[Reference] = []
    issues: list[Issue] = []

    try:
        source = manifest_path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        _issue(issues, "error", "manifest_unreadable", f"无法读取登记表：{exc}")
        return references, issues, True

    try:
        with source:
            reader = csv.reader(source)
            try:
                raw_headers = next(reader)
            except StopIteration:
                _issue(issues, "error", "manifest_empty", "登记表为空，缺少表头")
                return references, issues, True

            headers = [header.strip() for header in raw_headers]
            duplicate_headers = sorted({header for header in headers if header and headers.count(header) > 1})
            for header in duplicate_headers:
                _issue(issues, "error", "duplicate_column", f"表头重复：{header}", row_number=1)
            if any(not header for header in headers):
                _issue(issues, "error", "empty_column", "表头中存在空列名", row_number=1)

            for column in REQUIRED_COLUMNS:
                if column not in headers:
                    _issue(issues, "error", "missing_column", f"缺少必需列：{column}", row_number=1)

            for row_number, cells in enumerate(reader, start=2):
                if not any(cell.strip() for cell in cells):
                    continue
                if len(cells) > len(headers):
                    _issue(
                        issues,
                        "error",
                        "extra_cells",
                        f"记录比表头多 {len(cells) - len(headers)} 个单元格",
                        row_number=row_number,
                    )
                values = _normalise_row(headers, cells)
                references.append(Reference(row_number=row_number, values=values))
    except (csv.Error, UnicodeError) as exc:
        _issue(issues, "error", "manifest_parse_error", f"CSV 解析失败：{exc}")
        return references, issues, True

    references = validate_references(references, project_root, issues)
    return references, issues, False


def validate_references(
    references: Sequence[Reference], project_root: Path, issues: list[Issue]
) -> list[Reference]:
    """完成逐行、枚举、唯一性和本地文件检查。"""

    validated: list[Reference] = []
    seen_ids: dict[str, Reference] = {}

    for reference in references:
        for field in REQUIRED_VALUE_FIELDS:
            if not reference.get(field):
                _issue(issues, "error", "missing_required_value", f"必填字段为空：{field}", reference)

        reference_key = reference.reference_id.casefold()
        if reference_key:
            if reference_key in seen_ids:
                first = seen_ids[reference_key]
                _issue(
                    issues,
                    "error",
                    "duplicate_reference_id",
                    f"reference_id 与第 {first.row_number} 行重复：{reference.reference_id}",
                    reference,
                )
            else:
                seen_ids[reference_key] = reference

        for field, allowed_values in ENUM_VALUES.items():
            value = reference.get(field)
            if value and value not in allowed_values:
                allowed = ", ".join(sorted(allowed_values))
                _issue(
                    issues,
                    "error",
                    "invalid_enum",
                    f"{field} 的值“{value}”不合法；允许值：{allowed}",
                    reference,
                )

        if not reference.get("source_locator"):
            _issue(issues, "warning", "missing_source", "缺少 source_locator", reference)
        if not reference.get("copyright_or_license_status"):
            _issue(issues, "warning", "missing_rights", "缺少版权或许可状态", reference)
        elif reference.get("copyright_or_license_status") == "unknown":
            _issue(issues, "warning", "rights_unknown", "版权或许可状态仍为 unknown", reference)
        if not reference.get("what_to_learn"):
            _issue(issues, "warning", "missing_learning_notes", "缺少 what_to_learn 视觉分析", reference)
        if not reference.get("what_not_to_copy"):
            _issue(issues, "warning", "missing_copy_boundary", "缺少 what_not_to_copy 使用边界", reference)

        review_status = reference.get("review_status")
        if review_status == "unreviewed":
            _issue(issues, "warning", "unreviewed", "条目尚未审核", reference)
        elif review_status == "source_uncertain":
            _issue(issues, "warning", "source_uncertain", "条目来源仍待确认", reference)

        raw_local_path = reference.get("local_path")
        resolved: Path | None = None
        exists: bool | None = None
        if raw_local_path:
            if "://" in raw_local_path:
                _issue(
                    issues,
                    "warning",
                    "local_path_is_url",
                    "local_path 应为文件系统路径，网络地址应填写在 source_locator",
                    reference,
                )
                exists = False
            else:
                try:
                    candidate = Path(raw_local_path)
                    resolved = candidate if candidate.is_absolute() else project_root / candidate
                    resolved = resolved.resolve(strict=False)
                    exists = resolved.is_file()
                except OSError as exc:
                    _issue(
                        issues,
                        "warning",
                        "local_path_invalid",
                        f"无法检查 local_path：{exc}",
                        reference,
                    )
                    exists = False
                else:
                    if not exists:
                        _issue(
                            issues,
                            "warning",
                            "local_path_missing",
                            f"local_path 不存在或不是文件：{raw_local_path}",
                            reference,
                        )

        validated.append(
            Reference(
                row_number=reference.row_number,
                values=reference.values,
                resolved_local_path=resolved,
                local_path_exists=exists,
            )
        )

    return validated


def _md_cell(value: str) -> str:
    escaped = html.escape(value, quote=False).replace("|", "&#124;")
    return escaped.replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")


def _code(value: str) -> str:
    return f"<code>{html.escape(value)}</code>"


def _markdown_destination(value: str) -> str:
    # 保留 URL/相对路径结构，同时编码空格、尖括号等会破坏 Markdown 的字符。
    return quote(value, safe="/:@?&=#%+,$;~*'()-._")


def _relative_destination(target: Path, output_directory: Path) -> str | None:
    try:
        relative = Path(os.path.relpath(target, start=output_directory))
    except ValueError:
        # Windows 不同盘符之间没有相对路径；此时宁可不预览，也不写 file:// 或图片副本。
        return None
    return _markdown_destination(relative.as_posix())


def _source_cell(locator: str) -> str:
    if not locator:
        return "⚠ 缺少来源"
    parsed = urlsplit(locator)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return f"[打开来源](<{_markdown_destination(locator)}>)"
    return _code(locator)


def _local_file_cell(reference: Reference, output_directory: Path) -> str:
    raw_path = reference.get("local_path")
    if not raw_path:
        return "仅登记来源（无本地副本）"
    if not reference.local_path_exists or reference.resolved_local_path is None:
        return f"⚠ 不存在：{_code(raw_path)}"
    destination = _relative_destination(reference.resolved_local_path, output_directory)
    if destination is None:
        return f"存在，但与索引不在同一盘符：{_code(raw_path)}"
    return f"[打开本地文件](<{destination}>)<br>{_code(raw_path)}"


def _preview_line(reference: Reference, output_directory: Path) -> str | None:
    path = reference.resolved_local_path
    if not reference.local_path_exists or path is None or path.suffix.casefold() not in IMAGE_EXTENSIONS:
        return None
    destination = _relative_destination(path, output_directory)
    if destination is None:
        return None
    alt = reference.get("title") or reference.reference_id or "参考图"
    alt = alt.replace("[", "\\[").replace("]", "\\]").replace("\n", " ").replace("\r", " ")
    return f"![{alt}](<{destination}>)"


def _record_issues(reference: Reference, issues: Sequence[Issue]) -> list[Issue]:
    return [issue for issue in issues if issue.row_number == reference.row_number]


def _status_summary(references: Sequence[Reference], issues: Sequence[Issue]) -> dict[str, int]:
    return {
        "records": len(references),
        "categories": len({reference.get("category") or "未分类" for reference in references}),
        "local_paths": sum(bool(reference.get("local_path")) for reference in references),
        "local_existing": sum(reference.local_path_exists is True for reference in references),
        "local_missing": sum(issue.code == "local_path_missing" for issue in issues),
        "missing_source": sum(issue.code == "missing_source" for issue in issues),
        "rights_attention": sum(issue.code in {"missing_rights", "rights_unknown"} for issue in issues),
        "review_attention": sum(issue.code in {"unreviewed", "source_uncertain"} for issue in issues),
        "errors": sum(issue.severity == "error" for issue in issues),
        "warnings": sum(issue.severity == "warning" for issue in issues),
    }


def _format_issue(issue: Issue) -> str:
    severity = "错误" if issue.severity == "error" else "警告"
    location_parts: list[str] = []
    if issue.row_number is not None:
        location_parts.append(f"第 {issue.row_number} 行")
    if issue.reference_id:
        location_parts.append(issue.reference_id)
    location = " / ".join(location_parts) or "登记表"
    return f"**{severity}** · {_md_cell(location)} · `{issue.code}`：{_md_cell(issue.message)}"


def _append_metadata_row(lines: list[str], label: str, value: str) -> None:
    if value:
        lines.append(f"| {_md_cell(label)} | {value} |")


def render_index(
    references: Sequence[Reference],
    issues: Sequence[Issue],
    manifest_path: Path,
    output_path: Path,
) -> str:
    """生成确定性的 Markdown；不读取、转换或复制任何图片内容。"""

    summary = _status_summary(references, issues)
    manifest_destination = _relative_destination(manifest_path, output_path.parent)
    manifest_link = (
        f"[REFERENCE_MANIFEST.csv](<{manifest_destination}>)"
        if manifest_destination is not None
        else _code(str(manifest_path))
    )

    lines = [
        "<!-- 由 tools/art/build_reference_index.py 自动生成；请修改 CSV 后重新生成本页。 -->",
        "# 视觉参考索引",
        "",
        "> 本索引只提供视觉分析入口。出现于此不代表素材可再分发或可直接进入游戏；正式资产必须另行登记和审核。",
        "",
        f"数据源：{manifest_link}",
        "",
        "## 汇总",
        "",
        "| 指标 | 数量 |",
        "| --- | ---: |",
        f"| 参考记录 | {summary['records']} |",
        f"| 分类 | {summary['categories']} |",
        f"| 填写了 local_path | {summary['local_paths']} |",
        f"| 本地文件存在 | {summary['local_existing']} |",
        f"| 本地文件缺失 | {summary['local_missing']} |",
        f"| 缺少来源 | {summary['missing_source']} |",
        f"| 授权状态需关注 | {summary['rights_attention']} |",
        f"| 审核状态需关注 | {summary['review_attention']} |",
        f"| 校验错误 | {summary['errors']} |",
        f"| 校验警告 | {summary['warnings']} |",
        "",
    ]

    if issues:
        lines.extend(["## 质量提示", ""])
        for issue in issues:
            lines.append(f"- {_format_issue(issue)}")
        lines.append("")
    else:
        lines.extend(["## 质量提示", "", "未发现校验问题。", ""])

    grouped: dict[str, dict[str, list[Reference]]] = defaultdict(lambda: defaultdict(list))
    for reference in references:
        category = reference.get("category") or "未分类"
        subcategory = reference.get("subcategory") or "未细分"
        grouped[category][subcategory].append(reference)

    lines.extend(["## 分类索引", ""])
    if not references:
        lines.extend(["登记表中暂无参考记录。", ""])

    for category in sorted(grouped, key=str.casefold):
        lines.extend([f"### {_md_cell(category)}", ""])
        for subcategory in sorted(grouped[category], key=str.casefold):
            lines.extend([f"#### {_md_cell(subcategory)}", ""])
            records = sorted(
                grouped[category][subcategory],
                key=lambda item: (item.reference_id.casefold(), item.get("title").casefold(), item.row_number),
            )
            for reference in records:
                record_id = reference.reference_id or f"第 {reference.row_number} 行（缺少 ID）"
                title = reference.get("title") or "未命名参考"
                lines.extend([f"##### {_code(record_id)} · {_md_cell(title)}", ""])

                preview = _preview_line(reference, output_path.parent)
                if preview:
                    lines.extend([preview, ""])

                lines.extend(["| 字段 | 内容 |", "| --- | --- |"])
                _append_metadata_row(lines, "对象", _md_cell(reference.get("subject")))
                _append_metadata_row(lines, "角色／阵营", _md_cell(reference.get("character_or_faction")))
                source_value = _md_cell(reference.get("source_type"))
                if source_value:
                    source_value += " · "
                source_value += _source_cell(reference.get("source_locator"))
                _append_metadata_row(lines, "来源", source_value)
                rights_value = _md_cell(reference.get("copyright_or_license_status") or "⚠ 未填写")
                usage = _md_cell(reference.get("allowed_usage"))
                if usage:
                    rights_value += f" · {usage}"
                _append_metadata_row(lines, "权利与用途", rights_value)
                _append_metadata_row(lines, "视觉角色", _code(reference.get("visual_role")))
                _append_metadata_row(lines, "审核状态", _code(reference.get("review_status")))

                tag_parts = []
                for label, field in (
                    ("视觉", "visual_tags"),
                    ("配色", "palette_tags"),
                    ("形状", "shape_tags"),
                    ("材质", "material_tags"),
                    ("构图", "composition_tags"),
                ):
                    if reference.get(field):
                        tag_parts.append(f"{label}：{_md_cell(reference.get(field))}")
                _append_metadata_row(lines, "标签", "<br>".join(tag_parts))
                _append_metadata_row(lines, "可学习", _md_cell(reference.get("what_to_learn")))
                _append_metadata_row(lines, "禁止照搬", _md_cell(reference.get("what_not_to_copy")))
                _append_metadata_row(lines, "关联 Moodboard", _md_cell(reference.get("linked_moodboards")))
                _append_metadata_row(lines, "本地文件", _local_file_cell(reference, output_path.parent))
                _append_metadata_row(lines, "备注", _md_cell(reference.get("notes")))

                record_issues = _record_issues(reference, issues)
                if record_issues:
                    flags = "<br>".join(
                        f"{'❌' if issue.severity == 'error' else '⚠'} "
                        f"{_md_cell(issue.message)} (`{issue.code}`)"
                        for issue in record_issues
                    )
                    _append_metadata_row(lines, "质量标记", flags)
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def print_report(references: Sequence[Reference], issues: Sequence[Issue]) -> None:
    summary = _status_summary(references, issues)
    print(
        "检查完成："
        f"{summary['records']} 条记录，{summary['errors']} 个错误，{summary['warnings']} 个警告。"
    )
    for issue in issues:
        severity = "错误" if issue.severity == "error" else "警告"
        location = f"第 {issue.row_number} 行" if issue.row_number is not None else "登记表"
        ref_id = f" {issue.reference_id}" if issue.reference_id else ""
        print(f"[{severity}] {location}{ref_id} {issue.code}: {issue.message}")


def write_index(output_path: Path, content: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as target:
        target.write(content)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = args.manifest.resolve(strict=False)
    project_root = args.root.resolve(strict=False)
    output_path = (args.output or manifest_path.with_name("REFERENCE_INDEX.md")).resolve(strict=False)

    if output_path == manifest_path and not args.check:
        print("错误：输出路径不能与登记表路径相同。", file=sys.stderr)
        return 2

    references, issues, fatal = load_manifest(manifest_path, project_root)
    print_report(references, issues)
    if fatal:
        return 2

    if not args.check:
        try:
            content = render_index(references, issues, manifest_path, output_path)
            write_index(output_path, content)
        except OSError as exc:
            print(f"错误：无法写入索引 {output_path}：{exc}", file=sys.stderr)
            return 2
        print(f"已生成索引：{output_path}")
    else:
        print("仅检查模式：未写入索引。")

    has_errors = any(issue.severity == "error" for issue in issues)
    has_warnings = any(issue.severity == "warning" for issue in issues)
    return 1 if has_errors or (args.strict and has_warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
