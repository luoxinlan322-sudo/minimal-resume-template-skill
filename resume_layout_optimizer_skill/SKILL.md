---
name: resume-layout-optimizer
description: Diagnose and optimize LaTeX resume layout after compilation. Use this when the user wants to make a resume fit one page, identify which bullet occupies too many lines, reduce only a few Chinese characters without losing meaning, detect short-tail lines, or tune spacing/font rhythm in a fixed resume template.
---

# Resume Layout Optimizer

Use this skill after a resume PDF already exists, or when the user explicitly asks to optimize layout only.

## Workflow

1. Make sure the resume has been compiled to PDF.
Prefer `../resume_latex_skill/scripts/compile_resume.ps1` if the PDF is missing or stale.

2. Run layout diagnosis.
Run `scripts/analyze_layout.py`.
This writes both `layout_diagnosis.json` and `layout_tasks.json`.
Use `scripts/optimize_layout.py` only as a deterministic fallback when unattended auto-compression is acceptable.
Default target is `main.pdf` in the current output directory.

3. Read the task file first.
Open `layout_tasks.json`.
Patch only the flagged bullets in `main.tex`.
Do not rewrite unaffected bullets.

4. Read the diagnosis report.
Prioritize:
- page count overflow
- bullets with too many lines
- bullets whose last line is very short
- pages that are visually too sparse or too dense

5. Apply fixes in this order.
- Compress the specific bullet text first
- If necessary, tighten local list rhythm in `resume.cls`
- Change global spacing only after local fixes are exhausted
- Avoid changing `main.tex` spacing unless the template cannot express the fix

6. Recompile and re-check.
Run `scripts/recheck_layout.ps1` after edits.
This recompiles the resume and refreshes both diagnosis and task files.

## Inputs

- PDF: `main.pdf`
- TeX target: `main.tex`
- Class file: `resume.cls`

## Script

- `scripts/analyze_layout.py`
- `scripts/recheck_layout.ps1`
- `scripts/optimize_layout.py`

## Reference

- `references/layout_rules.md`
