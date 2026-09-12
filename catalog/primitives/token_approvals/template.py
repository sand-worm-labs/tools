# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}"
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

APPROVAL_TOPIC0 = "8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
MAX_UINT256 = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_ADDRESS):
    raise ValueError(f"Invalid token_address: {TOKEN_ADDRESS!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")

sql = f"""
select
    block_time,
    block_number,
    tx_hash,
    concat('0x', lower(to_hex(substr(topic1, 13, 20)))) as owner,
    concat('0x', lower(to_hex(substr(topic2, 13, 20)))) as spender,
    data as approval_amount_raw,
    (data = from_hex('{MAX_UINT256}')) as is_unlimited
from {CHAIN}.logs
where contract_address = from_hex('{TOKEN_ADDRESS[2:].lower()}')
  and topic0 = from_hex('{APPROVAL_TOPIC0}')
  {{__time_where}}
order by block_time desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
