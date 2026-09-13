# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

sql = f"""
with first_seen as (
    select "from" as wallet, min(date_trunc('week', block_time)) as cohort_week
    from {CHAIN}.transactions
    where block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
activity as (
    select "from" as wallet, date_trunc('week', block_time) as activity_week
    from {CHAIN}.transactions
    where block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1, 2
),
cohort_activity as (
    select
        f.cohort_week,
        date_diff('week', f.cohort_week, a.activity_week) as week_number,
        a.wallet
    from first_seen f
    join activity a on a.wallet = f.wallet and a.activity_week >= f.cohort_week
),
cohort_sizes as (
    select cohort_week, count(*) as cohort_size
    from first_seen
    group by 1
)
select
    ca.cohort_week,
    ca.week_number,
    count(distinct ca.wallet) as active_wallets,
    cast(count(distinct ca.wallet) as double) / nullif(cs.cohort_size, 0) as retention_rate
from cohort_activity ca
join cohort_sizes cs on cs.cohort_week = ca.cohort_week
group by 1, 2, cs.cohort_size
order by 1, 2
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
