# Sandworm Power Toolbox — {{__tool_name}}
# "pump.fun" (a Solana-only bonding-curve launchpad) generalized to any EVM
# chain: a token "bonds" once it starts trading on a DEX after deployment.
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()
TOP_N = "{{top_n}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if LOOKBACK_DAYS and (not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
if TOP_N and (not TOP_N.isdigit() or int(TOP_N) <= 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

lookback_days = int(LOOKBACK_DAYS) if LOOKBACK_DAYS else 60
top_n = int(TOP_N) if TOP_N else 100

sql = f"""
with created_tokens as (
    select tx."from" as creator, tx.contract_address as token_address, tx.block_time as launch_time
    from {CHAIN}.transactions tx
    join tokens.erc20 e on e.blockchain = '{CHAIN}' and e.contract_address = tx.contract_address
    where tx."to" is null
      and tx.success = true
      and tx.block_time >= now() - interval '{lookback_days}' day
),
bonded as (
    select
        ct.creator,
        ct.launch_time,
        exists (
            select 1
            from dex.trades d
            where d.blockchain = '{CHAIN}'
              and (d.token_bought_address = ct.token_address or d.token_sold_address = ct.token_address)
              and d.block_time >= ct.launch_time
        ) as is_bonded
    from created_tokens ct
),
per_creator as (
    select
        creator,
        min(launch_time) as launch_date,
        count(*) as total_launches,
        sum(case when is_bonded then 1 else 0 end) as bonded_count
    from bonded
    group by creator
)
select
    '0x' || to_hex(creator) as creator,
    cast(launch_date as date) as launch_date,
    100.0 * bonded_count / nullif(total_launches, 0) as bonding_pct,
    rank() over (order by 100.0 * bonded_count / nullif(total_launches, 0) desc) as rank
from per_creator
order by bonding_pct desc
limit {top_n}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
