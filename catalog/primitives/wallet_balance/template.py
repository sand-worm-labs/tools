# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"
TOKEN_ADDRESS = "{{token_address}}"
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if not ADDRESS_RE.match(TOKEN_ADDRESS):
    raise ValueError(f"Invalid token_address: {TOKEN_ADDRESS!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")

wallet_hex = WALLET[2:].lower()
token_hex = TOKEN_ADDRESS[2:].lower()

# For a non-"all" time range, running_balance is the net change within the
# window, not the wallet's actual balance (which needs all history from
# token launch).
sql = f"""
with movements as (
    select date_trunc('day', block_time) as day, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "to" = from_hex('{wallet_hex}')
      {{__time_where}}
    union all
    select date_trunc('day', block_time) as day, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" = from_hex('{wallet_hex}')
      {{__time_where}}
),
daily as (
    select day, sum(amt) as net_change
    from movements
    group by day
)
select
    day,
    net_change,
    sum(net_change) over (order by day) as running_balance
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
