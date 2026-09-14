# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_CONTRACT = "{{token_contract}}"
TARGET_CONTRACT = "{{target_contract}}"
TOPIC0_TRANSFER = "{{topic0_transfer}}".strip()
DATE_TO = "{{date_to}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
TOPIC_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STANDARD_ERC20_TRANSFER_TOPIC0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_CONTRACT):
    raise ValueError(f"Invalid token_contract: {TOKEN_CONTRACT!r}")
if not ADDRESS_RE.match(TARGET_CONTRACT):
    raise ValueError(f"Invalid target_contract: {TARGET_CONTRACT!r}")
if TOPIC0_TRANSFER and not TOPIC_RE.match(TOPIC0_TRANSFER):
    raise ValueError(f"Invalid topic0_transfer: {TOPIC0_TRANSFER!r}")
# tokens.transfers is pre-decoded from raw logs of the standard ERC20
# Transfer(address,address,uint256) event only, so any custom topic0
# would silently match nothing — reject it up front instead.
if TOPIC0_TRANSFER and TOPIC0_TRANSFER.lower() != STANDARD_ERC20_TRANSFER_TOPIC0:
    raise ValueError("Only the standard ERC20 Transfer event topic0 is supported via the decoded transfers table")
if DATE_TO and not DATE_RE.match(DATE_TO):
    raise ValueError(f"Invalid date_to: {DATE_TO!r}")

token_hex = TOKEN_CONTRACT[2:].lower()
target_hex = TARGET_CONTRACT[2:].lower()
date_to_clause = f"and block_time <= timestamp '{DATE_TO}'" if DATE_TO else ""

sql = f"""
select
    date_trunc('day', block_time) as day,
    sum(amount) as value
from tokens.transfers
where blockchain = '{CHAIN}'
  and token_standard = 'erc20'
  and contract_address = from_hex('{token_hex}')
  and "to" = from_hex('{target_hex}')
  {date_to_clause}
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
