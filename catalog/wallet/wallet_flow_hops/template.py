# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET_ADDRESS = "{{wallet_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")

schema = CHAIN_SCHEMA[CHAIN]
wallet_hex = WALLET_ADDRESS[2:].lower()

# Trino has no recursive CTEs, so hops are unrolled explicitly up to depth 3.
sql = f"""
with hop1 as (
    select block_time, "from" as sender, "to" as recipient, value / 1e18 as eth_value, 1 as hop
    from {schema}.transactions
    where "from" = from_hex('{wallet_hex}')
      and value > 0
    order by block_time desc
    limit 100
),
hop2 as (
    select t.block_time, t."from" as sender, t."to" as recipient, t.value / 1e18 as eth_value, 2 as hop
    from {schema}.transactions t
    join (select distinct recipient as wallet from hop1) h1 on h1.wallet = t."from"
    where t.value > 0
    order by t.block_time desc
    limit 200
),
hop3 as (
    select t.block_time, t."from" as sender, t."to" as recipient, t.value / 1e18 as eth_value, 3 as hop
    from {schema}.transactions t
    join (select distinct recipient as wallet from hop2) h2 on h2.wallet = t."from"
    where t.value > 0
    order by t.block_time desc
    limit 300
)
select block_time, to_hex(sender) as sender, to_hex(recipient) as recipient, eth_value, hop from hop1
union all
select block_time, to_hex(sender) as sender, to_hex(recipient) as recipient, eth_value, hop from hop2
union all
select block_time, to_hex(sender) as sender, to_hex(recipient) as recipient, eth_value, hop from hop3
order by hop, block_time desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
