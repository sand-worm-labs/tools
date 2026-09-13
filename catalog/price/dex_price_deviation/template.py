# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_SYMBOL = "{{token_symbol}}".strip()
DATE_FROM = "{{date_from}}"
THRESHOLD_USD = "{{threshold_usd}}".strip() or "0.01"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
try:
    threshold = float(THRESHOLD_USD)
except ValueError:
    raise ValueError(f"Invalid threshold_usd: {THRESHOLD_USD!r}")

sql = f"""
with dex_px as (
    select
        date_trunc('minute', block_time) as ts,
        blockchain,
        amount_usd / nullif(token_bought_amount, 0) as trade_price
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_symbol = '{TOKEN_SYMBOL}'
      and block_time >= date('{DATE_FROM}')
),
oracle_px as (
    select date_trunc('minute', minute) as ts, avg(price) as oracle_price
    from prices.usd
    where upper(symbol) = upper('{TOKEN_SYMBOL}')
      and minute >= date('{DATE_FROM}')
    group by 1
),
joined as (
    select
        d.ts as timestamp,
        d.blockchain,
        d.trade_price - o.oracle_price as error
    from dex_px d
    join oracle_px o on o.ts = d.ts
)
select
    timestamp,
    blockchain,
    error,
    stddev(error) over () as stddev,
    abs(error) > {threshold} as is_outlier
from joined
order by timestamp
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.scatter({{__df_name}}, x="timestamp", y="error", color="is_outlier")
fig.show()

{{__df_name}}
