# Sandworm Power Toolbox — {{__tool_name}}
# token_symbol is kept as a display-only label (Dune's tokens.transfers has no
# symbol column); the query itself is scoped by contract_address and pool_address.
import re

CHAIN = "{{chain}}"
POOL_ADDRESS = "{{pool_address}}"
CONTRACT_ADDRESS = "{{contract_address}}"
TOKEN_SYMBOL = "{{token_symbol}}".strip() or "TOKEN"
DATE_FROM = "{{date_from}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(POOL_ADDRESS):
    raise ValueError(f"Invalid pool_address: {POOL_ADDRESS!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

pool_hex = POOL_ADDRESS[2:].lower()
token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with flows as (
    select date_trunc('day', block_time) as series_date, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" = from_hex('{pool_hex}')
      and block_time >= date '{DATE_FROM}'
    union all
    select date_trunc('day', block_time) as series_date, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "to" = from_hex('{pool_hex}')
      and block_time >= date '{DATE_FROM}'
)
select series_date, sum(amt) as net_holding
from flows
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
