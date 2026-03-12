from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PDF = ROOT / "template" / "main.pdf"
DEFAULT_TEX = ROOT / "template" / "main.tex"
DEFAULT_REPORT = ROOT / "template" / "layout_diagnosis.json"
DEFAULT_TASKS = ROOT / "template" / "layout_tasks.json"
KNOWN_SECTIONS = {"教育经历", "工作经历", "项目经历", "校园经历", "技能"}
BULLET_MARKERS = {"•", "◦", "◇", "–", "-", "·"}
ITEM_RE = re.compile(r"^\s*\\item\s+(.*)$")


@dataclass
class PdfLine:
    page: int
    text: str
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    @property
    def width(self) -> float:
        return self.x_max - self.x_min


@dataclass
class PdfFragment:
    page: int
    text: str
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    @property
    def y_center(self) -> float:
        return (self.y_min + self.y_max) / 2


def run_command(args: list[str]) -> str:
    completed = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"Command failed: {' '.join(args)}")
    return completed.stdout


def pdfinfo_data(pdf_path: Path) -> dict:
    output = run_command(["pdfinfo", str(pdf_path)])
    data = {}
    for raw in output.splitlines():
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def extract_bbox_xml(pdf_path: Path) -> str:
    return run_command(["pdftotext", "-bbox-layout", str(pdf_path), "-"])


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def child_elements(node: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(node) if local_name(child.tag) == name]


def parse_lines(xml_text: str) -> tuple[list[PdfLine], float, float]:
    root = ET.fromstring(xml_text)
    fragments: list[PdfFragment] = []
    page_width = 0.0
    page_height = 0.0

    pages = [node for node in root.iter() if local_name(node.tag) == "page"]
    for page_index, page in enumerate(pages, start=1):
        page_width = max(page_width, float(page.attrib.get("width", "0")))
        page_height = max(page_height, float(page.attrib.get("height", "0")))
        page_lines = [node for node in page.iter() if local_name(node.tag) == "line"]
        for line in page_lines:
            words = child_elements(line, "word")
            if not words:
                continue
            text = "".join(word.text or "" for word in words).strip()
            if not text:
                continue
            x_vals = [float(word.attrib["xMin"]) for word in words]
            x_max_vals = [float(word.attrib["xMax"]) for word in words]
            y_vals = [float(word.attrib["yMin"]) for word in words]
            y_max_vals = [float(word.attrib["yMax"]) for word in words]
            fragments.append(
                PdfFragment(
                    page=page_index,
                    text=text,
                    x_min=min(x_vals),
                    x_max=max(x_max_vals),
                    y_min=min(y_vals),
                    y_max=max(y_max_vals),
                )
            )

    merged_lines = merge_fragments_into_visual_lines(fragments)
    merged_lines.sort(key=lambda item: (item.page, item.y_min, item.x_min))
    return merged_lines, page_width, page_height


def merge_fragments_into_visual_lines(fragments: list[PdfFragment], tolerance: float = 1.6) -> list[PdfLine]:
    grouped: dict[int, list[list[PdfFragment]]] = {}

    for fragment in sorted(fragments, key=lambda item: (item.page, item.y_center, item.x_min)):
        page_groups = grouped.setdefault(fragment.page, [])
        if not page_groups:
            page_groups.append([fragment])
            continue

        last_group = page_groups[-1]
        last_center = sum(item.y_center for item in last_group) / len(last_group)
        if abs(fragment.y_center - last_center) <= tolerance:
            last_group.append(fragment)
        else:
            page_groups.append([fragment])

    visual_lines: list[PdfLine] = []
    for page, page_groups in grouped.items():
        for group in page_groups:
            group.sort(key=lambda item: item.x_min)
            text = " ".join(item.text for item in group).strip()
            visual_lines.append(
                PdfLine(
                    page=page,
                    text=text,
                    x_min=min(item.x_min for item in group),
                    x_max=max(item.x_max for item in group),
                    y_min=min(item.y_min for item in group),
                    y_max=max(item.y_max for item in group),
                )
            )

    return visual_lines


def is_section_header(line: PdfLine) -> bool:
    return line.text in KNOWN_SECTIONS and line.x_min <= 32


def split_marker(text: str) -> tuple[str, str]:
    if not text:
        return "", ""
    first = text[0]
    if first in BULLET_MARKERS:
        return first, text[1:].strip()
    return "", text


def is_bullet_line(line: PdfLine) -> bool:
    marker, remainder = split_marker(line.text)
    return bool(marker and remainder)


def section_for_lines(lines: list[PdfLine]) -> list[tuple[PdfLine, str]]:
    current = "未归类"
    out = []
    for line in lines:
        if is_section_header(line):
            current = line.text
        out.append((line, current))
    return out


