# Sandworm Power Toolbox — {{__tool_name}}
# Trino has no WITH RECURSIVE, so levels are unrolled explicitly as a fixed
# chain of CTEs (capped at 5 to keep the join fan-out bounded).
import re

WALLET_ADDRESS = "{{wallet_address}}"
CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
MAX_LEVELS = "{{max_levels}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
MAX_LEVELS_CAP = 5

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if MAX_LEVELS and not (MAX_LEVELS.isdigit() and int(MAX_LEVELS) > 0):
    raise ValueError(f"Invalid max_levels: {MAX_LEVELS!r}")

wallet_hex = WALLET_ADDRESS[2:].lower()
contract_hex = CONTRACT_ADDRESS[2:].lower()
levels = min(int(MAX_LEVELS) if MAX_LEVELS else 5, MAX_LEVELS_CAP)

ctes = []
for lvl in range(1, levels + 1):
    if lvl == 1:
        source_filter = f"\"from\" = from_hex('{wallet_hex}')"
    else:
        source_filter = f"\"from\" in (select \"to\" from level_{lvl - 1})"
    ctes.append(
        f"level_{lvl} as (\n"
        f"    select {lvl} as level, \"from\", \"to\", amount as value\n"
        f"    from tokens.transfers\n"
        f"    where blockchain = '{CHAIN}'\n"
        f"      and token_standard = 'erc20'\n"
        f"      and contract_address = from_hex('{contract_hex}')\n"
        f"      and {source_filter}\n"
        f")"
    )
cte_sql = ",\n".join(ctes)
union_sql = "\nunion all\n".join(
    f'select level, to_hex("from") as "from", to_hex("to") as "to", value from level_{lvl}'
    for lvl in range(1, levels + 1)
)

sql = f"""
with {cte_sql}
select * from (
{union_sql}
) t
order by level, value desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
