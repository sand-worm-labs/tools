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
with wallet_txs as (
    select "from" as wallet, count(*) as total_txs
    from {schema}.transactions
    where success
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
dist as (
    select total_txs, count(*) as addresses
    from wallet_txs
    group by 1
)
select
    total_txs,
    addresses,
    sum(addresses) over (order by total_txs) / cast(sum(addresses) over () as double) as percentile
from dist
order by total_txs
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
