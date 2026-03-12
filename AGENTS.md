# Resume Template Agent Guide

When the user asks to generate, rewrite, anonymize, or compile a resume in this repository, use:

- `resume_latex_skill/SKILL.md`
- `resume_layout_optimizer_skill/SKILL.md` when the request is only about layout diagnosis, single-page fitting, line-count-aware wording reduction, or spacing tuning

## Preferred workflow

1. If the input is markdown, prefer:
   - `resume_latex_skill/scripts/build_from_md.ps1`
2. If the input is Word, prefer:
   - `resume_latex_skill/scripts/build_from_word.ps1`
3. After compile, run:
   - `resume_layout_optimizer_skill/scripts/analyze_layout.py`
4. Read:
   - `template/layout_tasks.json`
   and patch only the flagged bullets in `template/main.tex`
5. After edits, run:
   - `resume_layout_optimizer_skill/scripts/recheck_layout.ps1`
6. Keep layout logic in:
   - `template/resume.cls`
7. Treat:
   - `template/main.tex`
   as the render target, not the primary authoring surface

## Input files

- Markdown template:
  - `input_templates/resume_input_template.md`
- Word template:
  - `input_templates/resume_input_template_word.docx`

## Safety rules

- Normalize edited text files to UTF-8 before compilation.
- Compile serially only. Do not run multiple `xelatex` processes against the same output in parallel.
- If content overflows, compress wording before changing template spacing.
- Prefer fixing the exact flagged bullet before changing global layout spacing.
- Do not invent metrics or missing experience details.

## Output target

- Final PDF:
  - `template/main.pdf`
