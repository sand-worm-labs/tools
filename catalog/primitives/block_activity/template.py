# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")

# blocks.time is assumed to be the block timestamp column (distinct from
# transactions.block_time used elsewhere in this catalog) — verify against
# the live schema before relying on this.
tx_time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS} days'"
block_time_where = "" if DAYS == "all" else f"AND time >= NOW() - INTERVAL '{DAYS} days'"

sql = f"""
with per_block as (
    select
        block_number,
        count(*) as tx_count
    from {CHAIN}.transactions
    where 1 = 1
      {tx_time_where}
    group by block_number
)
select
    date_trunc('hour', b.time) as hour,
    count(distinct b.number) as block_count,
    coalesce(sum(p.tx_count), 0) as tx_count,
    avg(coalesce(p.tx_count, 0)) as avg_txs_per_block,
    avg(b.gas_used) as avg_gas_used,
    avg(b.gas_limit) as avg_gas_limit,
    avg(cast(b.gas_used as double) / nullif(b.gas_limit, 0)) as avg_gas_utilization,
    avg(b.base_fee_per_gas) / 1e9 as avg_base_fee_gwei
from {CHAIN}.blocks b
left join per_block p on p.block_number = b.number
where 1 = 1
  {block_time_where}
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
