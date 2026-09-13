# Sandworm Power Toolbox — {{__tool_name}}
# No lookback field exists on this tool, so the window is fixed at 90 days.
CHAIN_TOKEN = {
    "ethereum": "ETH", "base": "ETH", "optimism": "OP", "arbitrum": "ARB",
    "polygon": "MATIC", "bsc": "BNB", "avalanche": "AVAX", "celo": "CELO",
}

raw_chains = "{{chains}}".replace("[", "").replace("]", "").replace('"', "")
chains = [c.strip().lower() for c in raw_chains.split(",") if c.strip()]
if not chains:
    chains = list(CHAIN_TOKEN)

unknown = [c for c in chains if c not in CHAIN_TOKEN]
if unknown:
    raise ValueError(f"Unsupported chain(s): {unknown!r}")

symbols = sorted({CHAIN_TOKEN[c] for c in chains})
symbol_list_sql = ", ".join(f"'{s}'" for s in symbols)

sql = f"""
with daily as (
    select date_trunc('day', minute) as time, symbol, avg(price) as price
    from prices.usd
    where symbol in ({symbol_list_sql})
      and minute >= now() - interval '90' day
    group by 1, 2
),
normalized as (
    select
        time, symbol,
        price / first_value(price) over (partition by symbol order by time) * 100 as normalized_price
    from daily
)
select time, avg(normalized_price) as index_value
from normalized
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="time", y=['index_value'])
fig.show()

{{__df_name}}
