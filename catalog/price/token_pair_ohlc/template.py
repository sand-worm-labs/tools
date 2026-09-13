# Sandworm Power Toolbox — {{__tool_name}}
import re

TOKEN_A = "{{token_a_symbol}}".strip()
TOKEN_B = "{{token_b_symbol}}".strip()
INTERVAL = "{{interval}}".strip() or "day"
DATE_FROM = "{{date_from}}"

ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if not TOKEN_A:
    raise ValueError("token_a_symbol is required")
if not TOKEN_B:
    raise ValueError("token_b_symbol is required")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

sql = f"""
with trades as (
    select
        block_time,
        case
            when token_bought_symbol = '{TOKEN_A}' then token_sold_amount / nullif(token_bought_amount, 0)
            else token_bought_amount / nullif(token_sold_amount, 0)
        end as price,
        amount_usd
    from dex.trades
    where block_time >= date('{DATE_FROM}')
      and ((token_bought_symbol = '{TOKEN_A}' and token_sold_symbol = '{TOKEN_B}')
        or (token_bought_symbol = '{TOKEN_B}' and token_sold_symbol = '{TOKEN_A}'))
),
bucketed as (
    select date_trunc('{INTERVAL}', block_time) as open_time, block_time, price, amount_usd
    from trades
    where price is not null
)
select
    open_time,
    min_by(price, block_time) as open,
    max(price) as high,
    min(price) as low,
    max_by(price, block_time) as close,
    sum(amount_usd) as volume
from bucketed
group by open_time
order by open_time
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.graph_objects as go

fig = go.Figure(data=[go.Candlestick(
    x={{__df_name}}["open_time"],
    open={{__df_name}}["open"],
    high={{__df_name}}["high"],
    low={{__df_name}}["low"],
    close={{__df_name}}["close"],
)])
fig.show()

{{__df_name}}
