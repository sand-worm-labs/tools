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
    select "from" as wallet, count(*) as tx_count
    from {schema}.transactions
    where success
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
bucketed as (
    select
        case
            when tx_count = 1 then '1'
            when tx_count between 2 and 5 then '2-5'
            when tx_count between 6 and 20 then '6-20'
            when tx_count between 21 and 100 then '21-100'
            else '100+'
        end as bucket
    from wallet_txs
)
select bucket, count(*) as wallet_count
from bucketed
group by 1
order by case bucket
    when '1' then 1
    when '2-5' then 2
    when '6-20' then 3
    when '21-100' then 4
    else 5
end
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
