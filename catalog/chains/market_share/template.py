# Sandworm Power Toolbox — {{__tool_name}}
DAYS = "{{days}}"
GRANULARITY = "{{granularity}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"base", "optimism", "arbitrum", "polygon", "scroll", "linea", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ALLOWED_GRANULARITY = {"hour", "day", "week"}

raw_chains = "{{chains}}".replace("[", "").replace("]", "").replace('"', "")
chains = [c.strip().lower() for c in raw_chains.split(",") if c.strip()]
if not chains:
    raise ValueError("At least one chain must be selected")

unknown = [c for c in chains if c not in ALLOWED_CHAINS]
if unknown:
    raise ValueError(f"Unsupported chain(s): {unknown!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if GRANULARITY not in ALLOWED_GRANULARITY:
    raise ValueError(f"Unsupported granularity: {GRANULARITY!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""

# TVL isn't included here — this catalog doesn't have a verified,
# chain-agnostic TVL source to join against — so share is measured by
# transaction volume and fees paid instead.
per_chain_sql = [
    f"""
    select
        '{c}' as chain,
        date_trunc('{GRANULARITY}', block_time) as time,
        count(*) as tx_count,
        sum(gas_used * gas_price) / 1e18 as total_fees_native
    from {c}.transactions
    where 1 = 1
      {time_where}
    group by 2
    """
    for c in chains
]
union_sql = "\nunion all\n".join(per_chain_sql)

sql = f"""
with activity as (
    {union_sql}
)
select
    time,
    chain,
    tx_count,
    tx_count / sum(tx_count) over (partition by time) as tx_share
from activity
order by time desc, tx_share desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.area({{__df_name}}, x="time", y="tx_share", color="chain")
fig.show()

{{__df_name}}
