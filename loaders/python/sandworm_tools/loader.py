from __future__ import annotations

import logging
from pathlib import Path

import yaml

from .models import Category, Tool

log = logging.getLogger("sandworm_tools.loader")


def load_tools(catalog_dir: Path) -> list[Tool]:
    """Load every tool file under catalog_dir (expects <category>/<tool_id>.yaml).

    Skips and logs a warning on any file that fails to parse or validate,
    rather than failing the whole load — one bad tool shouldn't take the
    rest of the catalog down.
    """
    tools: list[Tool] = []
    for path in sorted(catalog_dir.glob("*/*.yaml")):
        try:
            data = yaml.safe_load(path.read_text())
            tools.append(Tool(**data))
        except Exception as e:
            log.warning("skipping %s: %s", path, e)
    return tools


def load_categories(categories_path: Path) -> list[Category]:
    data = yaml.safe_load(categories_path.read_text()) or []
    return [Category(**entry) for entry in data]
