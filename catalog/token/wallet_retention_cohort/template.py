# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}"
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# total_unique is the running count of distinct wallets ever seen up to that
# day (via each wallet's first-active day), not a lifetime total independent
# of the lookback window.
sql = f"""
with activity as (
    select "to" as wallet, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    union all
    select "from" as wallet, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
daily_active as (
    select date_trunc('day', block_time) as day, count(distinct wallet) as unique_wallets
    from activity
    group by 1
),
first_seen as (
    select wallet, min(date_trunc('day', block_time)) as first_day
    from activity
    group by wallet
),
new_wallets as (
    select first_day as day, count(*) as new_count
    from first_seen
    group by 1
),
cumulative as (
    select day, sum(new_count) over (order by day) as total_unique
    from new_wallets
)
select
    d.day,
    d.unique_wallets,
    c.total_unique,
    cast(d.unique_wallets as double) / nullif(c.total_unique, 0) as retention_rate
from daily_active d
join cumulative c on d.day = c.day
order by d.day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
