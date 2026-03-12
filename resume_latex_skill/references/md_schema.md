# Markdown To TeX Schema

This schema is the preferred input format for resume generation.

## Required Sections

1. `header`
2. `education`
3. `experience`
4. `projects`
5. `campus`
6. `skills`

## Markdown Structure

Use the following heading levels:

- `#` candidate name or document title
- `##` section name
- `###` entry title
- flat bullet lists for entry details

## Recommended Field Model

### header

- `name`
- `target_role`
- `meta`
  Example: phone, email, GitHub, political status, city

### education item

- `school`
- `degree_line`
  Example: `计算机科学与技术专业 工学学士`
- `date`
- `bullets`

### experience / project / campus item

- `title`
- `title_link` (optional)
- `subtitle`
- `date`
- `bullets`

Each item should contain `2-5` bullets.
Each bullet should be one complete sentence or phrase block.
Nested bullets are supported with indentation.

### skills

Group into `2-4` labeled lines.
Preferred labels:

- `产品能力`
- `AI 应用`
- `工具与表达`

## Mapping Rules

- `school` -> `\ResumeEduItem` title
- `degree_line` -> subtitle field of `\ResumeEduItem`
- `date` -> right-aligned date field
- `title` + `subtitle` + `date` -> `\ResumeItem`
- `title_link` -> clickable linked title rendered with `\ResumeUrl`
- `bullets` -> `itemize` or `ResumeCompactList`

## Writing Constraints

- Nested bullets are allowed. Use indentation with `-` items.
- Avoid tables in source markdown.
- Keep dates in one consistent style.
- Keep metrics explicit if available.
- If metrics are unknown, use placeholders rather than invented numbers.

## Minimal Example

```md
# 张三

## header
- target_role: AI 产品经理
- meta: 138-0000-0000 | name@example.com | GitHub

## education
### 示例大学
- degree_line: XX专业 工学学士
- date: 20XX.XX -- 20XX.XX
- GPA：X.X/X.X（排名X/X）。
- 获校级奖学金并参与科研训练。

## experience
### 某头部互联网公司
- subtitle: AI 产品实习生
- date: 20XX.XX -- 20XX.XX
- title_link: https://example.com/experience-a
- 参与需求分析与版本规划。
- 协同设计与开发推进方案落地。
  - 补充一层说明。
```
