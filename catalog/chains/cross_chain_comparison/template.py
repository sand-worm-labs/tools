# Sandworm Power Toolbox — {{__tool_name}}
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche",
                   "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}

raw_chains = "{{chains}}".replace("[", "").replace("]", "").replace('"', "")
chains = [c.strip().lower() for c in raw_chains.split(",") if c.strip()]
if not chains:
    raise ValueError("At least one chain must be selected")

unknown = [c for c in chains if c not in ALLOWED_CHAINS]
if unknown:
    raise ValueError(f"Unsupported chain(s): {unknown!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""

# TPS is approximated as tx_count / 86400 (seconds/day) rather than measured
# against actual block-time span, which is close enough at a daily grain and
# avoids an extra join against each chain's blocks table.
per_chain_sql = [
    f"""
    select
        '{c}' as chain,
        date_trunc('day', block_time) as day,
        count(*) as tx_count,
        count(*) / 86400.0 as avg_tps,
        count(distinct "from") as dau,
        sum(gas_used * gas_price) / 1e18 as total_fees_native
    from {c}.transactions
    where 1 = 1
      {time_where}
    group by 2
    """
    for c in chains
]

sql = "\nunion all\n".join(per_chain_sql) + f"\norder by day desc, chain\n{limit_clause}"

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y="dau", color="chain")
fig.show()

{{__df_name}}
