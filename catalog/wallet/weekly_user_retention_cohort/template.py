# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]

sql = f"""
with txs as (
    select "from" as wallet, date_trunc('week', block_time) as week
    from {schema}.transactions
    where block_time >= date('{DATE_FROM}')
      and block_time < date('{DATE_FROM}') + interval '{LOOKBACK_DAYS}' day
    group by 1, 2
),
first_week as (
    select wallet, min(week) as cohort_week
    from txs
    group by 1
),
cohort_sizes as (
    select cohort_week, count(distinct wallet) as cohort_size
    from first_week
    group by 1
),
activity as (
    select f.cohort_week, t.week as activity_week, count(distinct t.wallet) as active_wallets
    from txs t
    join first_week f on f.wallet = t.wallet
    group by 1, 2
)
select
    cast(a.cohort_week as date) as cohort_week,
    cast(a.activity_week as date) as activity_week,
    a.active_wallets * 1.0 / c.cohort_size as retention_rate
from activity a
join cohort_sizes c on c.cohort_week = a.cohort_week
order by a.cohort_week, a.activity_week
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
