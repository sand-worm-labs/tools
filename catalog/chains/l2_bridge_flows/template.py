# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"base", "optimism", "arbitrum", "polygon", "scroll", "linea", "zksync"}
# Only Optimism's official Standard Bridge is backed by a verified, direction-
# labeled Dune table this catalog already relies on elsewhere
# (bridge_optimism.standard_bridge_flows, see bridges.volume). The other
# L2s' native bridges don't have an equivalently verified deposit+withdrawal
# source here yet — raise rather than guess at a table name.
VERIFIED_CHAINS = {"optimism"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")
if CHAIN not in VERIFIED_CHAINS:
    raise ValueError(
        f"No verified official-bridge deposit/withdrawal data source found for chain {CHAIN!r} "
        f"in this catalog yet. Supported: {sorted(VERIFIED_CHAINS)}"
    )

time_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"
limit_clause = f"limit {LIMIT}" if LIMIT else ""

sql = f"""
select
    date_trunc('day', block_time) as day,
    token_symbol,
    sum(case when type = 'deposit' then token_amount_usd else 0 end) as deposits_usd,
    sum(case when type = 'withdrawal' then token_amount_usd else 0 end) as withdrawals_usd,
    sum(case when type = 'deposit' then token_amount_usd else -token_amount_usd end) as net_flow_usd
from bridge_optimism.standard_bridge_flows
where 1 = 1 {time_where}
group by 1, 2
order by 1 desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="day", y="net_flow_usd", color="token_symbol")
fig.show()

{{__df_name}}
