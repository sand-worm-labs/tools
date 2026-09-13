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
THRESHOLD = "{{threshold number of transfers}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not THRESHOLD:
    THRESHOLD = "3000"
if not THRESHOLD.isdigit() or int(THRESHOLD) <= 0:
    raise ValueError(f"Invalid threshold: {THRESHOLD!r}")

date_from_clause = f"and block_time >= date('{DATE_FROM}')" if DATE_FROM else "and block_time >= now() - interval '1' day"
date_to_clause = f"and block_time <= date('{DATE_TO}')" if DATE_TO else ""

sql = f"""
with daily_pairs as (
    select date_trunc('day', block_time) as day, "from" as wallet, "to" as recipient, count(*) as transfers
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      {date_from_clause} {date_to_clause}
    group by 1, 2, 3
)
select day, wallet, recipient, transfers
from daily_pairs
where transfers >= {THRESHOLD}
order by transfers desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
