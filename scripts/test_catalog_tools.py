#!/usr/bin/env python3
"""Smoke-test catalog tools against a real Trino/Dune warehouse.

Renders each tool's template.py with small, cheap sample inputs (short
lookback windows, narrow date ranges) and runs the resulting SQL, wrapped
in an outer `limit` so even an unfiltered/full-table-scan query only pulls
back a handful of rows. This is a correctness smoke test, not a load test —
keep it slim so it's safe to run against production Dune credentials.

Requires the `trino` package (not a core dependency of this repo):
    pip install trino

Credentials are read from the environment, never hardcoded here:
    TRINO_HOST, TRINO_PORT, TRINO_CATALOG, TRINO_USER, TRINO_PASSWORD

Usage:
    TRINO_HOST=... TRINO_PORT=443 TRINO_CATALOG=delta_prod \\
    TRINO_USER=dune TRINO_PASSWORD=... \\
    python3 scripts/test_catalog_tools.py --prefix price
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "loaders" / "python"))

from sandworm_tools.loader import load_tools  # noqa: E402
from sandworm_tools.models import Tool, ToolInput  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent
CATALOG_DIR = REPO_ROOT / "catalog"

REAL_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # WETH
SLIM_LOOKBACK = "3"  # small window: keeps test queries cheap regardless of a tool's own default

# Fields whose sample value matters for correctness (a made-up symbol/address
# would just return zero rows, not exercise the query), keyed by input key.
KEY_OVERRIDES = {
    "token_symbol": "ETH",
    "token1": "ETH",
    "token2": "ETH",
    "token2_sym": "ETH",
    "token_a_symbol": "WETH",
    "token_b_symbol": "USDC",
    "portfolio_symbol": "BTC",
    "token_symbols": "BTC,ETH,USDC",
    "symbols": "BTC,ETH,USDC",
    "weights": "0.5,0.3,0.2",
    "pool_address": REAL_ADDRESS,
    "oracle_address": REAL_ADDRESS,
    "token1_addr": REAL_ADDRESS,
    "schema_uid": "0x57fe1f84e9960b144b245c4f381eaa29eaee11884effdc2f1dcd640d0332e8db",
    "schema_uids": "0x57fe1f84e9960b144b245c4f381eaa29eaee11884effdc2f1dcd640d0332e8db",
}

# Keys that mean "how far back to scan" — force these small no matter what
# the tool's own default is, so an unfiltered full-universe query stays cheap.
LOOKBACK_KEYS = {"lookback_days", "lookback_hours", "window", "window_days", "number_of_days", "ma_long", "ma_short"}


def sample_value(inp: ToolInput) -> str:
    if inp.key in KEY_OVERRIDES:
        return KEY_OVERRIDES[inp.key]
    if inp.key in LOOKBACK_KEYS:
        return SLIM_LOOKBACK
    if inp.type == "chain":
        return str(inp.default) if inp.default else "ethereum"
    if inp.type == "chain[]":
        return "ethereum"
    if inp.type == "address":
        return REAL_ADDRESS
    if inp.type == "date":
        return "2024-06-01"
    if inp.type == "date_range":
        return json.dumps({"from": "2024-06-01", "to": "2024-06-04"})
    if inp.type == "number":
        return str(inp.default) if inp.default not in (None, "") else SLIM_LOOKBACK
    if inp.type == "select":
        if inp.default:
            return str(inp.default)
        return inp.options[0].value if inp.options else ""
    if inp.type == "text":
        if inp.default not in (None, ""):
            return str(inp.default)
        return "ETH" if inp.required else ""
    return str(inp.default) if inp.default is not None else ""


def render_sql(tool: Tool) -> str:
    """Substitute placeholders and extract just the `sql` assignment,
    dropping any chart/rendering code — that's presentation, not correctness."""
    src = tool.template
    src = src.replace("{{__tool_name}}", tool.g3 or tool.tool_id)
    src = src.replace("{{__df_name}}", "df")
    for inp in tool.inputs:
        # Triple-quote the substitution: values that are themselves JSON
        # (date_range) contain double quotes that would otherwise break a
        # "{{key}}"-style literal in the template.
        src = src.replace("{{" + inp.key + "}}", sample_value(inp))

    marker = "df = _sandworm_query(sql)"
    idx = src.find(marker)
    if idx == -1:
        raise RuntimeError("could not find `df = _sandworm_query(sql)` in template")

    ns: dict = {}
    exec(src[:idx], ns)  # noqa: S102 - trusted, repo-local templates only
    return ns["sql"]


def run_query(sql: str, conn_kwargs: dict, limit_rows: int) -> None:
    import trino
    from trino.dbapi import connect

    wrapped = f"select * from (\n{sql}\n) t limit {limit_rows}"
    conn = connect(
        auth=trino.auth.BasicAuthentication(conn_kwargs["user"], conn_kwargs.pop("password")),
        **conn_kwargs,
    )
    try:
        cur = conn.cursor()
        cur.execute(wrapped)
        cur.fetchmany(limit_rows)
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--prefix", default="", help="only test tools whose tool_id starts with this (e.g. 'price')")
    parser.add_argument("--limit-rows", type=int, default=3, help="rows to fetch per query (keep this small)")
    args = parser.parse_args()

    try:
        import trino  # noqa: F401
    except ImportError:
        print("Missing dependency: pip install trino", file=sys.stderr)
        return 2

    required_env = ["TRINO_HOST", "TRINO_PORT", "TRINO_CATALOG", "TRINO_USER", "TRINO_PASSWORD"]
    missing = [k for k in required_env if not os.environ.get(k)]
    if missing:
        print(f"Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        return 2

    conn_kwargs = {
        "host": os.environ["TRINO_HOST"],
        "port": int(os.environ["TRINO_PORT"]),
        "catalog": os.environ["TRINO_CATALOG"],
        "user": os.environ["TRINO_USER"],
        "password": os.environ["TRINO_PASSWORD"],
        "http_scheme": os.environ.get("TRINO_HTTP_SCHEME", "https"),
    }

    tools = [t for t in load_tools(CATALOG_DIR) if t.tool_id.startswith(args.prefix)]
    if not tools:
        print(f"No tools matched prefix {args.prefix!r}", file=sys.stderr)
        return 2

    results: list[tuple[str, bool, str]] = []
    for tool in tools:
        try:
            sql = render_sql(tool)
            run_query(sql, dict(conn_kwargs), args.limit_rows)
            results.append((tool.tool_id, True, ""))
        except Exception as e:  # noqa: BLE001 - report every failure, don't let one stop the run
            results.append((tool.tool_id, False, f"{type(e).__name__}: {e}"))

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} passed\n")
    for tool_id, ok, _ in results:
        if ok:
            print(f"PASS  {tool_id}")
    for tool_id, ok, err in results:
        if not ok:
            print(f"FAIL  {tool_id}: {err.splitlines()[0][:300]}")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
