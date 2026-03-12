from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "input_templates" / "resume_input_template_word.docx"
DEFAULT_OUTPUT = ROOT / "input_templates" / "resume_input_from_word.md"

SECTION_MAP = {
    "教育经历": "education",
    "工作经历": "experience",
    "项目经历": "projects",
    "校园经历": "campus",
    "技能": "skills",
}
SECTION_SEQUENCE = ["education", "experience", "projects", "campus", "skills"]

HEADER_LABELS = {
    "姓名：": "name",
    "姓名:": "name",
    "求职方向：": "target_role",
    "求职方向:": "target_role",
    "求职意向：": "target_role",
    "求职意向:": "target_role",
    "基本信息：": "meta",
    "基本信息:": "meta",
}

BULLET_PREFIX_RE = re.compile(r"^[-+*\u2022]\s+(.*)$")
NUMBERED_ENTRY_RE = re.compile(r"^\d+\.\s+(.*)$")


def clean(text: str) -> str:
    return " ".join(text.replace("\u3000", " ").split()).strip()


def strip_placeholder_prefix(text: str) -> str:
    return text.lstrip("?？:： ")


def is_placeholder_heading(text: str) -> bool:
    normalized = text.strip()
    return bool(normalized) and all(ch in "?？【】[]（）() " for ch in normalized)


def new_entry(title: str, subtitle: str = "", date: str = "") -> dict:
    return {
        "title": title or "示例条目",
        "title_link": "",
        "subtitle": subtitle,
        "date": date,
        "degree_line": subtitle,
        "bullets": [],
    }


def parse_entry_line(text: str, current_section: str) -> dict:
    body = NUMBERED_ENTRY_RE.sub(r"\1", text, count=1).strip()
    parts = [part.strip() for part in body.split(" | ")]
    title = parts[0] if parts else "示例条目"
    subtitle = parts[1] if len(parts) > 1 else ""
    date = parts[2] if len(parts) > 2 else ""
    entry = new_entry(title, subtitle, date)
    if current_section != "education":
        entry["degree_line"] = ""
    return entry


def parse_docx(path: Path) -> dict:
    doc = Document(path)
    data = {
        "name": "你的姓名",
        "target_role": "目标岗位",
        "meta": "手机号 | 邮箱 | GitHub | 其他信息",
        "education": [],
        "experience": [],
        "projects": [],
        "campus": [],
        "skills": [],
    }

    current_section: str | None = None
    current_entry: dict | None = None
    pending_header_fields = ["name", "target_role", "meta"]
    next_section_index = 0

    for paragraph in doc.paragraphs:
        raw = paragraph.text.replace("\u3000", " ")
        indent = len(raw) - len(raw.lstrip(" "))
        text = clean(raw)
        if not text:
            continue

        matched_header = False
        for label, field in HEADER_LABELS.items():
            if text.startswith(label):
                value = text.split(label, 1)[1].strip()
                if value:
                    data[field] = value
                if pending_header_fields and pending_header_fields[0] == field:
                    pending_header_fields.pop(0)
                matched_header = True
                break
        if matched_header:
            continue

        stripped_text = strip_placeholder_prefix(text)
        if pending_header_fields and stripped_text != text and stripped_text:
            field = pending_header_fields.pop(0)
            data[field] = stripped_text
            continue

        if text.startswith("【") and text.endswith("】"):
            section_name = text[1:-1].strip()
            current_section = SECTION_MAP.get(section_name)
            current_entry = None
            if current_section in SECTION_SEQUENCE:
                next_section_index = SECTION_SEQUENCE.index(current_section) + 1
            continue

        if (
            not pending_header_fields
            and is_placeholder_heading(text)
            and next_section_index < len(SECTION_SEQUENCE)
        ):
            current_section = SECTION_SEQUENCE[next_section_index]
            next_section_index += 1
            current_entry = None
            continue

        if current_section is None:
            continue

        if current_section == "skills":
            data["skills"].append(text)
            continue

        if NUMBERED_ENTRY_RE.match(text):
            current_entry = parse_entry_line(text, current_section)
            data[current_section].append(current_entry)
            continue

        if current_entry is None:
            continue

        bullet_match = BULLET_PREFIX_RE.match(text)
        if bullet_match:
            content = bullet_match.group(1).strip()
            if indent == 0 and content.startswith("title_link:"):
                current_entry["title_link"] = content.split(":", 1)[1].strip()
            else:
                current_entry["bullets"].append({"indent": indent, "text": content})
        else:
            current_entry["bullets"].append({"indent": indent, "text": text})

    return data


def bullet_prefix(indent: int) -> str:
    if indent >= 4:
        return "    - "
    if indent >= 2:
        return "  - "
    return "- "


def render_bullets(items: list[dict]) -> list[str]:
    lines: list[str] = []
    for item in items:
        lines.append(f"{bullet_prefix(item['indent'])}{item['text']}")
    return lines


def render_section(title: str, entries: list[dict]) -> list[str]:
    lines = [f"## {title}", ""]
    for entry in entries:
        heading = entry["title"]
        if entry["title_link"]:
            heading = f"[{heading}]({entry['title_link']})"
        lines.append(f"### {heading}")
        if entry["degree_line"]:
            lines.append(f"- degree_line: {entry['degree_line']}")
        elif entry["subtitle"]:
            lines.append(f"- subtitle: {entry['subtitle']}")
        if entry["date"]:
            lines.append(f"- date: {entry['date']}")
        if entry["title_link"]:
            lines.append(f"- title_link: {entry['title_link']}")
        lines.extend(render_bullets(entry["bullets"]))
        lines.append("")
    return lines


def render_markdown(data: dict) -> str:
    lines = [
        f"# {data['name']}",
        "",
        "## header",
        f"- target_role: {data['target_role']}",
        f"- meta: {data['meta']}",
        "",
    ]
    lines.extend(render_section("education", data["education"]))
    lines.extend(render_section("experience", data["experience"]))
    lines.extend(render_section("projects", data["projects"]))
    lines.extend(render_section("campus", data["campus"]))
    lines.append("## skills")
    for skill in data["skills"]:
        lines.append(f"- {skill}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert structured Word resume input into markdown.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    data = parse_docx(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(data), encoding="utf-8")


if __name__ == "__main__":
    main()
