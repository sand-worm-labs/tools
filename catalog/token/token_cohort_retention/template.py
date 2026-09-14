# Sandworm Power Toolbox — {{__tool_name}}
import json
import re


def _parse_date_range(raw):
    raw = raw.strip()
    if not raw:
        return None, None
    try:
        d = json.loads(raw)
        return d.get("from") or None, d.get("to") or None
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None, None


CONTRACT_ADDRESS = "{{contract_address}}".strip()
CHAIN = "{{chain}}"
DATE_FROM, DATE_TO = _parse_date_range("""{{date_range}}""")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_range requires both 'from' and 'to'")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with all_events as (
    select "to" as user_address, block_date as day
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token_hex}')
      and block_date between date('{DATE_FROM}') and date('{DATE_TO}')
    union all
    select "from" as user_address, block_date as day
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token_hex}')
      and block_date between date('{DATE_FROM}') and date('{DATE_TO}')
),
distinct_events as (
    select distinct user_address, day from all_events
),
first_seen as (
    select user_address, min(day) as cohort_date
    from distinct_events
    group by user_address
),
returning as (
    select f.cohort_date, d.user_address
    from distinct_events d
    join first_seen f on f.user_address = d.user_address
    where d.day > f.cohort_date
)
select
    f.cohort_date,
    count(distinct r.user_address) as returning_users,
    count(distinct f.user_address) as cohort_size,
    cast(count(distinct r.user_address) as double) / nullif(count(distinct f.user_address), 0) as retention
from first_seen f
left join returning r on r.cohort_date = f.cohort_date
group by f.cohort_date
order by f.cohort_date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
