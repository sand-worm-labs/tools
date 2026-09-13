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
with monthly as (
    select
        "from" as wallet,
        date_trunc('month', block_time) as month_start,
        count(distinct "to") as contract_count
    from {schema}.transactions
    where success
      and "to" is not null
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1, 2
)
select
    month_start,
    count(*) as single_contract_users
from monthly
where contract_count = 1
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
