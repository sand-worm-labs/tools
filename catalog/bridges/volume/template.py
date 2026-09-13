# Sandworm Power Toolbox — {{__tool_name}}
SOURCE_CHAIN = "{{source_chain}}"
DEST_CHAIN = "{{dest_chain}}"
PROTOCOL = "{{protocol}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "optimism", "arbitrum", "base", "polygon", "bsc"}
ALLOWED_PROTOCOLS = {"all", "optimism_bridge", "arbitrum_bridge", "base_bridge", "across", "stargate", "hop", "synapse"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
# Dune's bridges_<chain>.* schemas name this chain "bnb", not "bsc".
CHAIN_SCHEMA = {"ethereum": "ethereum", "optimism": "optimism", "arbitrum": "arbitrum", "base": "base", "polygon": "polygon", "bsc": "bnb"}
# Curated, individually-verified subset of what Dune's "bridges" sector actually
# models per chain (dozens of other protocols exist there too, e.g. CCTP, Celer,
# Connext, LayerZero — not included here since each would need its own
# verification pass). "hop" and "optimism_bridge" live in separate, differently
# shaped tables and are handled as their own branch below.
DEPOSIT_TABLES = {
    "ethereum": ["across_v3_deposits", "synapse_rfq_deposits", "arbitrum_native_v1_deposits"],
    "optimism": ["across_v3_deposits", "synapse_rfq_deposits"],
    "arbitrum": ["across_v3_deposits", "synapse_rfq_deposits"],
    "base": ["across_v3_deposits", "synapse_rfq_deposits"],
    "polygon": ["across_v3_deposits"],
    "bsc": ["across_v3_deposits"],
}
PROTOCOL_BRIDGE_NAMES = {"across": ["Across"], "synapse": ["Synapse"], "arbitrum_bridge": ["Arbitrum"]}
NO_DATA_PROTOCOLS = {"stargate", "base_bridge"}

if SOURCE_CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported source_chain: {SOURCE_CHAIN!r}")
if DEST_CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported dest_chain: {DEST_CHAIN!r}")
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
source_schema = CHAIN_SCHEMA[SOURCE_CHAIN]

if PROTOCOL == "hop":
    if SOURCE_CHAIN != "optimism":
        raise ValueError("Hop is only supported here via its Optimism deployment (source_chain must be 'optimism')")
    time_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"
    sql = f"""
    select
        date_trunc('day', block_time) as day,
        'Hop' as bridge_name,
        token_symbol,
        sum(token_amount_usd) as volume_usd,
        count(*) as transfer_count
    from hop_protocol.flows
    where destination_chain_name = '{DEST_CHAIN}'
      {time_where}
    group by 1, 2, 3
    order by 1 desc
    {limit_clause}
    """
elif PROTOCOL == "optimism_bridge":
    if "optimism" not in (SOURCE_CHAIN, DEST_CHAIN):
        raise ValueError("optimism_bridge only has data on Optimism (set source_chain or dest_chain to 'optimism')")
    time_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"
    sql = f"""
    select
        date_trunc('day', block_time) as day,
        'Optimism Bridge' as bridge_name,
        token_symbol,
        sum(token_amount_usd) as volume_usd,
        count(*) as transfer_count
    from bridge_optimism.standard_bridge_flows
    where 1 = 1 {time_where}
    group by 1, 2, 3
    order by 1 desc
    {limit_clause}
    """
else:
    tables = DEPOSIT_TABLES.get(SOURCE_CHAIN, [])
    if not tables:
        raise ValueError(f"No bridge deposit tables available for source_chain {SOURCE_CHAIN!r}")

    bridge_name_filter = ""
    if PROTOCOL in PROTOCOL_BRIDGE_NAMES:
        names = ", ".join(f"'{n}'" for n in PROTOCOL_BRIDGE_NAMES[PROTOCOL])
        bridge_name_filter = f"and bridge_name in ({names})"
    time_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"

    # Filters pushed into each branch (not applied after the union) so each
    # table can be pruned by block_date before the union/join runs.
    union_sql = "\nunion all\n".join(
        f"select block_time, bridge_name, deposit_token_address as token_address, deposit_amount_raw as amount_raw "
        f"from bridges_{source_schema}.{t} "
        f"where withdrawal_chain = '{DEST_CHAIN}' {bridge_name_filter} {time_where}"
        for t in tables
    )

    sql = f"""
    with raw_deposits as (
        {union_sql}
    ),
    priced as (
        select
            d.block_time,
            d.bridge_name,
            e.symbol as token_symbol,
            (d.amount_raw / power(10, coalesce(e.decimals, 18))) * p.price as amount_usd
        from raw_deposits d
        left join tokens.erc20 e on e.blockchain = '{source_schema}' and e.contract_address = d.token_address
        left join prices.usd p on p.blockchain = '{source_schema}'
            and p.contract_address = d.token_address
            and p.minute = date_trunc('minute', d.block_time)
    )
    select
        date_trunc('day', block_time) as day,
        bridge_name,
        token_symbol,
        sum(amount_usd) as volume_usd,
        count(*) as transfer_count
    from priced
    group by 1, 2, 3
    order by 1 desc
    {limit_clause}
    """

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="day", y="volume_usd", color="bridge_name")
fig.show()

{{__df_name}}
