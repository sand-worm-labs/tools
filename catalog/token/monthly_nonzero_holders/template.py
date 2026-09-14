# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
MIN_NATIVE = "{{min_native}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
# Dune's raw <chain>.traces schema names diverge from our chain keys for these two.
CHAIN_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not MIN_NATIVE.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid min_native: {MIN_NATIVE!r}")

schema = CHAIN_SCHEMA[CHAIN]
min_wei = int(float(MIN_NATIVE) * 1e18)

sql = f"""
with movements as (
    select block_time, "to" as address, cast(value as double) as amt
    from {schema}.traces
    where success = true and value > uint256 '0'
    union all
    select block_time, "from" as address, -cast(value as double) as amt
    from {schema}.traces
    where success = true and value > uint256 '0'
),
monthly_net as (
    select date_trunc('month', block_time) as month, address, sum(amt) as net_change
    from movements
    group by 1, 2
),
running as (
    select month, address, sum(net_change) over (partition by address order by month) as balance
    from monthly_net
)
select month, count(distinct address) as non_zero_addresses
from running
where balance >= {min_wei}
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
