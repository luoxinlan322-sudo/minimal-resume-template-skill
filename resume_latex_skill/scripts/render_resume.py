from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "input_templates" / "resume_input_template.md"
DEFAULT_OUTPUT = ROOT / "template" / "main.tex"
TITLE_LINK_RE = re.compile(r"^\[(.+?)\]\((.+?)\)$")
BULLET_RE = re.compile(r"^(\s*)[-+*\u2022]\s+(.*)$")


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def read_text(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig").splitlines()


def init_entry(title: str, title_link: str = "") -> dict:
    return {
        "title": title,
        "title_link": title_link,
        "subtitle": "",
        "date": "",
        "degree_line": "",
        "bullets": [],
        "_bullet_stack": [],
    }


def parse_heading_title(text: str) -> tuple[str, str]:
    match = TITLE_LINK_RE.match(text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return text, ""


def add_bullet(entry: dict, indent: int, text: str) -> None:
    node = {"text": text, "children": []}
    stack = entry["_bullet_stack"]

    while stack and indent <= stack[-1][0]:
        stack.pop()

    if stack:
        stack[-1][1]["children"].append(node)
    else:
        entry["bullets"].append(node)

    stack.append((indent, node))


def parse_markdown(lines: list[str]) -> dict:
    data = {
        "name": "",
        "sections": {
            "header": [],
            "education": [],
            "experience": [],
            "projects": [],
            "campus": [],
            "skills": [],
        },
    }

    current_section = None
    current_entry = None

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if line.startswith("# "):
            data["name"] = line[2:].strip()
            continue

        if line.startswith("## "):
            current_section = line[3:].strip().lower()
            if current_section not in data["sections"]:
                current_section = None
            current_entry = None
            continue

        if current_section is None:
            continue

        if line.startswith("### "):
            title, title_link = parse_heading_title(line[4:].strip())
            current_entry = init_entry(title, title_link)
            data["sections"][current_section].append(current_entry)
            continue

        bullet_match = BULLET_RE.match(raw)
        if bullet_match:
            indent = len(bullet_match.group(1).replace("\t", "  "))
            content = bullet_match.group(2).strip()

            if current_section == "header":
                data["sections"]["header"].append(content)
                continue

            if current_section == "skills":
                data["sections"]["skills"].append(content)
                continue

            if current_entry is None:
                continue

            if indent == 0 and content.startswith("subtitle:"):
                current_entry["subtitle"] = content.split(":", 1)[1].strip()
            elif indent == 0 and content.startswith("date:"):
                current_entry["date"] = content.split(":", 1)[1].strip()
            elif indent == 0 and content.startswith("degree_line:"):
                current_entry["degree_line"] = content.split(":", 1)[1].strip()
            elif indent == 0 and content.startswith("title_link:"):
                current_entry["title_link"] = content.split(":", 1)[1].strip()
            else:
                add_bullet(current_entry, indent, content)

    for section in data["sections"].values():
        for entry in section:
            if isinstance(entry, dict) and "_bullet_stack" in entry:
                entry.pop("_bullet_stack", None)

    return data


def header_value(header_lines: list[str], key: str, default: str = "") -> str:
    prefix = f"{key}:"
    for line in header_lines:
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return default


def render_header(data: dict) -> str:
    header_lines = data["sections"]["header"]
    name = latex_escape(data["name"] or "你的姓名")
    role = latex_escape(header_value(header_lines, "target_role", "目标岗位"))
    meta = latex_escape(header_value(header_lines, "meta", "手机号 | 邮箱 | GitHub | 其他信息"))
    return rf"""\ResumeName{{{name}}}

% Header
\usepackage{{graphicx}}
\usepackage{{tikz}}

\begin{{document}}

\begin{{minipage}}[c]{{0.76\textwidth}}
  \raggedright
  \setlength{{\parindent}}{{0pt}}
  
  \ResumeHeaderName{{{name}}}\par
  \ResumeHeaderStackGap
  \ResumeHeaderIntent{{求职意向：{role}}}\par
  \ResumeHeaderStackGap
  \ResumeHeaderMeta{{
  {meta}
  }}
\end{{minipage}}%
\hfill
\begin{{minipage}}[c]{{0.16\textwidth}}
  \centering
  \begin{{tikzpicture}}
    \clip (0,0) circle (1.12cm);
    \node[inner sep=0pt] at (0,0)
      {{\includegraphics[width=2.55cm]{{profile_placeholder.png}}}};
\end{{tikzpicture}}
\end{{minipage}}

\ResumeHeaderBodyGap

\small"""


def render_title(title: str, title_link: str = "") -> str:
    escaped_title = latex_escape(title)
    if title_link:
        return rf"\ResumeUrl{{{latex_escape(title_link)}}}{{{escaped_title}}}"
    return escaped_title


def render_bullet_nodes(nodes: list[dict], top_env: str, indent: str = "") -> str:
    lines = [f"{indent}\\begin{{{top_env}}}"]
    for node in nodes:
        lines.append(f"{indent}  \\item {latex_escape(node['text'])}")
        if node["children"]:
            lines.append(render_bullet_nodes(node["children"], "itemize", indent + "    "))
    lines.append(f"{indent}\\end{{{top_env}}}")
    return "\n".join(lines)


def render_edu_item(entry: dict) -> str:
    title = latex_escape(entry["title"])
    degree_line = latex_escape(entry["degree_line"])
    date = latex_escape(entry["date"])
    return rf"""\ResumeEduItem[{title}]
  {{{title}}}
  [{degree_line}]
  [{date}]

{render_bullet_nodes(entry["bullets"], "ResumeCompactList")}"""


def render_item(entry: dict, env: str = "ResumeCompactList") -> str:
    title = render_title(entry["title"], entry.get("title_link", ""))
    title_bookmark = latex_escape(entry["title"])
    subtitle = latex_escape(entry["subtitle"])
    date = latex_escape(entry["date"])
    return rf"""\ResumeItem[{title_bookmark}]
  {{{title}}}
  [{subtitle}]
  [{date}]

{render_bullet_nodes(entry["bullets"], env)}"""


def render_section(title: str, body: list[str]) -> str:
    if not body:
        return ""
    return "\\section{" + latex_escape(title) + "}\n\n" + "\n\n".join(body)


def render_skills(lines: list[str]) -> str:
    skill_lines = [line.strip() for line in lines if line.strip()]
    if not skill_lines:
        return ""
    bullets = "\n".join(f"  \\item {latex_escape(line)}" for line in skill_lines)
    return rf"""\section{{技能}}

\begin{{itemize}}
{bullets}
\end{{itemize}}"""


def build_tex(data: dict) -> str:
    education = render_section(
        "教育经历",
        [render_edu_item(entry) for entry in data["sections"]["education"]],
    )
    experience = render_section(
        "工作经历",
        [render_item(entry) for entry in data["sections"]["experience"]],
    )
    projects = render_section(
        "项目经历",
        [render_item(entry, env="itemize") for entry in data["sections"]["projects"]],
    )
    campus = render_section(
        "校园经历",
        [render_item(entry) for entry in data["sections"]["campus"]],
    )
    skills = render_skills(data["sections"]["skills"])

    parts = [
        "% !TeX TS-program = xelatex",
        "",
        r"\documentclass{resume}",
        render_header(data),
        education,
        experience,
        projects,
        campus,
        skills,
        "",
        r"\end{document}",
        "",
    ]
    return "\n".join(part for part in parts if part)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render structured markdown into the resume LaTeX template.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to the markdown source file.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to the generated TeX file.")
    args = parser.parse_args()

    lines = read_text(args.input)
    data = parse_markdown(lines)
    tex = build_tex(data)
    args.output.write_text(tex, encoding="utf-8")


if __name__ == "__main__":
    main()
