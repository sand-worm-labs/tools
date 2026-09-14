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
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
zero_hex = "0" * 40
date_filter = f"where h.day >= date '{DATE_FROM}'" if DATE_FROM else ""

# Unlike cumulative_token_holders (lifetime "ever received" count, monotonic),
# this tracks currently-held balances: a wallet only counts as a holder on
# days its running balance is positive, so total_holders can fall as people
# exit their position.
sql = f"""
with flows as (
    select date_trunc('day', block_time) as day, "to" as address, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "to" <> from_hex('{zero_hex}')
    union all
    select date_trunc('day', block_time) as day, "from" as address, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" <> from_hex('{zero_hex}')
),
daily_net as (
    select day, address, sum(amt) as net_change
    from flows
    group by day, address
),
balances as (
    select
        day,
        address,
        sum(net_change) over (partition by address order by day) as balance,
        lag(sum(net_change) over (partition by address order by day)) over (partition by address order by day) as prev_balance
    from daily_net
),
new_holder_flags as (
    select day, case when balance > 0 and coalesce(prev_balance, 0) <= 0 then 1 else 0 end as became_holder
    from balances
),
daily_new as (
    select day, sum(became_holder) as new_holders
    from new_holder_flags
    group by day
),
holder_counts as (
    select day, count(*) filter (where balance > 0) as total_holders
    from balances
    group by day
)
select h.day, coalesce(n.new_holders, 0) as new_holders, h.total_holders
from holder_counts h
left join daily_new n on n.day = h.day
{date_filter}
order by h.day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
