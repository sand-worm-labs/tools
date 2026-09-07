import { globSync, readFileSync } from "fs";
import { dirname, join } from "path";

import { load } from "js-yaml";

import type { Category, Tool } from "./types";

/**
 * Load every tool under catalogDir (expects <category>/<tool_id>/tool.yaml,
 * with the tool's Python/SQL source alongside it in template.py).
 * Skips and logs a warning on any tool that fails to parse, rather than
 * failing the whole load — one bad tool shouldn't take the rest down.
 */
export function loadTools(catalogDir: string): Tool[] {
  const files = globSync(`${catalogDir}/*/*/tool.yaml`);
  const tools: Tool[] = [];

  for (const file of files) {
    try {
      const tool = load(readFileSync(file, "utf-8")) as Tool;
      tool.template = readFileSync(join(dirname(file), "template.py"), "utf-8");
      tools.push(tool);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn(`[sandworm-tools] skipping ${file}: ${(err as Error).message}`);
    }
  }

  return tools;
}

export function loadCategories(categoriesPath: string): Category[] {
  return (load(readFileSync(categoriesPath, "utf-8")) as Category[]) ?? [];
}
