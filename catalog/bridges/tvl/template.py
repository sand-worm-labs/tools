# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
PROTOCOL = "{{protocol}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "optimism", "arbitrum", "base", "polygon", "bsc"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
# TVL only means something for lock-and-mint native bridges, where a deposit
# locks collateral and a withdrawal releases it. Across/Synapse/Stargate/Hop
# are relayer/liquidity-pool bridges — there's no "locked balance" concept to
# compute from deposit/withdrawal counts, so they aren't offered here.
SUPPORTED_PROTOCOLS = {"optimism_bridge", "arbitrum_bridge"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")
if PROTOCOL not in SUPPORTED_PROTOCOLS:
    raise ValueError(
        f"bridges.tvl only supports lock-based native bridges: {sorted(SUPPORTED_PROTOCOLS)}. "
        f"{PROTOCOL!r} is either a liquidity-pool bridge (no locked-balance concept) or has no "
        f"verified data source in this catalog yet."
    )

limit_clause = f"limit {LIMIT}" if LIMIT else ""

if PROTOCOL == "optimism_bridge":
    if CHAIN != "optimism":
        raise ValueError("optimism_bridge TVL is only computable from Optimism-side data (set chain to 'optimism')")
    time_where = "" if DAYS == "all" else "and day >= now() - interval '{}' day".format(DAYS)
    sql = f"""
    with daily_net as (
        select
            date_trunc('day', block_time) as day,
            sum(case
                when destination_chain_name = 'optimism' then token_amount_usd
                when destination_chain_name = 'ethereum' then -token_amount_usd
                else 0
            end) as net_flow_usd
        from bridge_optimism.standard_bridge_flows
        group by 1
    )
    select
        day,
        sum(net_flow_usd) over (order by day) as tvl_usd
    from daily_net
    where 1 = 1 {time_where}
    order by day desc
    {limit_clause}
    """
else:  # arbitrum_bridge, locked on ethereum
    if CHAIN != "ethereum":
        raise ValueError("arbitrum_bridge TVL is only computable from Ethereum-side data (set chain to 'ethereum')")
    time_where = "" if DAYS == "all" else "and day >= now() - interval '{}' day".format(DAYS)
    sql = f"""
    with inflow as (
        select date_trunc('day', d.block_time) as day,
               sum((d.deposit_amount_raw / power(10, coalesce(e.decimals, 18))) * p.price) as amt
        from bridges_ethereum.arbitrum_native_v1_deposits d
        left join tokens.erc20 e on e.blockchain = 'ethereum' and e.contract_address = d.deposit_token_address
        left join prices.usd p on p.blockchain = 'ethereum' and p.contract_address = d.deposit_token_address
            and p.minute = date_trunc('minute', d.block_time)
        group by 1
    ),
    outflow as (
        select date_trunc('day', w.block_time) as day,
               sum((w.withdrawal_amount_raw / power(10, coalesce(e.decimals, 18))) * p.price) as amt
        from bridges_ethereum.arbitrum_native_v1_withdrawals w
        left join tokens.erc20 e on e.blockchain = 'ethereum' and e.contract_address = w.withdrawal_token_address
        left join prices.usd p on p.blockchain = 'ethereum' and p.contract_address = w.withdrawal_token_address
            and p.minute = date_trunc('minute', w.block_time)
        group by 1
    ),
    combined as (
        select day, sum(amt) as net_flow_usd
        from (
            select day, amt from inflow
            union all
            select day, -amt as amt from outflow
        )
        group by day
    ),
    running as (
        select day, sum(net_flow_usd) over (order by day) as tvl_usd
        from combined
    )
    select day, tvl_usd
    from running
    where 1 = 1 {time_where}
    order by day desc
    {limit_clause}
    """

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y="tvl_usd")
fig.show()

{{__df_name}}
