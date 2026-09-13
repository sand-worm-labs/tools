# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
START_WALLET = "{{start_wallet}}"
TARGET_CONTRACT = "{{target_contract}}"
MAX_HOPS = "{{max_hops}}"

CHAIN_SCHEMA = {
    "ethereum": "ethereum",
    "base": "base",
    "optimism": "optimism",
    "arbitrum": "arbitrum",
    "polygon": "polygon",
    "bsc": "bnb",
    "avalanche": "avalanche_c",
    "celo": "celo",
}
ALLOWED_CHAINS = set(CHAIN_SCHEMA)
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(START_WALLET):
    raise ValueError(f"Invalid start_wallet: {START_WALLET!r}")
if not ADDRESS_RE.match(TARGET_CONTRACT):
    raise ValueError(f"Invalid target_contract: {TARGET_CONTRACT!r}")
if not MAX_HOPS.isdigit() or not (0 < int(MAX_HOPS) <= 10):
    raise ValueError(f"Invalid max_hops: {MAX_HOPS!r}")

schema = CHAIN_SCHEMA[CHAIN]
start_hex = START_WALLET[2:].lower()
target_hex = TARGET_CONTRACT[2:].lower()
max_hops = int(MAX_HOPS)

# Trino has no WITH RECURSIVE support here, so each hop is unrolled as its
# own CTE, self-joining onto the previous hop's "to" address, capped at a
# 30-day window between consecutive hops to keep the join bounded.
ctes = [f"""
hop0 as (
    select block_time, "from", "to", value, 0 as hop
    from {schema}.transactions
    where "from" = from_hex('{start_hex}')
      and success
)
"""]
for i in range(1, max_hops + 1):
    ctes.append(f"""
hop{i} as (
    select t.block_time, t."from", t."to", t.value, {i} as hop
    from {schema}.transactions t
    join hop{i - 1} h on t."from" = h."to"
    where t.success
      and t.block_time > h.block_time
      and t.block_time <= h.block_time + interval '30' day
)
""")

union_all = " union all\n".join(f"select block_time, \"from\", \"to\", value, hop from hop{i}" for i in range(0, max_hops + 1))

sql = f"""
with {",".join(ctes)}
select
    block_time,
    to_hex("from") as "from",
    to_hex("to") as "to",
    value,
    hop
from (
    {union_all}
) all_hops
where "to" = from_hex('{target_hex}')
order by hop, block_time
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
