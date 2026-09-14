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
date_filter = f"where date >= date '{DATE_FROM}'" if DATE_FROM else ""

sql = f"""
with first_seen as (
    select "to" as holder, min(date_trunc('day', block_time)) as first_day
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "to" <> from_hex('{zero_hex}')
    group by "to"
),
daily as (
    select first_day as date, count(*) as daily_new
    from first_seen
    group by first_day
),
cumulative as (
    select date, daily_new, sum(daily_new) over (order by date) as cumulative_holders
    from daily
)
select date, daily_new, cumulative_holders
from cumulative
{date_filter}
order by date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
