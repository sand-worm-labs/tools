# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ALLOWED_LIMITS = {"10", "25", "50", "100"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT not in ALLOWED_LIMITS:
    raise ValueError(f"Unsupported limit: {LIMIT!r}")

wallet_hex = WALLET[2:].lower()

sql = f"""
select
    block_time,
    block_number,
    hash as tx_hash,
    "from",
    "to",
    value,
    gas_used,
    gas_price,
    success,
    nonce
from {CHAIN}.transactions
where "from" = from_hex('{wallet_hex}') OR "to" = from_hex('{wallet_hex}')
  {{__time_where}}
order by block_time desc
limit {LIMIT}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
