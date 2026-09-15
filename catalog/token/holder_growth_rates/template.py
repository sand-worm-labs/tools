# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DECIMALS = "{{decimals}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DECIMALS.isdigit():
    raise ValueError(f"Invalid decimals: {DECIMALS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
decimals_val = int(DECIMALS)
lookback_days_val = int(LOOKBACK_DAYS)
# A "holder" here means a wallet holding at least one whole token (dust
# filtered out), using the caller-supplied decimals to define that raw-unit
# cutoff rather than joining tokens.erc20.
min_balance_raw = 10**decimals_val

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
daily_holders as (
    select day, count(distinct wallet) filter (where balance >= {min_balance_raw}) as holders
    from running
    group by day
)
select
    day,
    holders,
    holders - lag(holders, 30) over (order by day) as growth_30d,
    holders - lag(holders, 60) over (order by day) as growth_60d,
    holders - lag(holders, 90) over (order by day) as growth_90d
from daily_holders
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
