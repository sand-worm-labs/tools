# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()
DECIMALS = "{{decimals}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
if not DECIMALS.isdigit():
    raise ValueError(f"Invalid decimals: {DECIMALS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
scale = f"power(10, {int(DECIMALS)})"

# tokens.transfers.amount_raw is the un-adjusted on-chain integer amount;
# `decimals` scales it into human units here instead of relying on the
# spellbook's own (sometimes stale) decimals lookup.
sql = f"""
with movements as (
    select "to" as address, amount_raw / {scale} as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    union all
    select "from" as address, -(amount_raw / {scale}) as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
net as (
    select address, sum(amt) as net_flow
    from movements
    group by address
)
select
    to_hex(address) as address,
    net_flow,
    case when net_flow >= 0 then 'net_receiver' else 'net_sender' end as direction
from net
order by abs(net_flow) desc
limit 200
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
