# Sandworm Power Toolbox — {{__tool_name}}
TOKEN_SYMBOL = "{{token_symbol}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip()

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

# No contribution amount/frequency input exists on this tool, so this simulates
# a fixed $100/week DCA schedule bought at each week's median price.
sql = f"""
with daily as (
    select date_trunc('day', minute) as price_date, approx_percentile(price, 0.5) as median_price
    from prices.usd
    where upper(symbol) = upper('{TOKEN_SYMBOL}')
      and minute >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
weekly_buys as (
    select
        price_date,
        median_price,
        case when row_number() over (partition by date_trunc('week', price_date) order by price_date) = 1
             then 100.0 / median_price else 0 end as bought
    from daily
)
select
    price_date,
    median_price,
    sum(bought) over (order by price_date) as btc_stack,
    sum(bought) over (order by price_date) * median_price as stack_usd
from weekly_buys
order by price_date
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="price_date", y=['median_price'])
fig.show()

fig2 = px.line({{__df_name}}, x="price_date", y="stack_usd")
fig2.show()

{{__df_name}}
