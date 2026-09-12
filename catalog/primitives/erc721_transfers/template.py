# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
WALLET = "{{wallet}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if WALLET and not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

wallet_where = ""
if WALLET:
    wallet_hex = WALLET[2:].lower()
    wallet_where = f'AND ("from" = from_hex(\'{wallet_hex}\') OR "to" = from_hex(\'{wallet_hex}\'))'

limit_clause = f"limit {LIMIT}" if LIMIT else ""

sql = f"""
select
    block_time,
    block_number,
    tx_hash,
    blockchain,
    contract_address,
    token_id,
    "from",
    "to"
from nft.transfers
where blockchain = '{CHAIN}'
  and token_standard = 'erc721'
  and contract_address = from_hex('{CONTRACT_ADDRESS[2:].lower()}')
  {wallet_where}
  {{__time_where}}
order by block_time desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
