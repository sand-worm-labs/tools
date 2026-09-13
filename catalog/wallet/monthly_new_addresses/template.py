# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {DAYS!r}")

sql = f"""
with all_addrs as (
    select "from" as address, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20'
    union all
    select "to" as address, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20'
),
first_seen as (
    select address, min(block_time) as first_time
    from all_addrs
    group by address
)
select date_trunc('month', first_time) as month, count(*) as new_addresses
from first_seen
where first_time >= now() - interval '{DAYS}' day
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
