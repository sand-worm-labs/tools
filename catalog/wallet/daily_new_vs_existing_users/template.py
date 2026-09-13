# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
PROTOCOL_ADDRESS = "{{protocol_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "60"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(PROTOCOL_ADDRESS):
    raise ValueError(f"Invalid protocol_address: {PROTOCOL_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

protocol_hex = PROTOCOL_ADDRESS[2:].lower()

# first_seen is computed over the protocol's full history (not just the
# lookback window) so "new" vs "existing" is judged against true first use.
sql = f"""
with activity as (
    select "from" as wallet, date_trunc('day', block_time) as day
    from {CHAIN}.transactions
    where "to" = from_hex('{protocol_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1, 2
),
first_seen as (
    select "from" as wallet, min(date_trunc('day', block_time)) as first_day
    from {CHAIN}.transactions
    where "to" = from_hex('{protocol_hex}')
    group by 1
)
select
    a.day as time,
    count(distinct case when a.day = f.first_day then a.wallet end) as new,
    count(distinct case when a.day > f.first_day then a.wallet end) as existing
from activity a
join first_seen f on f.wallet = a.wallet
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
