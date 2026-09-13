# Sandworm Power Toolbox — {{__tool_name}}
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

if not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

sql = f"""
select
    cast(date_trunc('day', block_time) as varchar) as period,
    blockchain,
    approx_percentile(amount_usd / nullif(token_bought_amount, 0), 0.5) as price_50,
    approx_percentile(amount_usd / nullif(token_bought_amount, 0), 0.1) as price_lower
from dex.trades
where block_time >= now() - interval '{LOOKBACK_DAYS}' day
  and token_bought_amount > 0
group by 1, 2
order by 1, 2
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="period", y=['price_50', 'price_lower'])
fig.show()

{{__df_name}}
