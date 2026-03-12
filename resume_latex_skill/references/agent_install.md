# CodeAgent 安装与接入说明

## 适用场景

当需要让 CodeAgent 基于结构化输入自动改写并编译这套中文 LaTeX 简历模板时，可接入本 Skill。

## 建议目录

将以下目录整体放入可被 Agent 读取的位置：

- `resume_latex_skill/`
- `input_templates/`
- `template/`

## 推荐触发方式

在任务中明确说明：

- 使用 `resume-latex-builder`
- 输入文件路径
- 输出目标

示例：

`使用 resume-latex-builder，将 input_templates/resume_input_template.md 中的内容改写进 template/main.tex 并编译。`

如果希望直接跑完整链路，可让 Agent 直接执行：

- `scripts/build_from_md.ps1`
- `scripts/build_from_word.ps1`

## 推荐工作流

1. 读取用户填写的 Markdown 或 Word 转换后的 Markdown
2. 优先直接执行总控脚本
3. 如需拆步，再执行 `scripts/check_env.ps1`
4. 执行 `scripts/normalize_encoding.py`
5. 执行 `scripts/render_resume.py`，按 `references/md_schema.md` 写入 `template/main.tex`
6. 执行 `scripts/compile_resume.ps1`
6. 检查页数、编码和编译结果

## Word 输入建议

- 推荐路径：`Word -> Markdown -> TeX`
- 让用户按 `input_templates/resume_input_template_word.docx` 的结构在 Word 中填写
- 先运行 `scripts/word_to_markdown.py`
- 再将生成的 Markdown 交给 `scripts/render_resume.py`

## 让 Agent 在聊天中可直接使用

有两种方式：

1. 安装成正式 Codex Skill
将 `resume_latex_skill/` 拷贝到 `$CODEX_HOME/skills/resume-latex-builder/`，这样它会出现在可用技能列表中。

2. 作为仓库内工作流使用
在仓库根目录放一份 `AGENTS.md`，明确说明当用户请求“生成/改写/编译简历”时，应读取 `resume_latex_skill/SKILL.md` 并优先执行总控脚本。

如果希望聊天里稳定触发，优先推荐第 1 种。
