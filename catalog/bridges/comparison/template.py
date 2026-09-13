# Sandworm Power Toolbox — {{__tool_name}}
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}

if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

limit_clause = f"limit {LIMIT}" if LIMIT else ""

# Curated, individually-verified subset (see volume/template.py) — Dune's
# bridges sector covers dozens more protocols per chain not included here.
DEPOSIT_TABLES = {
    "ethereum": ["across_v3_deposits", "synapse_rfq_deposits"],
    "optimism": ["across_v3_deposits", "synapse_rfq_deposits"],
    "arbitrum": ["across_v3_deposits", "synapse_rfq_deposits"],
    "base": ["across_v3_deposits", "synapse_rfq_deposits"],
    "polygon": ["across_v3_deposits"],
    "bnb": ["across_v3_deposits"],
}

# Time filter pushed into each branch (not applied after the union) so each
# table can be pruned by block_date before the union/join runs.
pool_time_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"
hop_time_where = "" if DAYS == "all" else f"where block_time >= now() - interval '{DAYS}' day"
op_time_where = "" if DAYS == "all" else f"where block_time >= now() - interval '{DAYS}' day"

union_parts = [
    f"select block_time, bridge_name, sender, "
    f"deposit_token_address as token_address, deposit_amount_raw as amount_raw, '{chain}' as chain "
    f"from bridges_{chain}.{t} where 1 = 1 {pool_time_where}"
    for chain, tables in DEPOSIT_TABLES.items()
    for t in tables
]
union_sql = "\nunion all\n".join(union_parts)

sql = f"""
with raw_deposits as (
    {union_sql}
),
priced as (
    select
        d.bridge_name,
        d.sender,
        (d.amount_raw / power(10, coalesce(e.decimals, 18))) * p.price as amount_usd
    from raw_deposits d
    left join tokens.erc20 e on e.blockchain = d.chain and e.contract_address = d.token_address
    left join prices.usd p on p.blockchain = d.chain and p.contract_address = d.token_address
        and p.minute = date_trunc('minute', d.block_time)
),
pool_bridges as (
    select bridge_name, sum(amount_usd) as volume_usd, count(distinct sender) as unique_users,
           cast(null as double) as fee_usd
    from priced
    group by 1
),
hop_bridge as (
    select 'Hop' as bridge_name, sum(token_amount_usd) as volume_usd, count(distinct sender) as unique_users,
           sum(fee_amount_usd) as fee_usd
    from hop_protocol.flows
    {hop_time_where}
),
op_bridge as (
    select 'Optimism Bridge' as bridge_name, sum(token_amount_usd) as volume_usd, count(distinct sender) as unique_users,
           cast(null as double) as fee_usd
    from bridge_optimism.standard_bridge_flows
    {op_time_where}
)
select * from pool_bridges
union all
select * from hop_bridge
union all
select * from op_bridge
order by volume_usd desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="bridge_name", y="volume_usd")
fig.show()

{{__df_name}}
