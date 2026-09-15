# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# True "currently holding" count, not just cumulative unique recipients ever
# (see cumulative_holders_timeseries for that simpler cohort view): tracks
# each wallet's running balance and only counts a day when a wallet actually
# crosses the zero-balance line, so total_holders reflects net entries/exits.
sql = f"""
with movements as (
    select "to" as wallet, date_trunc('day', block_time) as day, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select "from" as wallet, date_trunc('day', block_time) as day, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
daily_net as (
    select wallet, day, sum(amt) as net_change
    from movements
    group by wallet, day
),
running as (
    select
        wallet,
        day,
        sum(net_change) over (partition by wallet order by day) as running_balance,
        sum(net_change) over (partition by wallet order by day rows between unbounded preceding and 1 preceding) as prev_balance
    from daily_net
),
transitions as (
    select
        day,
        case
            when running_balance > 0 and coalesce(prev_balance, 0) <= 0 then 1
            when running_balance <= 0 and coalesce(prev_balance, 0) > 0 then -1
            else 0
        end as holder_delta
    from running
),
daily_delta as (
    select day, sum(holder_delta) as net_holder_change
    from transitions
    group by day
)
select
    day as date,
    sum(net_holder_change) over (order by day) as total_holders
from daily_delta
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
