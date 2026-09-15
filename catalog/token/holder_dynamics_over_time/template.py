# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}, expected YYYY-MM-DD")

token_hex = CONTRACT_ADDRESS[2:].lower()
# Open-ended window: runs from date_from (or the token's first-ever transfer
# day, when omitted) through today — unlike holder_count_timeseries, which
# takes a closed date_range.
start_day_expr = (
    f"date('{DATE_FROM}')"
    if DATE_FROM
    else f"(select min(date_trunc('day', block_time)) from tokens.transfers "
         f"where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token_hex}'))"
)

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
    select day from unnest(sequence({start_day_expr}, current_date, interval '1' day)) as t(day)
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
)
select day as date, count(distinct wallet) filter (where balance > 0) as holder_count
from running
group by day
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
