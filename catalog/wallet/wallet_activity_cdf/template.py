# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "365"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
# Dune's chain-prefixed raw schemas name BSC "bnb", not "bsc" (see bridges/volume for the same quirk).
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]

sql = f"""
with active_days as (
    select "from" as wallet, count(distinct date_trunc('day', block_time)) as days
    from {schema}.transactions
    where block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
hist as (
    select days, count(*) as wallet_count
    from active_days
    group by 1
),
total as (
    select sum(wallet_count) as total_wallets from hist
)
select
    h.days,
    h.wallet_count * 1.0 / t.total_wallets as pdf,
    sum(h.wallet_count) over (order by h.days) * 1.0 / t.total_wallets as cdf
from hist h
cross join total t
order by h.days
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
