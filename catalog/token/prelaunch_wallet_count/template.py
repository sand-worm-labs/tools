# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
START_TIME = "{{start_time}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DATE_RE.match(START_TIME):
    raise ValueError(f"Invalid start_time: {START_TIME!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

# "start_time" is date-granular input; treated as the launch moment
# (midnight UTC on that date) that the 5/10-minute buyer windows count from.
sql = f"""
with buys as (
    select taker as wallet, block_time
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{contract_hex}')
      and block_time >= timestamp '{START_TIME} 00:00:00'
      and block_time < timestamp '{START_TIME} 00:00:00' + interval '10' minute
)
select
    count(distinct case when block_time < timestamp '{START_TIME} 00:00:00' + interval '5' minute then wallet end) as wallets_5min,
    count(distinct wallet) as wallets_10min,
    'first_10min' as period
from buys
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
