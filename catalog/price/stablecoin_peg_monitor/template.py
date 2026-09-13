# Sandworm Power Toolbox — {{__tool_name}}
import re

SYMBOLS_RAW = "{{symbols}}".replace('"', "").strip() or "USDC,USDT,DAI,FRAX"
INTERVAL = "{{interval}}".strip() or "hour"
DATE_FROM = "{{date_from}}"

ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

symbols = [s.strip() for s in SYMBOLS_RAW.split(",") if s.strip()]
if not symbols:
    raise ValueError("symbols is required")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

symbol_in_sql = ", ".join(f"upper('{s}')" for s in symbols)

sql = f"""
with bucketed as (
    select date_trunc('{INTERVAL}', minute) as hour, symbol, avg(price) as price
    from prices.usd
    where upper(symbol) in ({symbol_in_sql})
      and minute >= date('{DATE_FROM}')
    group by 1, 2
)
select
    hour,
    symbol,
    price - 1 as peg_diff,
    stddev(price) over (partition by symbol order by hour rows between 9 preceding and current row) as volatility
from bucketed
order by symbol, hour
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="hour", y=['peg_diff', 'volatility'])
fig.show()

{{__df_name}}
