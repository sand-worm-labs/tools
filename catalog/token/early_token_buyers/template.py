# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with first_trade as (
    select min(block_time) as launch_time
    from dex.trades
    where blockchain = '{CHAIN}' and token_bought_address = from_hex('{token_hex}')
),
buys as (
    select taker, block_time, token_bought_amount
    from dex.trades, first_trade
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{token_hex}')
      and block_time <= first_trade.launch_time + interval '{LOOKBACK_DAYS}' day
)
select
    to_hex(taker) as wallet_address,
    min(block_time) as first_buy_time,
    sum(token_bought_amount) as buy_amount
from buys
group by taker
order by first_buy_time asc
limit 500
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
