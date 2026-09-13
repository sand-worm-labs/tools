# Sandworm Power Toolbox — {{__tool_name}}
import json


def _parse_date_range(raw):
    raw = raw.strip()
    if not raw:
        return None, None
    try:
        d = json.loads(raw)
        return d.get("from") or None, d.get("to") or None
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None, None


CHAIN = "{{chain}}"
DATE_FROM, DATE_TO = _parse_date_range("""{{date_range}}""")

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
if not DATE_FROM:
    raise ValueError("date_range.from is required")

schema = CHAIN_SCHEMA[CHAIN]
date_to_clause = f"and block_time <= date('{DATE_TO}')" if DATE_TO else ""

sql = f"""
with daily_wallet as (
    select
        "from" as wallet,
        date_trunc('day', block_time) as block_date,
        count(*) as tx_count,
        sum(value) / 1e18 as native_transferred
    from {schema}.transactions
    where success
      and block_time >= date('{DATE_FROM}')
      {date_to_clause}
    group by 1, 2
),
bucketed as (
    select
        block_date,
        case
            when tx_count = 1 then '1'
            when tx_count between 2 and 5 then '2-5'
            when tx_count between 6 and 20 then '6-20'
            else '20+'
        end as bucket,
        wallet,
        native_transferred
    from daily_wallet
)
select
    block_date,
    bucket,
    count(distinct wallet) as user_count,
    avg(native_transferred) as avg_native_transferred
from bucketed
group by 1, 2
order by 1, 2
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
