# Sandworm Power Toolbox — {{__tool_name}}
import json
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_RANGE = json.loads('''{{date_range}}''')

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

DATE_FROM = DATE_RANGE.get("from", "")
DATE_TO = DATE_RANGE.get("to", "")
if not DATE_RE.match(DATE_FROM) or not DATE_RE.match(DATE_TO):
    raise ValueError(f"Invalid date_range: {DATE_RANGE!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

# Retention is measured on the exact cohort_date + N day, not "any time within
# N days" — a stricter, simpler definition given no session-level data exists.
sql = f"""
with all_transfers as (
    select block_time, "from" as addr
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{contract_hex}')
    union all
    select block_time, "to" as addr
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{contract_hex}')
),
first_seen as (
    select addr, min(date_trunc('day', block_time)) as cohort_date
    from all_transfers
    group by addr
),
cohorts as (
    select addr, cohort_date
    from first_seen
    where cohort_date between date '{DATE_FROM}' and date '{DATE_TO}'
),
activity as (
    select distinct addr, date_trunc('day', block_time) as activity_day
    from all_transfers
)
select
    c.cohort_date,
    count(distinct c.addr) as cohort_size,
    count(distinct a1.addr) * 1.0 / count(distinct c.addr) as retention_1d,
    count(distinct a7.addr) * 1.0 / count(distinct c.addr) as retention_7d,
    count(distinct a30.addr) * 1.0 / count(distinct c.addr) as retention_30d
from cohorts c
left join activity a1 on a1.addr = c.addr and a1.activity_day = c.cohort_date + interval '1' day
left join activity a7 on a7.addr = c.addr and a7.activity_day = c.cohort_date + interval '7' day
left join activity a30 on a30.addr = c.addr and a30.activity_day = c.cohort_date + interval '30' day
group by c.cohort_date
order by c.cohort_date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
