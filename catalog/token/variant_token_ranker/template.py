# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
BASE_SYMBOL = "{{base_symbol}}".strip().upper()
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
SYMBOL_RE = re.compile(r"^[A-Z0-9]{1,20}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not BASE_SYMBOL:
    BASE_SYMBOL = "BTC"
if not SYMBOL_RE.match(BASE_SYMBOL):
    raise ValueError(f"Invalid base_symbol: {BASE_SYMBOL!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    LOOKBACK_DAYS = "30"

sql = f"""
with matched as (
    select token_bought_symbol as symbol, token_bought_amount_usd as amount_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
      and token_bought_symbol like '%{BASE_SYMBOL}%'
    union all
    select token_sold_symbol as symbol, token_sold_amount_usd as amount_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
      and token_sold_symbol like '%{BASE_SYMBOL}%'
)
select
    symbol,
    sum(amount_usd) as volume
from matched
where symbol is not null
group by symbol
order by volume desc
limit 50
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
