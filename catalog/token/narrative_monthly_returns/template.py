# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
SYMBOLS_LIST = "{{symbols_list}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
SYMBOL_RE = re.compile(r"^[A-Za-z0-9]{1,15}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
symbols = [s.strip().upper() for s in SYMBOLS_LIST.split(",") if s.strip()]
if not symbols or not all(SYMBOL_RE.match(s) for s in symbols):
    raise ValueError(f"Invalid symbols_list: {SYMBOLS_LIST!r}")

symbol_list = ", ".join(f"'{s}'" for s in symbols)

sql = f"""
with monthly_prices as (
    select
        symbol,
        date_trunc('month', minute) as month,
        price,
        row_number() over (partition by symbol, date_trunc('month', minute) order by minute asc) as rn_first,
        row_number() over (partition by symbol, date_trunc('month', minute) order by minute desc) as rn_last
    from prices.usd
    where blockchain = '{CHAIN}'
      and symbol in ({symbol_list})
),
first_last as (
    select
        symbol,
        month,
        max(case when rn_first = 1 then price end) as price_start,
        max(case when rn_last = 1 then price end) as price_end
    from monthly_prices
    group by symbol, month
)
select
    symbol,
    month,
    (price_end - price_start) / nullif(price_start, 0) as return
from first_last
order by symbol, month
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
