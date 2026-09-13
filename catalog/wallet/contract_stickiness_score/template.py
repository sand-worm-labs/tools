# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

sql = f"""
with calls as (
    select "to" as contract, date_trunc('day', block_time) as day, "from" as caller
    from {CHAIN}.transactions
    where block_time >= date '{DATE_FROM}'
      and "to" is not null
),
daily_actives as (
    select contract, day, count(distinct caller) as dau
    from calls
    group by 1, 2
),
monthly_actives as (
    select contract, date_trunc('month', day) as month, count(distinct caller) as mau
    from calls
    group by 1, 2
),
avg_dau as (
    select contract, date_trunc('month', day) as month, avg(dau) as avg_dau
    from daily_actives
    group by 1, 2
)
select
    '0x' || to_hex(a.contract) as contract,
    a.avg_dau as dau,
    m.mau as mau,
    a.avg_dau / nullif(m.mau, 0) as stickiness_ratio
from avg_dau a
join monthly_actives m on m.contract = a.contract and m.month = a.month
order by stickiness_ratio desc
limit 500
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
