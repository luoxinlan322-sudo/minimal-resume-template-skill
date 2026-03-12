---
name: resume-latex-builder
description: Build or rewrite a Chinese LaTeX resume from structured markdown or converted Word content using the bundled one-page template. Use this when the user wants to generate, rewrite, anonymize, validate, or compile a resume under resume_cn_public_template, especially from markdown drafts, resume notes, or Word-to-markdown input.
---

# Resume LaTeX Builder

Use this skill when the task is to turn structured resume content into bundled LaTeX template assets, copy them beside the user's input file when needed, then validate encoding, dependencies, and compile output.

## Workflow

1. Read the input source.
If the input is markdown, follow `references/md_schema.md`.
If the input comes from Word, first normalize it using `references/word_strategy.md`.

2. Validate environment.
Run `scripts/check_env.ps1`.
If `xelatex` is missing, use the install path already defined there.

3. Normalize encoding before edits.
Run `scripts/normalize_encoding.py` on all edited `.md`, `.tex`, `.cls`, and `.ps1` files.

4. Map source fields into the LaTeX template.
Prefer `scripts/render_resume.py`.
Render to `main.tex` in the active output directory.
Keep layout controls in the copied `resume.cls`.
Do not introduce ad hoc spacing in `main.tex` unless template-level control is impossible.

5. Compile serially.
Run `scripts/compile_resume.ps1`.
Never run multiple `xelatex` processes against the same output in parallel.

6. Generate layout tasks.
After compile, run `../resume_layout_optimizer_skill/scripts/analyze_layout.py`.
This will write `layout_tasks.json` in the same output directory.
Use the layout skill directly when the user only wants single-page control, line-count-aware wording compression, spacing tuning, or layout diagnosis.

7. Let the agent patch flagged bullets.
Read `layout_tasks.json` and edit only the targeted bullets in `main.tex`.

8. Verify output.
Run `../resume_layout_optimizer_skill/scripts/recheck_layout.ps1`.
If the resume overflows, use the refreshed task file to continue local wording compression before changing global layout.

## Input Rules

- Prefer markdown input over free-form chat text.
- Prefer `Word -> Markdown -> TeX` over direct `Word -> TeX`.
- Preserve section order from the schema unless the user asks otherwise.
- Replace unsupported or ambiguous content with explicit placeholders instead of guessing.

## Files To Read

- Schema: `references/md_schema.md`
- Word path guidance: `references/word_strategy.md`
- User markdown template: `../input_templates/resume_input_template.md`
- Bundled template assets: `assets/template/`

## Scripts

- Environment check: `scripts/check_env.ps1`
- Encoding normalization: `scripts/normalize_encoding.py`
- Create Word template: `scripts/create_word_template.py`
- Convert Word to markdown: `scripts/word_to_markdown.py`
- Render markdown into TeX: `scripts/render_resume.py`
- Build from markdown end-to-end: `scripts/build_from_md.ps1`
- Build from Word end-to-end: `scripts/build_from_word.ps1`
- Compile: `scripts/compile_resume.ps1`
- Layout diagnosis: `../resume_layout_optimizer_skill/scripts/analyze_layout.py`
- Layout recheck: `../resume_layout_optimizer_skill/scripts/recheck_layout.ps1`
- Layout optimization: `../resume_layout_optimizer_skill/scripts/optimize_layout.py`

## Output Targets

- By default, output files are written beside the input file.
- If that directory does not yet contain template assets, the skill copies them from `assets/template/`.
- Main outputs:
  - `main.tex`
  - `resume.cls`
  - `main.pdf`
  - `layout_diagnosis.json`
  - `layout_tasks.json`
