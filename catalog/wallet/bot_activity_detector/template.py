# Sandworm Power Toolbox — {{__tool_name}}
import json
import re

CHAIN = "{{chain}}"
DATE_RANGE = json.loads("""{{date_range}}""")

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

sql = f"""
with bursts as (
    select
        date_trunc('hour', block_time) + (minute(block_time) / 5) * interval '5' minute as interval_start,
        "from" as signer_addr,
        count(*) as tx_count
    from {CHAIN}.transactions
    where block_time >= date '{FROM_DATE}'
      and block_time < date '{TO_DATE}' + interval '1' day
    group by 1, 2
)
select
    date_trunc('month', interval_start) as month,
    '0x' || to_hex(signer_addr) as signer,
    avg(tx_count) as bot_score
from bursts
group by 1, 2
order by bot_score desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
