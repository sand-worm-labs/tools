# Sandworm Power Toolbox — {{__tool_name}}
TOKEN_SYMBOL = "{{token_symbol}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip()

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

sql = f"""
with current_px as (
    select avg(price) as price
    from prices.usd
    where upper(symbol) = upper('{TOKEN_SYMBOL}')
      and minute >= now() - interval '1' hour
),
prior_px as (
    select avg(price) as price
    from prices.usd
    where upper(symbol) = upper('{TOKEN_SYMBOL}')
      and minute >= now() - interval '{LOOKBACK_DAYS}' day - interval '1' hour
      and minute < now() - interval '{LOOKBACK_DAYS}' day + interval '1' hour
)
select
    c.price as current_price,
    p.price as prior_price,
    (c.price - p.price) / nullif(p.price, 0) * 100 as pct_change
from current_px c
cross join prior_px p
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
