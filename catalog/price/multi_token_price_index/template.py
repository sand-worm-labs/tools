# Sandworm Power Toolbox — {{__tool_name}}
SYMBOLS_RAW = "{{token_symbols}}".strip()
WEIGHTS_RAW = "{{weights}}".strip()

if not SYMBOLS_RAW:
    raise ValueError("token_symbols is required")
if not WEIGHTS_RAW:
    raise ValueError("weights is required")

symbols = [s.strip() for s in SYMBOLS_RAW.split(",") if s.strip()]
try:
    weights = [float(w.strip()) for w in WEIGHTS_RAW.split(",") if w.strip()]
except ValueError:
    raise ValueError(f"Invalid weights: {WEIGHTS_RAW!r}")

if len(symbols) != len(weights):
    raise ValueError("token_symbols and weights must have the same length")

symbol_in_sql = ", ".join(f"upper('{s}')" for s in symbols)
weighted_terms = " + ".join(
    f"coalesce(sum(case when upper(symbol) = upper('{sym}') then price end), 0) * {w}"
    for sym, w in zip(symbols, weights)
)

sql = f"""
with daily as (
    select date_trunc('day', minute) as day, symbol, avg(price) as price
    from prices.usd
    where upper(symbol) in ({symbol_in_sql})
    group by 1, 2
)
select day, {weighted_terms} as index_value
from daily
group by day
order by day
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y=['index_value'])
fig.show()

{{__df_name}}
