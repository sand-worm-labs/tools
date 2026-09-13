# Sandworm Power Toolbox — {{__tool_name}}
SYMBOLS_RAW = "{{symbols}}".strip() or "BTC,ETH,SOL"
LOOKBACK_HOURS = "{{lookback_hours}}".strip() or "24"
TOP_N = "{{top_n}}".strip() or "3"

symbols = [s.strip() for s in SYMBOLS_RAW.split(",") if s.strip()]
if not symbols:
    raise ValueError("symbols is required")
if not (LOOKBACK_HOURS.isdigit() and int(LOOKBACK_HOURS) > 0):
    raise ValueError(f"Invalid lookback_hours: {LOOKBACK_HOURS!r}")
if not (TOP_N.isdigit() and int(TOP_N) > 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

symbol_in_sql = ", ".join(f"upper('{s}')" for s in symbols)

sql = f"""
with hourly as (
    select date_trunc('hour', minute) as ts, symbol, avg(price) as price
    from prices.usd
    where upper(symbol) in ({symbol_in_sql})
      and minute >= now() - interval '{LOOKBACK_HOURS}' hour
    group by 1, 2
),
returns as (
    select
        ts, symbol,
        (price - lag(price) over (partition by symbol order by ts))
            / nullif(lag(price) over (partition by symbol order by ts), 0) as r
    from hourly
),
ranked as (
    select ts, symbol, r, row_number() over (partition by ts order by r desc) as rnk
    from returns
    where r is not null
)
select ts, symbol, r
from ranked
where rnk <= {int(TOP_N)}
order by ts, rnk
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="symbol", y="r")
fig.show()

{{__df_name}}
