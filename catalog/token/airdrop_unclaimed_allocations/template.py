# Sandworm Power Toolbox — {{__tool_name}}
# "Allocation events" generalized to: each ERC20 transfer the distributor
# contract sends out is one recipient's claim of their airdrop allocation.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
CLAIMER_ADDRESS = "{{claimer_address}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if CLAIMER_ADDRESS and not ADDRESS_RE.match(CLAIMER_ADDRESS):
    raise ValueError(f"Invalid claimer_address: {CLAIMER_ADDRESS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
claimer_filter = ""
if CLAIMER_ADDRESS:
    claimer_filter = f"and \"to\" = from_hex('{CLAIMER_ADDRESS[2:].lower()}')"

sql = f"""
select
    amount as allocation,
    tx_hash,
    block_time
from tokens.transfers
where blockchain = '{CHAIN}'
  and token_standard = 'erc20'
  and "from" = from_hex('{contract_hex}')
  {claimer_filter}
order by block_time desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
