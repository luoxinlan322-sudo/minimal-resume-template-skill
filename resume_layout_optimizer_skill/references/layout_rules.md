# Layout Rules

## Goal Order

1. Keep the resume to one page unless the user explicitly asks for more.
2. Avoid changing global template spacing before trying local wording compression.
3. Prefer fixing the exact bullet that causes overflow or awkward wrapping.
4. Keep visual rhythm balanced across sections.

## What The Analyzer Flags

- `overflow`: PDF page count exceeds target.
- `sparse_page`: page bottom whitespace is large.
- `dense_page`: page is too close to the bottom.
- `long_bullet`: a bullet uses many visual lines.
- `short_tail`: the last line of a bullet is much shorter than the available width.

## Recommended Fix Order

### Too full

1. Shorten the flagged bullet by a few characters without dropping meaning.
2. Merge repetitive phrases within the same bullet.
3. Tighten local list spacing in `resume.cls`.
4. Only then consider global line-height or margin changes.

### Too sparse

1. Restore wording that was over-compressed.
2. Slightly relax section/list spacing in `resume.cls`.
3. Only then consider small font-size changes.

## Practical Interpretation

- A `short_tail` warning usually means a bullet is close to dropping one line if a few characters are removed.
- A `long_bullet` warning usually means the bullet should be simplified before changing template spacing.
- If multiple bullets in the same section are flagged, fix the longest one first.
- Prefer patching only the flagged `\item` lines before touching section spacing or font size.
- Let the script generate tasks; let the agent decide the actual rewrite wording.
