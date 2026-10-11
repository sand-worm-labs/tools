from __future__ import annotations

import logging
from pathlib import Path

import yaml

from .models import Category, Tool

log = logging.getLogger("sandworm_tools.loader")


def load_tools(catalog_dir: Path, include_unimplemented: bool = False) -> list[Tool]:
    """Load every tool under catalog_dir (expects <category>/<tool_id>/tool.yaml,
    with the tool's Python/SQL source alongside it in template.py).

    Skips and logs a warning on any tool that fails to parse or validate,
    rather than failing the whole load — one bad tool shouldn't take the
    rest of the catalog down.

    Tools marked `implemented: false` (stub templates) are left out unless
    include_unimplemented is True.
    """
    tools: list[Tool] = []
    for path in sorted(catalog_dir.glob("*/*/tool.yaml")):
        try:
            data = yaml.safe_load(path.read_text())
            data["template"] = (path.parent / "template.py").read_text()
            tool = Tool(**data)
            if tool.implemented or include_unimplemented:
                tools.append(tool)
        except Exception as e:
            log.warning("skipping %s: %s", path, e)
    return tools


def load_categories(categories_path: Path) -> list[Category]:
    data = yaml.safe_load(categories_path.read_text()) or []
    return [Category(**entry) for entry in data]
