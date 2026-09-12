# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
FUNCTION_NAME = "{{function_name}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ALLOWED_LIMITS = {"10", "25", "50", "100"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# Only names with a single, unambiguous 4-byte selector can be resolved without
# the contract's ABI. Overloaded or protocol-specific names (swap, execute, ...)
# are not resolvable from the function name alone.
KNOWN_SELECTORS = {
    "transfer": "a9059cbb",
    "approve": "095ea7b3",
    "transferfrom": "23b872dd",
    "mint": "40c10f19",
    "burn": "42966c68",
    "deposit": "d0e30db0",
    "withdraw": "2e1a7d4d",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT not in ALLOWED_LIMITS:
    raise ValueError(f"Unsupported limit: {LIMIT!r}")

function_key = re.sub(r"\(.*\)$", "", FUNCTION_NAME.strip()).lower()
selector = KNOWN_SELECTORS.get(function_key)
if selector is None:
    raise ValueError(
        f"Cannot resolve a 4-byte selector for {FUNCTION_NAME!r} without the contract's ABI. "
        f"Supported names: {sorted(KNOWN_SELECTORS)}"
    )

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS} days'"

sql = f"""
select
    block_time,
    block_number,
    tx_hash,
    "from" as caller,
    "to" as contract_address,
    value,
    gas_used,
    data as calldata
from {CHAIN}.transactions
where "to" = from_hex('{CONTRACT_ADDRESS[2:].lower()}')
  and substr(data, 1, 4) = from_hex('{selector}')
  {time_where}
order by block_time desc
limit {LIMIT}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
