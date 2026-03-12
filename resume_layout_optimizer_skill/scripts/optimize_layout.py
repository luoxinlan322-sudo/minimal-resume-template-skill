from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEX = ROOT / "template" / "main.tex"
DEFAULT_PDF = ROOT / "template" / "main.pdf"
DEFAULT_DIAGNOSIS = ROOT / "template" / "layout_diagnosis.json"
DEFAULT_REPORT = ROOT / "template" / "layout_optimization_report.json"
ANALYZE_SCRIPT = Path(__file__).with_name("analyze_layout.py")
COMPILE_SCRIPT = ROOT / "resume_latex_skill" / "scripts" / "compile_resume.ps1"

SHRINK_RULES = [
    ("以及", "及"),
    ("并且", "并"),
    ("可以", "可"),
    ("能够", "能"),
    ("对于", "对"),
    ("如果", "若"),
    ("目前", ""),
    ("已经", "已"),
    ("进行", ""),
    ("进一步", ""),
    ("相关", ""),
    ("其中", ""),
    ("阶段性", "阶段"),
    ("整体", ""),
    ("持续", ""),
]


@dataclass
class OptimizationResult:
    bullet_index: int
    target_trim: int
    removed_chars: int
    before: str
    after: str


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)


def diagnose(pdf_path: Path, diagnosis_path: Path) -> dict:
    run(["python", str(ANALYZE_SCRIPT), "--pdf", str(pdf_path), "--json-output", str(diagnosis_path)])
    return json.loads(diagnosis_path.read_text(encoding="utf-8"))


def compile_resume() -> None:
    run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(COMPILE_SCRIPT)])


def item_line_indices(lines: list[str]) -> list[int]:
    return [idx for idx, line in enumerate(lines) if re.match(r"^\s*\\item\s+", line)]


def count_visible_chars(text: str) -> int:
    return len(text.replace(" ", ""))


def cleanup_spacing(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s*([，。；：、）])", r"\1", text)
    text = re.sub(r"([（])\s*", r"\1", text)
    text = re.sub(r"\s*([,.!?;:])", r"\1", text)
    text = re.sub(r"([A-Za-z0-9])\s+([A-Za-z0-9])", r"\1 \2", text)
    text = re.sub(r"([\u4e00-\u9fff])\s+([A-Za-z0-9])", r"\1\2", text)
    text = re.sub(r"([A-Za-z0-9])\s+([\u4e00-\u9fff])", r"\1\2", text)
    return text


def shrink_text(text: str, target_trim: int) -> tuple[str, int]:
    original = text
    working = cleanup_spacing(text)
    removed = count_visible_chars(original) - count_visible_chars(working)

    for old, new in SHRINK_RULES:
        if removed >= target_trim:
            break
        while old in working and removed < target_trim:
            candidate = working.replace(old, new, 1)
            delta = count_visible_chars(working) - count_visible_chars(candidate)
            if delta <= 0:
                break
            working = candidate
            removed += delta

    if removed < target_trim:
        candidate = re.sub(r"(的|地|得)(?=[，。；、])", "", working)
        delta = count_visible_chars(working) - count_visible_chars(candidate)
        if delta > 0:
            working = candidate
            removed += delta

    working = cleanup_spacing(working)
    removed = count_visible_chars(original) - count_visible_chars(working)
    return working, removed


def optimize_tex(tex_path: Path, diagnosis: dict) -> list[OptimizationResult]:
    lines = tex_path.read_text(encoding="utf-8").splitlines()
    item_indices = item_line_indices(lines)
    results: list[OptimizationResult] = []

    flagged = [
        item
        for item in diagnosis.get("bullets", [])
        if item.get("warnings") and item.get("suggested_trim_chars", 0) > 0
    ]
    flagged.sort(key=lambda item: (item["suggested_trim_chars"], item["line_count"]), reverse=True)

    for item in flagged:
        bullet_index = item["bullet_index"]
        if bullet_index >= len(item_indices):
            continue
        line_idx = item_indices[bullet_index]
        line = lines[line_idx]
        prefix, body = re.match(r"^(\s*\\item\s+)(.*)$", line).groups()
        optimized, removed = shrink_text(body, item["suggested_trim_chars"])
        if removed <= 0 or optimized == body:
            continue
        lines[line_idx] = prefix + optimized
        results.append(
            OptimizationResult(
                bullet_index=bullet_index,
                target_trim=item["suggested_trim_chars"],
                removed_chars=removed,
                before=body,
                after=optimized,
            )
        )

    if results:
        tex_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize only the flagged resume bullets, then recompile and re-check.")
    parser.add_argument("--tex", type=Path, default=DEFAULT_TEX, help="Rendered TeX file to patch.")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF, help="Compiled PDF file.")
    parser.add_argument("--diagnosis", type=Path, default=DEFAULT_DIAGNOSIS, help="Diagnosis JSON path.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Optimization report JSON path.")
    parser.add_argument("--max-passes", type=int, default=2, help="Maximum optimization passes.")
    args = parser.parse_args()

    history: list[dict] = []

    diagnosis = diagnose(args.pdf, args.diagnosis)

    for pass_index in range(1, args.max_passes + 1):
        changes = optimize_tex(args.tex, diagnosis)
        if not changes:
            history.append({"pass": pass_index, "changes": [], "summary": diagnosis.get("summary", {})})
            break

        compile_resume()
        diagnosis = diagnose(args.pdf, args.diagnosis)
        history.append(
            {
                "pass": pass_index,
                "changes": [
                    {
                        "bullet_index": change.bullet_index,
                        "target_trim": change.target_trim,
                        "removed_chars": change.removed_chars,
                        "before": change.before,
                        "after": change.after,
                    }
                    for change in changes
                ],
                "summary": diagnosis.get("summary", {}),
            }
        )

        if not diagnosis.get("summary", {}).get("overflow") and not diagnosis.get("summary", {}).get("flagged_short_tail"):
            break

    payload = {
        "passes": history,
        "final_summary": diagnosis.get("summary", {}),
        "final_diagnosis": str(args.diagnosis),
    }
    args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Layout optimization")
    print(f"- passes: {len(history)}")
    print(f"- final pages: {payload['final_summary'].get('actual_pages', 0)} / {payload['final_summary'].get('target_pages', 1)}")
    print(f"- final overflow: {'yes' if payload['final_summary'].get('overflow') else 'no'}")
    print(f"- final flagged_short_tail: {payload['final_summary'].get('flagged_short_tail', 0)}")
    print(f"- report: {args.report}")


if __name__ == "__main__":
    main()
