# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

# No contract_address input on this tool: it tracks unique ERC20 holder
# activity across the whole chain, not one token.
sql = f"""
with movements as (
    select date_trunc('day', block_time) as day, "to" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    union all
    select date_trunc('day', block_time) as day, "from" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
daily_active as (
    select day, count(distinct wallet) as unique_holders
    from movements
    group by day
)
select
    day,
    unique_holders,
    unique_holders - lag(unique_holders) over (order by day) as daily_change
from daily_active
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
