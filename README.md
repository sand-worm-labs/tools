# tools

The Sandworm power-tool catalog — the analytics tools available to notebooks
via the Power Toolbox, and the AI's tool-selection search.

## Layout

- `catalog/<category>/<name>/tool.yaml` — one folder per tool, grouped by
  category (`<name>` is the part of `tool_id` after the `<category>.` prefix,
  since the category is already the parent directory); `tool.yaml` holds
  the metadata.
- `catalog/<category>/<name>/template.py` — the tool's actual Python/SQL
  source, kept in its own file (not inline in the YAML) so it gets real
  syntax highlighting and clean diffs regardless of size. `{{key}}` in the
  source is replaced with whatever the user (or the AI) filled into the
  matching `inputs[].key` before it runs.
- `categories.yaml` — the category taxonomy (single source of truth; every
  tool's `g1` must match a `category_id` here).
- `schema/` — JSON Schema for `tool.yaml` and `categories.yaml`. CI
  (`.github/workflows/validate.yml`) rejects a PR if any catalog file,
  `categories.yaml`, or a missing/empty `template.py` fails validation.
- `loaders/python/sandworm_tools/` — installable pip package (`load_tools`,
  `load_categories`); `load_tools` reads `template.py` in alongside each
  `tool.yaml` and sets it as the `Tool.template` field.
- `loaders/typescript/` — installable npm package (`loadTools`, `loadCategories`),
  same behavior.

## Adding a tool

Add `catalog/defi/example_tool/tool.yaml` (folder name is `tool_id` with the
`defi.` category prefix dropped):

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

and `catalog/defi/example_tool/template.py`, using `{{contract_address}}`,
`{{protocol}}`, `{{lookback_days}}` (one `{{key}}` per `inputs[].key` above)
wherever that input's value belongs.

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
