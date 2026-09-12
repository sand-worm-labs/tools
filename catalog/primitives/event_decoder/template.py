# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
EVENT_NAME = "{{event_name}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ALLOWED_LIMITS = {"10", "25", "50", "100"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# Only common, single-signature standard events are resolvable from a plain
# name without the contract's ABI. Custom/protocol-specific events are not.
EVENT_TOPICS = {
    "transfer": "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
    "approval": "8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",
    "approvalforall": "17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31",
    "transfersingle": "c3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62",
    "transferbatch": "4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb",
    "ownershiptransferred": "8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e",
    "deposit": "e1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c",
    "withdrawal": "7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT not in ALLOWED_LIMITS:
    raise ValueError(f"Unsupported limit: {LIMIT!r}")

event_key = re.sub(r"\(.*\)$", "", EVENT_NAME.strip()).lower()
topic0 = EVENT_TOPICS.get(event_key)
if topic0 is None:
    raise ValueError(
        f"Unknown event signature for {EVENT_NAME!r} without the contract's ABI. "
        f"Supported names: {sorted(EVENT_TOPICS)}"
    )

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
limit {LIMIT}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
