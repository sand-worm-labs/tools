# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
PROTOCOL = "{{protocol}}"
DATE_FROM = "{{date_from}}"
INTERVAL = "{{interval}}".strip() or "day"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(PROTOCOL):
    raise ValueError(f"Invalid protocol address: {PROTOCOL!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")

protocol_hex = PROTOCOL[2:].lower()

sql = f"""
with activity as (
    select "from" as wallet, date_trunc('{INTERVAL}', block_time) as period
    from {CHAIN}.transactions
    where "to" = from_hex('{protocol_hex}')
      and block_time >= date '{DATE_FROM}'
    group by 1, 2
),
first_seen as (
    select "from" as wallet, min(date_trunc('{INTERVAL}', block_time)) as first_period
    from {CHAIN}.transactions
    where "to" = from_hex('{protocol_hex}')
    group by 1
)
select
    a.period as date,
    count(distinct case when a.period = f.first_period then a.wallet end) as new_users,
    count(distinct case when a.period > f.first_period then a.wallet end) as returning_users,
    count(distinct a.wallet) as total_users
from activity a
join first_seen f on f.wallet = a.wallet
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
