# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
TOP_N = "{{top_n}}".strip()
DATE_TO = "{{date_to}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if TOP_N and not (TOP_N.isdigit() and int(TOP_N) > 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")
if DATE_TO and not DATE_RE.match(DATE_TO):
    raise ValueError(f"Invalid date_to: {DATE_TO!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
limit_clause = f"limit {TOP_N}" if TOP_N else ""
date_to_clause = f"and block_time <= date('{DATE_TO}')" if DATE_TO else ""

sql = f"""
with movements as (
    select "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      {date_to_clause}
    union all
    select "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      {date_to_clause}
),
balances as (
    select wallet, sum(amt) as holding
    from movements
    group by 1
    having sum(amt) > 0
)
select
    row_number() over (order by holding desc) as rank,
    to_hex(wallet) as address,
    holding
from balances
order by holding desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
