# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}"

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
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

schema = CHAIN_SCHEMA[CHAIN]

sql = f"""
with wallet_txs as (
    select "from" as wallet, count(*) as tx_count
    from {schema}.transactions
    where success
      and block_time >= date '{DATE_FROM}'
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
),
counts as (
    select bucket, count(*) as user_count
    from bucketed
    group by 1
)
select
    bucket,
    user_count,
    100.0 * user_count / sum(user_count) over () as pct_users
from counts
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
