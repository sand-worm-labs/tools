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
with active_wallets as (
    select distinct "from" as wallet
    from {schema}.transactions
    where success
      and block_time >= date '{DATE_FROM}'
),
lifetime as (
    select t."from" as wallet, count(*) as lifetime_txs
    from {schema}.transactions t
    join active_wallets a on a.wallet = t."from"
    where t.success
    group by 1
)
select
    case
        when lifetime_txs <= 10 then '1-10'
        when lifetime_txs <= 50 then '11-50'
        when lifetime_txs <= 200 then '51-200'
        else '200+'
    end as cohort,
    count(*) as address_count
from lifetime
group by 1
order by case
    when max(lifetime_txs) <= 10 then 1
    when max(lifetime_txs) <= 50 then 2
    when max(lifetime_txs) <= 200 then 3
    else 4
end
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
