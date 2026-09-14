# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
FROM_ADDRESS = "{{from_address}}"
TOP_N = "{{top_n}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not ADDRESS_RE.match(FROM_ADDRESS):
    raise ValueError(f"Invalid from_address: {FROM_ADDRESS!r}")
if TOP_N and not (TOP_N.isdigit() and int(TOP_N) > 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
from_hex_val = FROM_ADDRESS[2:].lower()
limit_clause = f"limit {TOP_N}" if TOP_N else "limit 100"

sql = f"""
select
    to_hex("to") as address,
    count(*) as claim_count,
    sum(amount) as amount
from tokens.transfers
where blockchain = '{CHAIN}'
  and token_standard = 'erc20'
  and contract_address = from_hex('{contract_hex}')
  and "from" = from_hex('{from_hex_val}')
group by 1
order by amount desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
