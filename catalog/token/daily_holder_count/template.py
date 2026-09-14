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
if not LOOKBACK_DAYS:
    LOOKBACK_DAYS = "365"
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
zero_hex = "0" * 40

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
    select day, address, sum(net_change) over (partition by address order by day) as balance
    from daily_net
),
holder_counts as (
    select day, count(*) filter (where balance > 0) as holder_count
    from balances
    group by day
)
select
    day,
    holder_count,
    (holder_count - lag(holder_count) over (order by day))
        / cast(nullif(lag(holder_count) over (order by day), 0) as double) as growth_rate
from holder_counts
where day >= now() - interval '{LOOKBACK_DAYS}' day
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
