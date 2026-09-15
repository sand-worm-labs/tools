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

# Every address that ever received the token, tagged by its first-receipt
# day — the base table cohort-retention analyses group by, regardless of
# whether that wallet still holds a positive balance today.
sql = f"""
select "to" as address, min(date_trunc('day', block_time)) as first_seen_day
from tokens.transfers
where blockchain = '{CHAIN}'
  and token_standard = 'erc20'
  and contract_address = from_hex('{token_hex}')
group by "to"
order by first_seen_day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
