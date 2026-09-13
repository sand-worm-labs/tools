# Sandworm Power Toolbox — {{__tool_name}}
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

if not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

sql = f"""
with bounds as (
    select
        blockchain, symbol, contract_address,
        min_by(price, minute) as start_price,
        max_by(price, minute) as end_price
    from prices.usd
    where minute >= now() - interval '{LOOKBACK_DAYS}' day
    group by blockchain, symbol, contract_address
)
select
    blockchain,
    symbol,
    '0x' || to_hex(contract_address) as contract_address,
    (end_price - start_price) / nullif(start_price, 0) * 100 as pct_change,
    row_number() over (order by (end_price - start_price) / nullif(start_price, 0) desc) as rank
from bounds
where start_price is not null and start_price > 0
order by rank
limit 100
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="symbol", y="pct_change")
fig.show()

{{__df_name}}
