# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]

sql = f"""
with daily as (
    select
        date_trunc('day', block_time) as block_time,
        sum(gas_used * gas_price) / 1e18 as native_spent
    from {schema}.transactions
    where block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
)
select
    block_time,
    sum(native_spent) over (order by block_time) as cumulative_native
from daily
order by block_time
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
