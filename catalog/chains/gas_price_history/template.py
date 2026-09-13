# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
DAYS = "{{days}}"
GRANULARITY = "{{granularity}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche",
                   "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ALLOWED_GRANULARITY = {"hour", "day", "week"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if GRANULARITY not in ALLOWED_GRANULARITY:
    raise ValueError(f"Unsupported granularity: {GRANULARITY!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""

sql = f"""
select
    date_trunc('{GRANULARITY}', block_time) as time,
    avg(gas_price) / 1e9 as avg_gas_price_gwei,
    approx_percentile(gas_price, 0.5) / 1e9 as p50_gas_price_gwei,
    approx_percentile(gas_price, 0.9) / 1e9 as p90_gas_price_gwei,
    approx_percentile(gas_price, 0.99) / 1e9 as p99_gas_price_gwei
from {CHAIN}.transactions
where 1 = 1
  {time_where}
group by 1
order by 1 desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="time", y=["avg_gas_price_gwei", "p50_gas_price_gwei", "p90_gas_price_gwei", "p99_gas_price_gwei"])
fig.show()

{{__df_name}}
