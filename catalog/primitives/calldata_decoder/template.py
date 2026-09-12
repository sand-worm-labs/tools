# Sandworm Power Toolbox — {{__tool_name}}
import re
from eth_utils import keccak

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
FUNCTION_SIGNATURE = "{{function_name}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ALLOWED_LIMITS = {"10", "25", "50", "100"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
# "name(type1,type2,...)" — the canonical form the function_signature field
# already resolved against the contract's real ABI (see tool.yaml), so this
# is just a shape check, not a resolution step. No more KNOWN_SELECTORS
# guess table or hand-rolled Keccak needed.
SIGNATURE_RE = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*\(.*\)$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not SIGNATURE_RE.match(FUNCTION_SIGNATURE):
    raise ValueError(f"Invalid function signature: {FUNCTION_SIGNATURE!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT not in ALLOWED_LIMITS:
    raise ValueError(f"Unsupported limit: {LIMIT!r}")

selector = keccak(text=FUNCTION_SIGNATURE).hex()[:8]

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS}' DAY"

sql = f"""
select
    block_time,
    block_number,
    hash as tx_hash,
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
