# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}"
DAYS = "{{days}}"
TOP_N = "{{top_n}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_TOP_N = {"10", "25", "50", "100"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_ADDRESS):
    raise ValueError(f"Invalid token_address: {TOKEN_ADDRESS!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid days: {DAYS!r}")
if TOP_N not in ALLOWED_TOP_N:
    raise ValueError(f"Unsupported top_n: {TOP_N!r}")

token_hex = TOKEN_ADDRESS[2:].lower()

sql = f"""
with trades as (
    select
        taker as wallet,
        block_time,
        case when token_bought_address = from_hex('{token_hex}') then token_bought_amount else -token_sold_amount end as token_amount,
        case when token_bought_address = from_hex('{token_hex}') then -amount_usd else amount_usd end as usd_flow
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{token_hex}') or token_sold_address = from_hex('{token_hex}'))
      and block_time >= now() - interval '{DAYS}' day
),
agg as (
    select
        wallet,
        min(block_time) as first_trade_time,
        count(*) as trade_count,
        sum(usd_flow) as realized_usd_pnl,
        sum(token_amount) as net_token_position
    from trades
    group by 1
),
latest_price as (
    select price
    from prices.usd
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{token_hex}')
    order by minute desc
    limit 1
)
select
    to_hex(a.wallet) as wallet,
    a.first_trade_time,
    a.trade_count,
    a.realized_usd_pnl,
    a.net_token_position,
    a.net_token_position * lp.price as unrealized_usd_value,
    a.realized_usd_pnl + (a.net_token_position * lp.price) as total_pnl_usd
from agg a
cross join latest_price lp
order by total_pnl_usd desc
limit {TOP_N}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
