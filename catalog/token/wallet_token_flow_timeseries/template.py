# Sandworm Power Toolbox — {{__tool_name}}
import re

TOKEN_CONTRACT = "{{token_contract}}"
WALLET_ADDRESS = "{{wallet_address}}"
TOKEN_DECIMALS = "{{token_decimals}}"
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_CONTRACT):
    raise ValueError(f"Invalid token_contract: {TOKEN_CONTRACT!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")
if not TOKEN_DECIMALS.isdigit():
    raise ValueError(f"Invalid token_decimals: {TOKEN_DECIMALS!r}")

token_hex = TOKEN_CONTRACT[2:].lower()
wallet_hex = WALLET_ADDRESS[2:].lower()

# amount_raw / 10^token_decimals is used (rather than the pre-adjusted
# `amount` column) so the caller-supplied decimals input is actually applied.
sql = f"""
select block_time as time, 'inflow' as category, amount_raw / power(10, {TOKEN_DECIMALS}) as raw_amt
from tokens.transfers
where blockchain = '{CHAIN}'
  and token_standard = 'erc20'
  and contract_address = from_hex('{token_hex}')
  and "to" = from_hex('{wallet_hex}')
union all
select block_time as time, 'outflow' as category, amount_raw / power(10, {TOKEN_DECIMALS}) as raw_amt
from tokens.transfers
where blockchain = '{CHAIN}'
  and token_standard = 'erc20'
  and contract_address = from_hex('{token_hex}')
  and "from" = from_hex('{wallet_hex}')
order by time
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
