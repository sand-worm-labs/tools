import { globSync, readFileSync } from "fs";

import { load } from "js-yaml";

import type { Category, Tool } from "./types";

/**
 * Load every tool file under catalogDir (expects <category>/<tool_id>.yaml).
 * Skips and logs a warning on any file that fails to parse, rather than
 * failing the whole load — one bad tool shouldn't take the rest down.
 */
export function loadTools(catalogDir: string): Tool[] {
  const files = globSync(`${catalogDir}/*/*.yaml`);
  const tools: Tool[] = [];

  for (const file of files) {
    try {
      tools.push(load(readFileSync(file, "utf-8")) as Tool);
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
