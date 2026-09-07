#!/usr/bin/env python3
"""One-off: move every catalog/<category>/<tool_id>.yaml into its own
catalog/<category>/<name>/tool.yaml (folder named after the part of
tool_id after the category dot, since the category is already the
parent directory), and give it a sibling template.py placeholder that
just prints back whatever params it's called with.

Lets the pick-tool -> fill-inputs -> run -> see-a-result pipeline be
tested end-to-end before real per-tool Python/SQL logic is written.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CATALOG_DIR = Path(__file__).parent.parent / "catalog"


def build_template(inputs: list[dict]) -> str:
    lines = ["params = {"]
    for i in inputs:
        key = i["key"]
        lines.append(f'    "{key}": "{{{{{key}}}}}",')
    lines.append("}")
    lines.append("print(params)")
    return "\n".join(lines) + "\n"


def main() -> None:
    paths = sorted(CATALOG_DIR.glob("*/*.yaml"))
    for path in paths:
        data = yaml.safe_load(path.read_text())
        _category, name = data["tool_id"].split(".", 1)
        tool_dir = path.parent / name
        tool_dir.mkdir()

        (tool_dir / "tool.yaml").write_text(path.read_text())
        (tool_dir / "template.py").write_text(build_template(data.get("inputs", [])))

        path.unlink()

    print(f"migrated {len(paths)} tool files")


if __name__ == "__main__":
    main()
