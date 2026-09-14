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

# Realized PnL only: sells minus buys in USD. Remaining unsold tokens are not
# marked to current price, since that would need a separate price lookup per
# trader's remaining balance.
sql = f"""
with buys as (
    select taker, block_time, amount_usd
    from dex.trades
    where blockchain = '{CHAIN}' and token_bought_address = from_hex('{token_hex}')
),
sells as (
    select taker, amount_usd
    from dex.trades
    where blockchain = '{CHAIN}' and token_sold_address = from_hex('{token_hex}')
),
buy_agg as (
    select taker, min(block_time) as first_buy_time, sum(amount_usd) as total_usd_b
    from buys
    group by 1
),
sell_agg as (
    select taker, sum(amount_usd) as total_usd_s
    from sells
    group by 1
)
select
    to_hex(b.taker) as trader_id,
    b.first_buy_time,
    b.total_usd_b,
    coalesce(s.total_usd_s, 0) as total_usd_s,
    coalesce(s.total_usd_s, 0) - b.total_usd_b as pnl
from buy_agg b
left join sell_agg s on s.taker = b.taker
order by pnl desc
limit 500
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
