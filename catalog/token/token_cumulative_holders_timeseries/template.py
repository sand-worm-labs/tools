# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}".strip()
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# Same "ever received the token" holder definition as token_cumulative_holders,
# but this variant only surfaces the running total (no daily_new column).
sql = f"""
with first_seen as (
    select "to" as address, min(block_date) as first_date
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token_hex}')
    group by "to"
),
daily_new as (
    select first_date as date, count(*) as new_holders
    from first_seen
    group by first_date
)
select
    date,
    sum(new_holders) over (order by date) as cumulative_holders
from daily_new
order by date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
