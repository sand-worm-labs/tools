# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}"
WALLET = "{{wallet}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_ADDRESS):
    raise ValueError(f"Invalid token_address: {TOKEN_ADDRESS!r}")
if WALLET and not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS} days'"

limit_clause = f"limit {LIMIT}" if LIMIT else ""

wallet_where = ""
if WALLET:
    wallet_hex = WALLET[2:].lower()
    wallet_where = f'AND ("from" = from_hex(\'{wallet_hex}\') OR "to" = from_hex(\'{wallet_hex}\'))'

sql = f"""
select
    block_time,
    block_number,
    tx_hash,
    blockchain,
    contract_address as token_address,
    symbol,
    "from",
    "to",
    amount,
    amount_raw
from tokens.transfers
where blockchain = '{CHAIN}'
  and token_standard = 'erc20'
  and contract_address = from_hex('{TOKEN_ADDRESS[2:].lower()}')
  {wallet_where}
  {time_where}
order by block_time desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
