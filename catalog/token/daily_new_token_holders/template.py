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

# "First interaction" = first day a wallet ever received the token (first
# incoming transfer), regardless of whether it still holds a balance today.
sql = f"""
with first_receipt as (
    select "to" as wallet, min(date_trunc('day', block_time)) as first_day
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    group by "to"
)
select
    first_day as date,
    count(*) as new_holders
from first_receipt
group by first_day
order by first_day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
