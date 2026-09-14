# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}".strip()
CHAIN = "{{chain}}"
INTERVAL = "{{interval}}".strip() or "day"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# Point-in-time snapshot (see token_circulating_supply_timeseries for the
# full daily history): mint = transfer from the zero address, burn = transfer
# to it, so net(mint - burn) up to now approximates circulating supply.
sql = f"""
with movements as (
    select
        case
            when "from" = from_hex('0000000000000000000000000000000000000000') then amount
            when "to" = from_hex('0000000000000000000000000000000000000000') then -amount
            else 0
        end as net_amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and (
        "from" = from_hex('0000000000000000000000000000000000000000')
        or "to" = from_hex('0000000000000000000000000000000000000000')
      )
)
select
    date_trunc('{INTERVAL}', now()) as day,
    sum(net_amount) as circulating_supply
from movements
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
