# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
PROTOCOL = "{{protocol}}".strip()
DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
PROTOCOL_RE = re.compile(r"^[A-Za-z0-9_\- ]{1,64}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not PROTOCOL_RE.match(PROTOCOL):
    raise ValueError(f"Invalid protocol: {PROTOCOL!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {DAYS!r}")

sql = f"""
with trades as (
    select block_date, taker as user_address
    from dex.trades
    where blockchain = '{CHAIN}'
      and lower(project) = lower('{PROTOCOL}')
      and block_time >= now() - interval '{DAYS}' day
    group by block_date, taker
),
first_seen as (
    select taker as user_address, min(block_date) as first_date
    from dex.trades
    where blockchain = '{CHAIN}'
      and lower(project) = lower('{PROTOCOL}')
    group by taker
)
select
    t.block_date as time,
    count(*) filter (where f.first_date = t.block_date) as new,
    count(*) filter (where f.first_date < t.block_date) as existing,
    count(*) as dau
from trades t
join first_seen f on f.user_address = t.user_address
group by t.block_date
order by t.block_date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
