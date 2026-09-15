# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
LIST_SYMBOLS = "{{list_symbols}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
SYMBOL_RE = re.compile(r"^[A-Za-z0-9._-]{1,20}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")

symbols = [s.strip().upper() for s in LIST_SYMBOLS.split(",") if s.strip()]
if not symbols:
    raise ValueError(f"Invalid list_symbols: {LIST_SYMBOLS!r}")
for sym in symbols:
    if not SYMBOL_RE.match(sym):
        raise ValueError(f"Invalid symbol in list_symbols: {sym!r}")

symbols_sql = ", ".join(f"'{s}'" for s in symbols)

sql = f"""
with p as (
    select symbol, minute, price
    from prices.usd
    where blockchain = '{CHAIN}' and symbol in ({symbols_sql})
),
current_p as (
    select p.symbol, p.price as current
    from p
    join (select symbol, max(minute) as minute from p group by symbol) m
      on m.symbol = p.symbol and m.minute = p.minute
),
p30 as (
    select p.symbol, p.price as init_30d
    from p
    join (
        select symbol, min(minute) as minute
        from p
        where minute >= now() - interval '30' day
        group by symbol
    ) m on m.symbol = p.symbol and m.minute = p.minute
),
p6m as (
    select p.symbol, p.price as init_6m
    from p
    join (
        select symbol, min(minute) as minute
        from p
        where minute >= now() - interval '180' day
        group by symbol
    ) m on m.symbol = p.symbol and m.minute = p.minute
)
select
    c.symbol,
    i30.init_30d,
    i6.init_6m,
    c.current,
    (c.current - i30.init_30d) / nullif(i30.init_30d, 0) as perf_30d,
    (c.current - i6.init_6m) / nullif(i6.init_6m, 0) as perf_6m
from current_p c
left join p30 i30 on i30.symbol = c.symbol
left join p6m i6 on i6.symbol = c.symbol
order by c.symbol
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
