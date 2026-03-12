# Word To TeX Strategy

## Recommended Path

Prefer:

`Word -> Markdown -> TeX`

Do not default to direct `Word -> TeX` unless the Word document is already highly structured.

## Why

- Markdown is easier to validate and diff.
- Encoding problems are easier to detect.
- Section boundaries become explicit.
- It is easier to compress and rewrite content before templating.

## Suggested Conversion Process

1. Let users fill the bundled Word template.
2. Run `scripts/word_to_markdown.py`.
3. Normalize the generated markdown into the section structure defined in `md_schema.md`.
4. Then render into `main.tex`.

## Direct Word To TeX

Possible, but not the preferred first implementation.

Risks:

- field extraction is brittle
- hidden formatting pollutes content
- layout semantics are unclear
- encoding and punctuation inconsistencies are harder to fix

## Recommendation For Users

- Give users a `.md` template first
- If Word input is needed, let them fill the bundled `.docx` template that mirrors the markdown schema
- Then convert that Word file into markdown before final rendering
