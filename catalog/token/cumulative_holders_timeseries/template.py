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

# Cohort-growth view: a wallet counts here from the day it first ever received
# the token onward, even if it later sold out entirely (unlike
# cumulative_holders_over_time, which tracks true current-holder counts via
# running balances) — this is simply "how many distinct addresses have ever
# touched this token", monotonically non-decreasing by construction.
sql = f"""
with first_receipt as (
    select "to" as wallet, min(date_trunc('day', block_time)) as first_day
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    group by "to"
),
daily as (
    select first_day as day, count(*) as daily_new
    from first_receipt
    group by first_day
)
select
    day as date,
    daily_new,
    sum(daily_new) over (order by day) as cumulative
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
