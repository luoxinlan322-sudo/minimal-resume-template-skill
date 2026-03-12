from __future__ import annotations

import sys
from pathlib import Path


TEXT_SUFFIXES = {".md", ".tex", ".cls", ".ps1", ".txt", ".yaml", ".yml"}


def normalize(path: Path) -> None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return
    text = path.read_text(encoding="utf-8-sig")
    path.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    for raw in argv[1:]:
        path = Path(raw)
        if path.is_file():
            normalize(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

