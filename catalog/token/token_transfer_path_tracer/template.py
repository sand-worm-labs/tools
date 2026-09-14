# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
START_ADDRESS = "{{start_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not ADDRESS_RE.match(START_ADDRESS):
    raise ValueError(f"Invalid start_address: {START_ADDRESS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
start_hex = START_ADDRESS[2:].lower()
MAX_HOPS_PER_LEVEL = 200

# Trino has no recursive CTE support, so the trace is unrolled to a fixed
# 3-hop depth (level 1/2/3) via successive self-joins instead of recursion,
# with a per-level fan-out cap to keep the join size bounded.
sql = f"""
with hop1 as (
    select 1 as level, tx_hash, "from", "to", amount as value
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and "from" = from_hex('{start_hex}')
    order by block_time
    limit {MAX_HOPS_PER_LEVEL}
),
hop2 as (
    select 2 as level, t.tx_hash, t."from", t."to", t.amount as value
    from tokens.transfers t
    join (select distinct "to" from hop1) h on t."from" = h."to"
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{contract_hex}')
    order by t.block_time
    limit {MAX_HOPS_PER_LEVEL}
),
hop3 as (
    select 3 as level, t.tx_hash, t."from", t."to", t.amount as value
    from tokens.transfers t
    join (select distinct "to" from hop2) h on t."from" = h."to"
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{contract_hex}')
    order by t.block_time
    limit {MAX_HOPS_PER_LEVEL}
)
select level, to_hex(tx_hash) as tx_hash, to_hex("from") as "from", to_hex("to") as "to", value from hop1
union all
select level, to_hex(tx_hash) as tx_hash, to_hex("from") as "from", to_hex("to") as "to", value from hop2
union all
select level, to_hex(tx_hash) as tx_hash, to_hex("from") as "from", to_hex("to") as "to", value from hop3
order by level, value desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
