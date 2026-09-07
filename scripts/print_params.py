#!/usr/bin/env python3
"""Print every tool's params (inputs) from the catalog.

This repo only holds tool *definitions* — the actual Python/SQL
implementations live in the consuming apps. This is a template for
walking the whole catalog; for now it just prints each tool's params.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "loaders" / "python"))

from sandworm_tools.loader import load_tools  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent
CATALOG_DIR = REPO_ROOT / "catalog"


def main() -> None:
    for tool in load_tools(CATALOG_DIR):
        print(f"{tool.tool_id} ({tool.g1})")
        for param in tool.inputs:
            print(f"  {param.key}: {param.type} required={param.required} default={param.default!r}")


if __name__ == "__main__":
    main()
