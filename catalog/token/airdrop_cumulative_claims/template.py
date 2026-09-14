# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM = "{{date_from}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

# No distributor address input exists for this tool, so claims are modeled as
# mints of the airdrop token (transfers from the zero address), the common
# pattern for on-chain claim contracts.
sql = f"""
select
    date(block_time) as block_date,
    sum(amount) over (order by block_time) as cumulative_claim,
    to_hex("to") as claim_address
from tokens.transfers
where blockchain = '{CHAIN}'
  and contract_address = from_hex('{contract_hex}')
  and "from" = from_hex('0000000000000000000000000000000000000000')
  and block_time >= date '{DATE_FROM}'
order by block_time
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
