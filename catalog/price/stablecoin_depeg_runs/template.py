# Sandworm Power Toolbox — {{__tool_name}}
import re

TOKEN_SYMBOL = "{{token_symbol}}".strip() or "USDT"
THRESHOLD_PCT = "{{threshold_pct}}".strip() or "5"
CHAIN = "{{chain}}".strip()
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

try:
    threshold = float(THRESHOLD_PCT)
except ValueError:
    raise ValueError(f"Invalid threshold_pct: {THRESHOLD_PCT!r}")
if CHAIN and CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

chain_clause = f"and blockchain = '{CHAIN}'" if CHAIN else ""
date_clause = f"and minute >= date('{DATE_FROM}')" if DATE_FROM else "and minute >= now() - interval '30' day"

sql = f"""
with px as (
    select minute, blockchain, price
    from prices.usd
    where upper(symbol) = upper('{TOKEN_SYMBOL}')
      {chain_clause}
      {date_clause}
),
flagged as (
    select minute, blockchain, abs(price - 1) / 1 * 100 > {threshold} as is_depegged
    from px
),
grouped as (
    select
        minute, blockchain, is_depegged,
        row_number() over (partition by blockchain order by minute)
            - row_number() over (partition by blockchain, is_depegged order by minute) as grp
    from flagged
)
select
    date_trunc('day', min(minute)) as day,
    min(minute) as minute,
    blockchain,
    date_diff('minute', min(minute), max(minute)) + 1 as run_duration
from grouped
where is_depegged
group by blockchain, grp
order by minute
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="minute", y="run_duration")
fig.show()

{{__df_name}}
