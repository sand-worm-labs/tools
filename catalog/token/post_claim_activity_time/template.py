# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CLAIM_FROM = "{{claim_from}}"
CONTRACT_ADDRESS = "{{contract_address}}"
MIN_DATE = "{{min_date}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CLAIM_FROM):
    raise ValueError(f"Invalid claim_from: {CLAIM_FROM!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DATE_RE.match(MIN_DATE):
    raise ValueError(f"Invalid min_date: {MIN_DATE!r}")

claim_from_hex = CLAIM_FROM[2:].lower()
contract_hex = CONTRACT_ADDRESS[2:].lower()

# "Post-claim activity" = the same wallet moving the claimed token onward;
# activity is measured on the same token contract, not the wallet's whole
# on-chain footprint.
sql = f"""
with claims as (
    select "to" as user, min(block_time) as claim_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and "from" = from_hex('{claim_from_hex}')
      and block_time >= date '{MIN_DATE}'
    group by 1
),
activity as (
    select "from" as user, min(block_time) as first_tx_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
    group by 1
)
select
    c.user,
    c.claim_time,
    a.first_tx_time,
    date_diff('second', c.claim_time, a.first_tx_time) / 86400.0 as days_gap
from claims c
join activity a on a.user = c.user and a.first_tx_time > c.claim_time
order by c.claim_time
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
