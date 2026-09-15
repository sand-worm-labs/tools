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
# Fixed 90-day window (per this tool's own "Holders growth 90d" label) with a
# single day-over-day growth_rate column — distinct from holder_growth_rates,
# which exposes separate 30/60/90-day deltas over a caller-chosen window.
FIXED_WINDOW_DAYS = 90

sql = f"""
with movements as (
    select date_trunc('day', block_time) as day, "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select date_trunc('day', block_time) as day, "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
daily_net as (
    select day, wallet, sum(amt) as net_change
    from movements
    group by day, wallet
),
day_spine as (
    select day from unnest(sequence(current_date - interval '{FIXED_WINDOW_DAYS}' day, current_date, interval '1' day)) as t(day)
),
wallets as (
    select distinct wallet from movements
),
grid as (
    select s.day, w.wallet, coalesce(m.net_change, 0) as net_change
    from day_spine s
    cross join wallets w
    left join daily_net m on m.day = s.day and m.wallet = w.wallet
),
running as (
    select day, wallet, sum(net_change) over (partition by wallet order by day) as balance
    from grid
),
daily_holders as (
    select day, count(distinct wallet) filter (where balance > 0) as holders
    from running
    group by day
)
select
    day,
    holders,
    100.0 * (holders - lag(holders) over (order by day)) / nullif(lag(holders) over (order by day), 0) as growth_rate
from daily_holders
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
