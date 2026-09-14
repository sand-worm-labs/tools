# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}"
THRESHOLD_USD = "{{threshold_usd}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
if not THRESHOLD_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid threshold_usd: {THRESHOLD_USD!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# "Dormant" is proxied as: an address's most recent transfer activity on this
# token was before the lookback window, then it received a large transfer
# inside the window (a reactivation), since we have no separate dormancy
# period input distinct from lookback_days.
sql = f"""
with activity as (
    select "from" as address, block_time from tokens.transfers
    where blockchain = '{CHAIN}' and contract_address = from_hex('{token_hex}')
    union all
    select "to" as address, block_time from tokens.transfers
    where blockchain = '{CHAIN}' and contract_address = from_hex('{token_hex}')
),
last_before_window as (
    select address, max(block_time) as last_activity
    from activity
    where block_time < now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
recent_large as (
    select "to" as address, block_time as recent_time, amount as recent_amount, amount_usd as usd_amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{token_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
      and amount_usd >= {THRESHOLD_USD}
)
select
    to_hex(r.address) as address,
    lb.last_activity,
    r.recent_amount,
    r.usd_amount
from recent_large r
join last_before_window lb on lb.address = r.address
order by r.usd_amount desc
limit 200
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
