# Sandworm Power Toolbox — {{__tool_name}}
import re

TOKEN1_ADDR = "{{token1_addr}}"
TOKEN2_SYM = "{{token2_sym}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "333"

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if not ADDRESS_RE.match(TOKEN1_ADDR):
    raise ValueError(f"Invalid token1_addr: {TOKEN1_ADDR!r}")
if not TOKEN2_SYM:
    raise ValueError("token2_sym is required")
if not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

sql = f"""
with p1 as (
    select date_trunc('day', minute) as date, avg(price) as price
    from prices.usd
    where contract_address = from_hex('{TOKEN1_ADDR[2:].lower()}')
      and minute >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
p2 as (
    select date_trunc('day', minute) as date, avg(price) as price
    from prices.usd
    where upper(symbol) = upper('{TOKEN2_SYM}')
      and minute >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
ratios as (
    select p1.date, p1.price / nullif(p2.price, 0) as ratio
    from p1 join p2 on p1.date = p2.date
)
select
    date,
    ratio,
    avg(ratio) over (order by date rows between 29 preceding and current row) as ma30
from ratios
order by date
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="date", y=['ratio', 'ma30'])
fig.show()

{{__df_name}}
