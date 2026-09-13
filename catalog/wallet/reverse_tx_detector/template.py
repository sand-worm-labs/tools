# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}"

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

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]

sql = f"""
with txs as (
    select "from" as addr_a, "to" as addr_b, block_time
    from {schema}.transactions
    where success
      and value > 0
      and "to" is not null
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
pairs as (
    select a.addr_a as wallet_x
    from txs a
    join txs b
        on a.addr_a = b.addr_b
       and a.addr_b = b.addr_a
       and b.block_time > a.block_time
       and b.block_time <= a.block_time + interval '{LOOKBACK_DAYS}' day
)
select
    to_hex(wallet_x) as wallet,
    count(*) as pair_count
from pairs
group by 1
order by pair_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
