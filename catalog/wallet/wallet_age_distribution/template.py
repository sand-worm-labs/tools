# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_TO = "{{date_to}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_TO):
    raise ValueError(f"Invalid date_to: {DATE_TO!r}")

schema = CHAIN_SCHEMA[CHAIN]

sql = f"""
with first_tx as (
    select "from" as wallet, min(block_time) as first_block_time
    from {schema}.transactions
    where block_time <= date('{DATE_TO}')
    group by 1
),
aged as (
    select date_diff('day', first_block_time, date('{DATE_TO}')) as age_days
    from first_tx
),
bucketed as (
    select
        case
            when age_days < 7 then '0-7d'
            when age_days < 30 then '7-30d'
            when age_days < 90 then '30-90d'
            when age_days < 365 then '90-365d'
            else '365d+'
        end as cohort,
        age_days
    from aged
)
select cohort, count(*) as wallet_count
from bucketed
group by 1
order by min(age_days)
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
