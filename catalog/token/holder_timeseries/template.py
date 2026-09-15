# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
lookback_days_val = int(LOOKBACK_DAYS)

# unique_wallets is the balance-positive holder count for that day (can go
# down); cumulative_holders is the monotonically non-decreasing count of
# every wallet that has ever received the token by that day, regardless of
# whether it still holds a balance — the two together are what sets this
# tool apart from holder_growth_timeseries (unique_wallets only) and
# holder_dynamics_over_time (no daily_change/cumulative pair).
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
    select day from unnest(sequence(current_date - interval '{lookback_days_val}' day, current_date, interval '1' day)) as t(day)
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
first_seen as (
    select "to" as wallet, min(date_trunc('day', block_time)) as first_seen_day
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    group by "to"
),
daily_unique as (
    select day, count(distinct wallet) filter (where balance > 0) as unique_wallets
    from running
    group by day
),
daily_cumulative as (
    select s.day, count(distinct f.wallet) as cumulative_holders
    from day_spine s
    left join first_seen f on f.first_seen_day <= s.day
    group by s.day
)
select
    u.day,
    u.unique_wallets,
    u.unique_wallets - lag(u.unique_wallets) over (order by u.day) as daily_change,
    c.cumulative_holders
from daily_unique u
join daily_cumulative c on c.day = u.day
order by u.day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
