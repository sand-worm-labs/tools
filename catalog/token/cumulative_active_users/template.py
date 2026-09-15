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
if LOOKBACK_DAYS and (not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

lookback_days = int(LOOKBACK_DAYS) if LOOKBACK_DAYS else 30
contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with participants as (
    select block_time, "to" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{lookback_days}' day
    union all
    select block_time, "from" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{lookback_days}' day
),
daily as (
    select date_trunc('day', block_time) as day, count(distinct wallet) as total_user
    from participants
    group by day
),
first_seen as (
    select wallet, min(date_trunc('day', block_time)) as first_day
    from participants
    group by wallet
),
new_per_day as (
    select first_day as day, count(*) as new_users
    from first_seen
    group by first_day
)
select
    cast(d.day as timestamp) as evt_block_time,
    d.total_user,
    sum(coalesce(n.new_users, 0)) over (order by d.day) as cumulative_total
from daily d
left join new_per_day n on n.day = d.day
order by d.day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
