# Sandworm Power Toolbox — {{__tool_name}}
DAYS = "{{days}}"

ALLOWED_CHAINS = {"base", "optimism", "arbitrum", "polygon", "scroll", "linea", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}

raw_chains = "{{chains}}".replace("[", "").replace("]", "").replace('"', "")
chains = sorted({c.strip().lower() for c in raw_chains.split(",") if c.strip()})
if len(chains) < 2:
    raise ValueError("Select at least two chains to measure overlap")

unknown = [c for c in chains if c not in ALLOWED_CHAINS]
if unknown:
    raise ValueError(f"Unsupported chain(s): {unknown!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS}' DAY"

per_chain_sql = [
    f"""
    select distinct "from" as wallet, '{c}' as chain
    from {c}.transactions
    where 1 = 1
      {time_where}
    """
    for c in chains
]
union_sql = "\nunion all\n".join(per_chain_sql)

sql = f"""
with per_chain_wallets as (
    {union_sql}
),
wallet_reach as (
    select wallet, count(distinct chain) as chain_count
    from per_chain_wallets
    group by wallet
)
select chain_count, count(*) as wallet_count
from wallet_reach
group by chain_count
order by chain_count desc
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="chain_count", y="wallet_count")
fig.show()

{{__df_name}}
