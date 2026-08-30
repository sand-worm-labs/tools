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
  - key: protocol
    label: Protocol
    type: select
    required: true
    options:
      - label: Uniswap
        value: uniswap
      - label: 1inch
        value: 1inch
    default: uniswap
  - key: lookback_days
    label: Lookback (days)
    type: number
    required: false
    min: 1
    max: 365
    default: 30
    placeholder: "30"
    description: How many days back to look.
```

`inputs[].type` must be one of the types the loaders/frontend actually
render — see `loaders/typescript/src/types.ts`'s `ParamType`. CI will fail
the PR otherwise.

`options` (for `select` / `chain` / `chain[]`), `min`/`max` (for `number`),
`placeholder`, and `description` are all optional — omit them and the field
renders with no fixed choices / no bounds / no hint, same as before this was
added.

## Consumers

- `apps/ai` (Qdrant-backed semantic tool search) and `apps/api` (Postgres-backed
  Power Toolbox catalog) in the `sandworm-web` monorepo both fetch this repo's
  catalog live over HTTP on every boot (a tarball of `main`, parsed in memory)
  and seed on startup, skipping if already seeded.
