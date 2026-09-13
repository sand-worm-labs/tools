# Sandworm Power Toolbox — {{__tool_name}}
import json


def _parse_date_range(raw):
    raw = raw.strip()
    if not raw:
        return None, None
    try:
        d = json.loads(raw)
        return d.get("from") or None, d.get("to") or None
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None, None


DATE_FROM, DATE_TO = _parse_date_range("{{date_range}}")

# No stablecoins input exists on this tool, so this scores a fixed default set.
STABLECOINS = ["USDC", "USDT", "DAI", "FRAX"]
symbol_in_sql = ", ".join(f"upper('{s}')" for s in STABLECOINS)

date_from_clause = f"and minute >= date('{DATE_FROM}')" if DATE_FROM else "and minute >= now() - interval '90' day"
date_to_clause = f"and minute <= date('{DATE_TO}')" if DATE_TO else ""

sql = f"""
with daily as (
    select date_trunc('day', minute) as day, symbol, avg(price) as price, stddev(price) as vol_d
    from prices.usd
    where upper(symbol) in ({symbol_in_sql})
      {date_from_clause} {date_to_clause}
    group by 1, 2
)
select
    symbol as token,
    day,
    abs(price - 1) * 10000 as med_dev_bps,
    vol_d,
    abs(price - 1) * 10000 + coalesce(vol_d, 0) * 10000 as risk_score
from daily
order by symbol, day
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y=['risk_score'])
fig.show()

{{__df_name}}
