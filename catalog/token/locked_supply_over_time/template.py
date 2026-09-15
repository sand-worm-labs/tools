# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOCKER_ADDRESS = "{{locker_address}}"
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not ADDRESS_RE.match(LOCKER_ADDRESS):
    raise ValueError(f"Invalid locker_address: {LOCKER_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
locker_hex = LOCKER_ADDRESS[2:].lower()

sql = f"""
with movements as (
    select date_trunc('day', block_time) as day, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "to" = from_hex('{locker_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    union all
    select date_trunc('day', block_time) as day, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" = from_hex('{locker_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
daily as (
    select day, sum(amt) as locked
    from movements
    group by 1
)
select
    day as date,
    locked,
    sum(locked) over (order by day) as total_locked
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
