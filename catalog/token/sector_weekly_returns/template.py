# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
SYMBOLS = "{{symbols}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
SYMBOL_RE = re.compile(r"^[A-Za-z0-9]{1,15}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not SYMBOLS:
    raise ValueError("symbols is required")

symbols = [s.strip().upper() for s in SYMBOLS.split(",") if s.strip()]
if not symbols:
    raise ValueError("symbols must contain at least one token symbol")
for s in symbols:
    if not SYMBOL_RE.match(s):
        raise ValueError(f"Invalid symbol: {s!r}")

symbol_list_sql = ", ".join(f"'{s}'" for s in symbols)

sql = f"""
with daily as (
    select date_trunc('day', minute) as day, symbol, avg(price) as price
    from prices.usd
    where blockchain = '{CHAIN}'
      and upper(symbol) in ({symbol_list_sql})
    group by 1, 2
),
weekly as (
    select
        date_trunc('week', day) as week,
        symbol,
        min_by(price, day) as price_initial,
        max_by(price, day) as price
    from daily
    group by 1, 2
)
select
    week,
    symbol,
    price_initial,
    price,
    (price - price_initial) / nullif(price_initial, 0) as weekly_return
from weekly
order by week, symbol
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
