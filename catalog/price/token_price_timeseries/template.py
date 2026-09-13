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


TOKEN_SYMBOL = "{{token_symbol}}".strip()
INTERVAL = "{{interval}}".strip() or "day"
DATE_FROM, DATE_TO = _parse_date_range("{{date_range}}")

ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")

date_from_clause = f"and minute >= date('{DATE_FROM}')" if DATE_FROM else "and minute >= now() - interval '90' day"
date_to_clause = f"and minute <= date('{DATE_TO}')" if DATE_TO else ""

sql = f"""
select
    date_trunc('{INTERVAL}', minute) as time,
    avg(price) as avg_price,
    min(price) as min_price,
    max(price) as max_price
from prices.usd
where upper(symbol) = upper('{TOKEN_SYMBOL}')
  {date_from_clause} {date_to_clause}
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="time", y=['avg_price', 'min_price', 'max_price'])
fig.show()

{{__df_name}}
