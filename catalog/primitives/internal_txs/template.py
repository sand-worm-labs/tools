# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

wallet_hex = WALLET[2:].lower()

limit_clause = f"limit {LIMIT}" if LIMIT else ""

sql = f"""
select
    block_time,
    block_number,
    tx_hash,
    "from",
    "to",
    value,
    type,
    call_type,
    success
from {CHAIN}.traces
where type = 'call'
  and value > 0
  and ("from" = from_hex('{wallet_hex}') OR "to" = from_hex('{wallet_hex}'))
  {{__time_where}}
order by block_time desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
