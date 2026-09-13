# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}"
MIN_USD = "{{min_usd}}"
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_MIN_USD = {"10000", "100000", "1000000", "10000000"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_ADDRESS):
    raise ValueError(f"Invalid token_address: {TOKEN_ADDRESS!r}")
if MIN_USD not in ALLOWED_MIN_USD:
    raise ValueError(f"Unsupported min_usd: {MIN_USD!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid days: {DAYS!r}")

token_hex = TOKEN_ADDRESS[2:].lower()

sql = f"""
select
    block_time,
    to_hex("from") as from_address,
    to_hex("to") as to_address,
    amount as token_amount,
    amount_usd
from tokens.transfers
where blockchain = '{CHAIN}'
  and token_standard = 'erc20'
  and contract_address = from_hex('{token_hex}')
  and amount_usd >= {MIN_USD}
  and block_time >= now() - interval '{DAYS}' day
order by amount_usd desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