def read_tex_items(tex_path: Path) -> list[dict]:
    lines = tex_path.read_text(encoding="utf-8-sig").splitlines()
    items = []
    for idx, line in enumerate(lines, start=1):
        match = ITEM_RE.match(line)
        if match:
            items.append(
                {
                    "latex_line_index": idx,
                    "original_text": match.group(1).strip(),
                }
            )
    return items


def build_rewrite_hint(item: dict) -> str:
    target_trim = item["suggested_trim_chars"]
    if "short_tail" in item["warnings"] and "long_bullet" in item["warnings"]:
        return f"这条同时存在长 bullet 和短尾行，优先合并重复表达并压缩约 {target_trim} 个字，保留事实、指标和结论。"
    if "short_tail" in item["warnings"]:
        return f"这条是短尾行，优先删除语气词、重复修饰语或冗余连接词，目标压缩约 {target_trim} 个字，不改核心信息。"
    if "long_bullet" in item["warnings"]:
        return "这条偏长，优先合并近义表达、缩短状语和重复限定语，不改信息重心。"
    return "仅在必要时做轻微压字。"


def analyze_bullets(lines: list[PdfLine], page_width: float, tex_items: list[dict]) -> list[dict]:
    results: list[dict] = []
    annotated = section_for_lines(lines)
    right_margin = 28.0
    idx = 0
    bullet_index = 0

    while idx < len(annotated):
        line, section = annotated[idx]
        if not is_bullet_line(line):
            idx += 1
            continue

        _, body_text = split_marker(line.text)
        text_x = line.x_min + 6.0
        bullet_lines = [line]
        idx += 1

        while idx < len(annotated):
            next_line, next_section = annotated[idx]
            if next_section != section:
                break
            if is_section_header(next_line) or is_bullet_line(next_line):
                break
            if next_line.x_min < text_x - 10:
                break
            bullet_lines.append(next_line)
            idx += 1

        line_count = len(bullet_lines)
        full_width = max(page_width - right_margin - text_x, 1.0)
        last_line = bullet_lines[-1]
        last_ratio = max(min(last_line.width / full_width, 1.0), 0.0)
        joined_text = " ".join(split_marker(item.text)[1] if j == 0 else item.text for j, item in enumerate(bullet_lines))

        warnings = []
        if line_count >= 3:
            warnings.append("long_bullet")
        if line_count >= 2 and last_ratio < 0.38:
            warnings.append("short_tail")

        suggested_trim = 0
        if "short_tail" in warnings:
            suggested_trim = 2 if last_ratio >= 0.28 else 4 if last_ratio >= 0.18 else 6

        tex_info = tex_items[bullet_index] if bullet_index < len(tex_items) else {"latex_line_index": None, "original_text": ""}
        result = {
            "section": section,
            "bullet_index": bullet_index,
            "page": line.page,
            "indent_x": round(line.x_min, 2),
            "line_count": line_count,
            "last_line_fill_ratio": round(last_ratio, 3),
            "warnings": warnings,
            "suggested_trim_chars": suggested_trim,
            "preview": joined_text[:120] if body_text else joined_text[:120],
            "latex_line_index": tex_info["latex_line_index"],
            "original_text": tex_info["original_text"],
        }
        result["rewrite_hint"] = build_rewrite_hint(result)
        results.append(result)
        bullet_index += 1

    return results


def analyze_pages(lines: list[PdfLine], page_height: float, target_pages: int) -> dict:
    page_map: dict[int, list[PdfLine]] = {}
    for line in lines:
        page_map.setdefault(line.page, []).append(line)

    page_stats = []
    for page, page_lines in sorted(page_map.items()):
        bottom = max(line.y_max for line in page_lines)
        fullness = bottom / page_height if page_height else 0.0
        status = "balanced"
        if fullness < 0.83:
            status = "sparse_page"
        elif fullness > 0.965:
            status = "dense_page"
        page_stats.append(
            {
                "page": page,
                "bottom_y": round(bottom, 2),
                "page_height": round(page_height, 2),
                "fullness_ratio": round(fullness, 3),
                "status": status,
            }
        )

    overflow = len(page_stats) > target_pages
    return {"overflow": overflow, "pages": page_stats}


def build_summary(pdf_info: dict, bullet_stats: list[dict], page_stats: dict, target_pages: int) -> dict:
    flagged = [item for item in bullet_stats if item["warnings"]]
    return {
        "target_pages": target_pages,
        "actual_pages": int(pdf_info.get("Pages", "0") or 0),
        "overflow": page_stats["overflow"],
        "flagged_bullets": len(flagged),
        "flagged_short_tail": sum("short_tail" in item["warnings"] for item in flagged),
        "flagged_long_bullet": sum("long_bullet" in item["warnings"] for item in flagged),
    }


