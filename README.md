# tools

The Sandworm power-tool catalog — the analytics tools available to notebooks
via the Power Toolbox, and the AI's tool-selection search.

## Layout

- `catalog/<category>/<tool_id>.yaml` — one file per tool, grouped by category.
- `categories.yaml` — the category taxonomy (single source of truth; every
  tool's `g1` must match a `category_id` here).
- `schema/` — JSON Schema for both file types. CI (`.github/workflows/validate.yml`)
  rejects a PR if any catalog file or `categories.yaml` fails validation.
- `loaders/python/sandworm_tools/` — installable pip package (`load_tools`,
  `load_categories`).
- `loaders/typescript/` — installable npm package (`loadTools`, `loadCategories`).

## Adding a tool

Add `catalog/<category>/<tool_id>.yaml`:

```yaml
tool_id: defi.example_tool
g1: defi
description: What this tool computes.
scope: generic
returns:
  - name: some_field
    type: string
inputs:
  - key: contract_address
    label: Contract Address
    type: address
    required: true
```

`inputs[].type` must be one of the types the loaders/frontend actually
render — see `loaders/typescript/src/types.ts`'s `ParamType`. CI will fail
the PR otherwise.

## Consumers

- `apps/ai` (Qdrant-backed semantic tool search) and `apps/api` (Postgres-backed
  Power Toolbox catalog) in the `sandworm-web` monorepo both read from a copy
  of this repo and seed on startup, skipping if already seeded.
