# Sandworm Power Toolbox — {{__tool_name}}
import json
import re

CHAIN = "{{chain}}"
DATE_RANGE = json.loads("""{{date_range}}""")
TX_SUCCESS = "{{tx_success}}".strip().lower()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
FROM_DATE = str(DATE_RANGE.get("from", ""))
TO_DATE = str(DATE_RANGE.get("to", ""))
if not DATE_RE.match(FROM_DATE) or not DATE_RE.match(TO_DATE):
    raise ValueError(f"Invalid date_range: {DATE_RANGE!r}")
if FROM_DATE > TO_DATE:
    raise ValueError("date_range 'from' must not be after 'to'")
if TX_SUCCESS not in ("true", "false", ""):
    raise ValueError(f"Invalid tx_success: {TX_SUCCESS!r}")

success_filter = ""
if TX_SUCCESS == "true":
    success_filter = "and success = true"
elif TX_SUCCESS == "false":
    success_filter = "and success = false"

sql = f"""
with daily_tx as (
    select date_trunc('day', block_time) as block_date, "from" as wallet, "to" as contract
    from {CHAIN}.transactions
    where block_time >= date '{FROM_DATE}'
      and block_time < date '{TO_DATE}' + interval '1' day
      {success_filter}
),
wallet_daily_counts as (
    select block_date, wallet, count(*) as tx_count
    from daily_tx
    group by 1, 2
),
cohorts as (
    select
        block_date,
        wallet,
        case
            when tx_count >= 50 then 'high'
            when tx_count >= 10 then 'medium'
            else 'low'
        end as cohort
    from wallet_daily_counts
)
select
    d.block_date,
    c.cohort,
    '0x' || to_hex(d.contract) as contract,
    count(*) as call_count
from daily_tx d
join cohorts c on c.block_date = d.block_date and c.wallet = d.wallet
where d.contract is not null
group by 1, 2, 3
order by 1, 4 desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
