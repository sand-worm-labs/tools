# Sandworm Power Toolbox — {{__tool_name}}
# "Meme wallet trade classifier" generalized to any EVM DEX: classifies wallets
# trading a given set of meme-coin symbols by their buy/sell activity via dex.trades.
import re

CHAIN = "{{chain}}"
TOKEN_SYMBOLS = "{{token_symbols}}"
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
SYMBOL_RE = re.compile(r"^[A-Za-z0-9]{1,15}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
symbols = [s.strip().upper() for s in TOKEN_SYMBOLS.split(",") if s.strip()]
if not symbols or not all(SYMBOL_RE.match(s) for s in symbols):
    raise ValueError(f"Invalid token_symbols: {TOKEN_SYMBOLS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

symbol_list = ", ".join(f"'{s}'" for s in symbols)

sql = f"""
with trades as (
    select
        taker as wallet,
        case when token_bought_symbol in ({symbol_list}) then 1 else 0 end as is_buy,
        case when token_sold_symbol in ({symbol_list}) then 1 else 0 end as is_sell
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
      and (token_bought_symbol in ({symbol_list}) or token_sold_symbol in ({symbol_list}))
)
select
    concat('0x', to_hex(wallet)) as wallet_address,
    count(*) as total_trades,
    sum(is_buy) as buy_trades,
    sum(is_sell) as sell_trades
from trades
group by wallet
order by total_trades desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
