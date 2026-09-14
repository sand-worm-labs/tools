# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
TOP_N = "{{top_n}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if TOP_N and not (TOP_N.isdigit() and int(TOP_N) > 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
limit_clause = f"limit {TOP_N}" if TOP_N else ""

# Mints are ERC20 transfers from the zero address; the recipient of that
# transfer is treated as the "minter" (the address newly-issued supply lands on).
sql = f"""
with mints as (
    select "to" as minter, amount, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and "from" = from_hex('0000000000000000000000000000000000000000')
)
select
    to_hex(minter) as minter_address,
    sum(amount) as total_minted,
    min(block_time) as first_mint
from mints
group by 1
order by total_minted desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
