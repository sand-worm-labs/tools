# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM = "{{date_from}}".strip()
INTERVAL = "{{interval}}" or "day"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}, expected YYYY-MM-DD")

token_hex = CONTRACT_ADDRESS[2:].lower()
date_filter = f"and block_time >= date '{DATE_FROM}'" if DATE_FROM else ""

# "holder count" here means wallets active (sender or receiver) in the bucket,
# not a full running-balance snapshot — see token_holders_timeseries for the
# balance-based variant.
sql = f"""
with activity as (
    select date_trunc('{INTERVAL}', block_time) as day, "from" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      {date_filter}
    union all
    select date_trunc('{INTERVAL}', block_time) as day, "to" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      {date_filter}
),
daily as (
    select day, count(distinct wallet) as unique_wallets
    from activity
    group by day
)
select
    day,
    unique_wallets,
    unique_wallets - lag(unique_wallets) over (order by day) as daily_change
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
