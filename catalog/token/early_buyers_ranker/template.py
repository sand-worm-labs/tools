# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with buys as (
    select taker, block_time, token_bought_amount
    from dex.trades
    where blockchain = '{CHAIN}' and token_bought_address = from_hex('{token_hex}')
),
agg as (
    select
        taker,
        min(block_time) as time_of_first_buy,
        sum(token_bought_amount) as amount_bought,
        count(*) as buys_count
    from buys
    group by 1
)
select
    row_number() over (order by time_of_first_buy asc) as trader_rank,
    to_hex(taker) as trader,
    time_of_first_buy,
    amount_bought,
    buys_count
from agg
order by trader_rank
limit 500
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