def build_tasks(summary: dict, page_stats: dict, bullet_stats: list[dict]) -> list[dict]:
    tasks: list[dict] = []

    for item in bullet_stats:
        if not item["warnings"]:
            continue
        tasks.append(
            {
                "type": "rewrite_bullet",
                "priority": 100 if summary.get("overflow") else 80 if "short_tail" in item["warnings"] else 60,
                "section": item["section"],
                "bullet_index": item["bullet_index"],
                "page": item["page"],
                "warnings": item["warnings"],
                "target_trim_chars": item["suggested_trim_chars"],
                "latex_line_index": item["latex_line_index"],
                "original_text": item["original_text"],
                "rewrite_hint": item["rewrite_hint"],
                "instruction": (
                    f"仅改写这一条 bullet，尽量压缩约 {item['suggested_trim_chars']} 个字，"
                    "保留事实与语义重心，不要改动其他 bullet。"
                ),
                "preview": item["preview"],
            }
        )

    for page in page_stats["pages"]:
        if page["status"] == "sparse_page":
            tasks.append(
                {
                    "type": "review_spacing",
                    "priority": 30,
                    "page": page["page"],
                    "status": page["status"],
                    "instruction": "页面偏空，可在文案稳定后考虑适度放松 section 或 list 间距；优先不动全局字号。",
                }
            )
        elif page["status"] == "dense_page":
            tasks.append(
                {
                    "type": "review_density",
                    "priority": 90,
                    "page": page["page"],
                    "status": page["status"],
                    "instruction": "页面偏满，优先处理已标记 bullet，再考虑局部 list 间距。",
                }
            )

    tasks.sort(key=lambda item: item["priority"], reverse=True)
    return tasks


def print_report(summary: dict, page_stats: dict, bullets: list[dict]) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("Layout diagnosis")
    print(f"- pages: {summary['actual_pages']} / target {summary['target_pages']}")
    print(f"- overflow: {'yes' if summary['overflow'] else 'no'}")
    for page in page_stats["pages"]:
        print(f"- page {page['page']}: fullness={page['fullness_ratio']} status={page['status']}")

    flagged = [item for item in bullets if item["warnings"]]
    if not flagged:
        print("- bullets: no obvious long-bullet or short-tail risks detected")
        return

    print("- flagged bullets:")
    for item in flagged[:12]:
        warning_text = ",".join(item["warnings"])
        trim_note = f", suggest trim {item['suggested_trim_chars']} chars" if item["suggested_trim_chars"] else ""
        print(
            f"  - [{item['section']}] bullet#{item['bullet_index']} page {item['page']} "
            f"lines={item['line_count']} last-fill={item['last_line_fill_ratio']} "
            f"warnings={warning_text}{trim_note} :: {item['preview']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose line-count and spacing risks from the compiled resume PDF.")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF, help="Path to compiled PDF.")
    parser.add_argument("--tex", type=Path, default=DEFAULT_TEX, help="Path to rendered TeX file.")
    parser.add_argument("--target-pages", type=int, default=1, help="Expected maximum page count.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_REPORT, help="Optional JSON report path.")
    parser.add_argument("--tasks-output", type=Path, default=DEFAULT_TASKS, help="Optional layout task path for agent-guided rewrites.")
    parser.add_argument("--fail-on-overflow", action="store_true", help="Exit non-zero when page count exceeds target.")
    args = parser.parse_args()

    if not args.pdf.exists():
        raise SystemExit(f"PDF not found: {args.pdf}")
    if not args.tex.exists():
        raise SystemExit(f"TeX not found: {args.tex}")

    pdf_info = pdfinfo_data(args.pdf)
    xml_text = extract_bbox_xml(args.pdf)
    lines, page_width, page_height = parse_lines(xml_text)
    tex_items = read_tex_items(args.tex)
    page_stats = analyze_pages(lines, page_height, args.target_pages)
    bullets = analyze_bullets(lines, page_width, tex_items)
    summary = build_summary(pdf_info, bullets, page_stats, args.target_pages)

    payload = {
        "summary": summary,
        "pages": page_stats["pages"],
        "bullets": bullets,
    }
    tasks = build_tasks(summary, page_stats, bullets)

    if args.json_output:
        args.json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.tasks_output:
        args.tasks_output.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

    print_report(summary, page_stats, bullets)
    print(f"- tasks: {len(tasks)} written to {args.tasks_output}")

    if args.fail_on_overflow and summary["overflow"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
