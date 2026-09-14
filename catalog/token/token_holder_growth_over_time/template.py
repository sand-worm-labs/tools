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

# "first transfer interaction" = the day a wallet appears as sender or
# receiver for the very first time ever for this token.
sql = f"""
with activity as (
    select block_time, "from" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select block_time, "to" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
first_seen as (
    select wallet, min(date_trunc('day', block_time)) as first_day
    from activity
    group by wallet
),
daily_new as (
    select first_day as date, count(*) as daily_new
    from first_seen
    group by first_day
)
select
    date,
    daily_new,
    sum(daily_new) over (order by date) as cumulative_holders
from daily_new
order by date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
