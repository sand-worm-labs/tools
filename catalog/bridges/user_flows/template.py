# Sandworm Power Toolbox — {{__tool_name}}
PROTOCOL = "{{protocol}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_PROTOCOLS = {"all", "optimism_bridge", "arbitrum_bridge", "base_bridge", "across", "stargate", "hop", "synapse"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
NO_DATA_PROTOCOLS = {"stargate", "base_bridge"}

if PROTOCOL not in ALLOWED_PROTOCOLS:
    raise ValueError(f"Unsupported protocol: {PROTOCOL!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")
if PROTOCOL in NO_DATA_PROTOCOLS:
    raise ValueError(
        f"No verified on-chain data source found for protocol {PROTOCOL!r} in this catalog yet. "
        f"Supported: {sorted(ALLOWED_PROTOCOLS - NO_DATA_PROTOCOLS)}"
    )

limit_clause = f"limit {LIMIT}" if LIMIT else ""

# Curated, individually-verified subset (see volume/template.py) — Dune's
# bridges sector covers dozens more protocols per chain not included here.
DEPOSIT_TABLES = {
    "ethereum": ["across_v3_deposits", "synapse_rfq_deposits", "arbitrum_native_v1_deposits"],
    "optimism": ["across_v3_deposits", "synapse_rfq_deposits"],
    "arbitrum": ["across_v3_deposits", "synapse_rfq_deposits"],
    "base": ["across_v3_deposits", "synapse_rfq_deposits"],
    "polygon": ["across_v3_deposits"],
    "bnb": ["across_v3_deposits"],
}
PROTOCOL_BRIDGE_NAMES = {"across": ["Across"], "synapse": ["Synapse"], "arbitrum_bridge": ["Arbitrum"]}

if PROTOCOL == "hop":
    time_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"
    sql = f"""
    select
        source_chain_name as source_chain,
        destination_chain_name as dest_chain,
        sum(token_amount_usd) as volume_usd,
        count(*) as transfer_count
    from hop_protocol.flows
    where 1 = 1 {time_where}
    group by 1, 2
    order by volume_usd desc
    {limit_clause}
    """
elif PROTOCOL == "optimism_bridge":
    time_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"
    sql = f"""
    select
        source_chain_name as source_chain,
        destination_chain_name as dest_chain,
        sum(token_amount_usd) as volume_usd,
        count(*) as transfer_count
    from bridge_optimism.standard_bridge_flows
    where 1 = 1 {time_where}
    group by 1, 2
    order by volume_usd desc
    {limit_clause}
    """
else:
    bridge_name_filter = ""
    if PROTOCOL in PROTOCOL_BRIDGE_NAMES:
        names = ", ".join(f"'{n}'" for n in PROTOCOL_BRIDGE_NAMES[PROTOCOL])
        bridge_name_filter = f"and bridge_name in ({names})"
    time_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"

    union_parts = [
        f"select block_time, bridge_name, deposit_token_address as token_address, deposit_amount_raw as amount_raw, "
        f"deposit_chain, withdrawal_chain, '{chain}' as chain "
        f"from bridges_{chain}.{t} where 1 = 1 {bridge_name_filter} {time_where}"
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
            d.deposit_chain,
            d.withdrawal_chain,
            (d.amount_raw / power(10, coalesce(e.decimals, 18))) * p.price as amount_usd
        from raw_deposits d
        left join tokens.erc20 e on e.blockchain = d.chain and e.contract_address = d.token_address
        left join prices.usd p on p.blockchain = d.chain and p.contract_address = d.token_address
            and p.minute = date_trunc('minute', d.block_time)
    )
    select
        deposit_chain as source_chain,
        withdrawal_chain as dest_chain,
        sum(amount_usd) as volume_usd,
        count(*) as transfer_count
    from priced
    group by 1, 2
    order by volume_usd desc
    {limit_clause}
    """

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="source_chain", y="volume_usd", color="dest_chain")
fig.show()

{{__df_name}}
