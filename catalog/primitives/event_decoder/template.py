# Sandworm Power Toolbox — {{__tool_name}}
import re
from eth_utils import keccak

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
EVENT_SIGNATURE = "{{event_name}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
# "Name(type1,type2,...)" — the canonical form the event_signature field
# already resolved against the contract's real ABI (see tool.yaml), so this
# is just a shape check. No more EVENT_TOPICS guess table needed.
SIGNATURE_RE = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*\(.*\)$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not SIGNATURE_RE.match(EVENT_SIGNATURE):
    raise ValueError(f"Invalid event signature: {EVENT_SIGNATURE!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

topic0 = keccak(text=EVENT_SIGNATURE).hex()

limit_clause = f"limit {LIMIT}" if LIMIT else ""

sql = f"""
select
    block_time,
    block_number,
    tx_hash,
    contract_address,
    topic1,
    topic2,
    topic3,
    data
from {CHAIN}.logs
where contract_address = from_hex('{CONTRACT_ADDRESS[2:].lower()}')
  and topic0 = from_hex('{topic0}')
  {{__time_where}}
order by block_time desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
